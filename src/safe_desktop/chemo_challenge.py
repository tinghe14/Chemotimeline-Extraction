
from pathlib import Path
import datetime
import re
import csv
import os

import etherrunner
import MedDRATranslator


class ChemoChallenge():
    
    def __init__(self, data_root_path, output_root_path):
        self.data_root_path = data_root_path
        self.output_root_path = output_root_path
        
    def run_ether_on_patients(self, cancer_types, dataset):
        """
        Finds the list of patients for the cancer_types and dataset requested, and runs ETHER on all of the notes
        for each of those patients. The results from all notes for a single patient are written into a single
        csv file under the output_root_path
        
        Input:
            cancer_types should be a list that can contain all or a subset of ['breast', 'melanoma', 'ovarian']
            dataset should be either 'train' or 'dev'
        Output:
            Saves ETHER output to csv files in the directory path: self.output_root_path / cancer_type / dataset /
        """
        
        meddra_translator = MedDRATranslator.MedDRATranslator('meddra20_1')
        
        for cancer_type in cancer_types:
            patient_id_filename = f'{cancer_type}_{dataset}_patient_ids.txt'
            print(patient_id_filename)
            patient_ids = read_patient_ids(self.data_root_path / 'All_Patient_IDs' / patient_id_filename)
            
            file_lst = []
            file_add = os.path.join(self.output_root_path, cancer_type, dataset)
            os.makedirs(file_add, exist_ok=True)
            for filename in os.listdir(file_add):
                file = filename.split("_")[-1][:-4]
                file_lst.append(file)

            for patient_id in patient_ids:
                # Create a single output file for each patient
                if patient_id in file_lst:
                    continue
                csv_out_file_parent = os.path.join(*[self.output_root_path, cancer_type, dataset])
                csv_out_file = os.path.join(csv_out_file_parent, f"ether_output_{patient_id}.csv")
                # csv_out_file = self.output_root_path / cancer_type / dataset / 'ether_output_' + patient_id + '.csv'
                os.makedirs(csv_out_file_parent, exist_ok=True)

                # csv_out_file.parent.mkdir(parents=True, exist_ok=True) # Create directory structure if needed
                
                with open(csv_out_file, 'w', encoding='utf-8', newline='') as outf:
                    csv_writer = csv.writer(outf, dialect='excel')
                    csv_writer.writerow(['Patient', 'Note', 'Document Header Time', 'Record Type', 'ETHER Output Info...'])
                    
                    notes_dir = self.data_root_path / 'Patient_Notes' / cancer_type / dataset / patient_id
                    note_files = sorted(notes_dir.glob(patient_id + '_report*.txt'))
                    for note_file in note_files:
                        print(note_file)
                        note_filename = note_file.name
                        (document_datetime, record_type, note_text) = read_note(note_file)


                        # Now run ETHER on this note
                        doc_date = document_datetime.strftime('%Y%m%d')
                        (expose_date, onset_date, feature_rows, timex_rows) = etherrunner.run_feature_and_timex_extraction_on_text(note_text,
                                                                                                                                   exposure_date_string=doc_date,
                                                                                                                                   onset_date_string=doc_date,
                                                                                                                                   meddra_translator = meddra_translator)
                        
                        # Write the output for this note to the patient's output file
                        csv_writer.writerow([patient_id, note_filename, document_datetime, record_type, 'Output Exposure Date:', expose_date])
                        csv_writer.writerow([patient_id, note_filename, document_datetime, record_type, 'Output Onset Date:', onset_date])
                        for feat in feature_rows:
                            # print(feat['type'].lower())
                            if feat['type'].lower() == 'drug':
                                csv_writer.writerow([patient_id, note_filename, document_datetime, record_type,
                                                    feat['id'], feat['type'], feat['text'], feat['start_position'], feat['end_position'], feat['time_start'], feat['preferred_terms']])
                        for timex in timex_rows:
                            csv_writer.writerow([patient_id, note_filename, document_datetime, record_type,
                                                 timex['id'], timex['text'], timex['date_time'], timex['start_position']])


def read_patient_ids(file_path):
    """
    The input must be a Path from the pathlib library.
    Returns a list containing the lines from the file.
    """
    return file_path.read_text(encoding='utf-8').splitlines()


def read_note(file_path):
    """
    Input should be a Path from the pathlib library.
    Output will be a tuple of:
        (DateTime object, record_type, note_text)
    """
    with open(file_path, encoding='utf-8') as f:
        full_content = f.readlines()
    
    # Check the file format and extract the metadata from the first few lines of the file.
    # This metadata header was added by the challenge organizers, so
    # the formatting should always be exactly the same in every type of file.
    if (not full_content[0].startswith('==========================')
          or not full_content[1].startswith('Report ID...')
          or not full_content[2].startswith('Patient ID...')
          or not full_content[3].startswith('Patient Name...')
          or not full_content[4].startswith('Principal Date...')
          or not full_content[5].startswith('Record Type...')
          or not full_content[6].startswith('==========================')
          or not full_content[7].startswith('[Report de-identified')):
        raise ValueError('The file at path {} does not match the expected header format in the first few lines'.format(file_path.absolute()))
    
    date_match = re.search(r'Principal Date\.+([0-9]+)( [0-9]+)?', full_content[4], flags=re.I)
    if date_match is None or date_match.group(1) is None:
        # TODO: If any of the files in the data set are actually missing this Principal Date line, we'll have to find a way to deal with it instead of throwing an error.
        raise ValueError('The file at path {} does not have a Principal Date entry that can be parsed from the header'.format(file_path.absolute()))
    if date_match.group(2) is None:
        # Only the date is present in the file
        document_datetime = datetime.datetime.strptime(date_match.group(1), '%Y%m%d')
    else:
        # The date and the time are both present in the file
        document_datetime = datetime.datetime.strptime(date_match.group(1) + date_match.group(2), '%Y%m%d %H%M')
    
    rectype_match = re.search(r'Record Type\.+[a-zA-Z]{1,5}', full_content[5], flags=re.I)
    if rectype_match is None or rectype_match.group(0) is None:
        # TODO: If any of the files in the data set are actually missing this Record Type line, we'll have to find a way to deal with it instead of throwing an error.
        raise ValueError('The file at path {} does not have a Record Type entry that can be parsed from the header'.format(file_path.absolute()))
    record_type = rectype_match.group(0)
    
    # The remainder of the lines in the file are the full text of the note itself.
    note_text = ''.join(full_content[9:])
    
    return (document_datetime, record_type, note_text)

from multiprocessing import Pool

def run_challenge(cancer_dataset):
    data_root_path = Path("S:\\Chemo_Challenge\\chemoTimelines2024_train_dev_labeled\\subtask1")
    output_root_path = Path("S:\\Chemo_Challenge\\0306_drug_only\\ether_output_data")
    os.makedirs(output_root_path, exist_ok=True)
    # output_root_path = Path("S:\\Chemo_Challenge\\0310_new_cancer_drug_lexicon_only\\ether_output_data")
    cancer_types, dataset = cancer_dataset
    challenge_runner = ChemoChallenge(data_root_path, output_root_path)
    challenge_runner.run_ether_on_patients(cancer_types, dataset)

if __name__ == '__main__':

    #['breast', 'melanoma', 'ovarian']:
    #['train', 'dev']:
    data_root_path = Path("S:\\Chemo_Challenge\\chemoTimelines2024_train_dev_labeled\\subtask1")
    output_root_path = Path("S:\\Chemo_Challenge\\0312_temp_test\\0318_check_true_lexicon_exp2\\ether_output_data")
    os.makedirs(output_root_path, exist_ok=True) # ç”Ÿæˆfolderä¹‹åŽå¯ä»¥åˆ æŽ‰ å†…å­˜æœ‰é™
    for cancer_types in [['breast']]: #, ['melanoma'], ['ovarian']
        for dataset in ['dev']:
            challenge_runner = ChemoChallenge(data_root_path, output_root_path)
            challenge_runner.run_ether_on_patients(cancer_types, dataset)
    # with Pool() as p:
    #     cancer_types_datasets = [(cancer_types, dataset) for cancer_types in [['breast'], ['melanoma'], ['ovarian']] for dataset in ['train']] #['breast'], ['melanoma'], ['ovarian']
    #     p.map(run_challenge, cancer_types_datasets)