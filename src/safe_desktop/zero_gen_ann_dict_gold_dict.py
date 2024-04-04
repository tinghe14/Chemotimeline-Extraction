# 00. ETHER subtask1: generate ent_dict from gold files & ether_ent_dict from ether output files, generate the results from begining to the end


import os, sys
from typing import List, Dict, Optional, Union
import logging

import numpy as np
import pandas as pd
import json
import xml.etree.ElementTree as et 
from collections import defaultdict
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime
from collections import Counter

logger = logging.getLogger("zero_logger")
logger.setLevel(logging.INFO) # DEBUG all files under patient 92 
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger.addHandler(ch)
# fh = logging.FileHandler("./zero_logs/temp.log", mode="w")
# fh.setFormatter(formatter)
# logger.addHandler(fh)

# note_filename eg "report031_NOTE"
# patient_filename eg "patient04_report031_NOTE"


class EntDicts:
    """
    Generate gold & ether dicts with the high-level structure of {note_filename}:{
        doc_create_time:{}, pair_wise:{chemo/event:{}, time:{}}, w/wo-patient_level:[], raw_note:str}
    # update: as patient_level
    """
    def __init__(self, mode, cancer_type, OUTPUT_DIR):
        self.mode = mode #"train"
        self.cancer_type = cancer_type #"breast"
        
        # self.gold_root = os.path.join("S:\\Chemo_Challenge\\chemoTimelines2024_train_dev_labeled\\subtask1\\Gold_PairWise_Annotations",self.cancer_type,self.mode)  
        self.gold_root = os.path.join("S:\\Chemo_Challenge\\subtask1\\Gold_PairWise_EventTimex", self.cancer_type)    

        self.ether_dir = os.path.join(OUTPUT_DIR, "ether_output_data",self.cancer_type,self.mode)
        self.ether_gold_raw_dir = os.path.join("S:\\Chemo_Challenge","chemoTimelines2024_train_dev_labeled", "subtask1", "Patient_Notes",self.cancer_type, self.mode)  

    
    # ========== gold_ent_dict from gold-pair-wise ann xml files ========== #
    def generate_gold_ent_dict(self) ->Dict:
        """this func is to read a pair raw NOTE and annotated xml files to generate gold entities and their attributes in patient-report level
        ouput:
            # {disease(str): {patient_id(str): {patient_filename(str): {
                                                'doc_create_time': {'ment_id':str, 'ment':str, 'span':tuple of int, 'standard':str},
                                                'pair_wise': {'chemo': {'ment_id':list of str, 'ment':list of str, 'span':list of tuple of int, 'id':list of int},
                                                                'time':{'ment_id':list of str, 'ment':list of str, 'span':list of tuple of int, 'id':list of int},
                                                                'chemo_time_rel':{'rel_id/id_rel':list of str, 'source_id':list of str, 'target_id':list of str, 'tlink_type':list of str, 'rel_type':list of str},
                                                # 'chemo_time_rel': list of tuple, final gold triple set,
                                                'raw_note': str,
                                                }
        """
        gold_ent_dict_filenames_ids = defaultdict(dict)
        for patient_id_file in os.listdir(self.gold_root):
            if os.path.isdir(os.path.join(self.gold_root, patient_id_file)):
                patient_id = patient_id_file.split("_")[1] 
                gold_ent_dict_filenames = defaultdict(dict)
                gold_dir = os.path.join(self.gold_root,self.cancer_type+"_"+patient_id+"_"+self.mode)
                for patient_filename in os.listdir(gold_dir):
                    # note_filename = patient_filename[11:] 
                    note_filename = "_".join(patient_filename.split("_")[1:])
                    #report014_RAD
                    gold_raw_note = os.path.join(gold_dir, patient_id+"_"+note_filename,patient_id+"_"+note_filename)
                    gold_ann_xml = gold_raw_note+".Temporal_Relation.gold.entity_only.xml" 
                    #Temporal_Relation.gold.inprogress.xml"
                    gold_ent_dict = defaultdict(list)
                    chemo_dict, time_dict, chemo_time_dict = defaultdict(dict), defaultdict(dict), defaultdict(dict)
                    # read note file
                    with open(gold_raw_note, "r") as raw_infile:
                        note_lines_lst = raw_infile.readlines()
                    note_lines = ''.join(note_lines_lst)
                    # read xml ann file
                    tree = et.parse(gold_ann_xml)
                    root = tree.getroot()
                    for ann_nodes in root[2]:
                        for ent_nodes in ann_nodes.iter('entity'):
                            for ents in ent_nodes:
                                if ents.tag == "parentsType" or ents.tag == "properties":
                                    pass
                                else:
                                    gold_ent_dict[ents.tag].append(ents.text)
                        for ent_nodes in ann_nodes.iter('relation'):
                            for ents in ent_nodes:
                                if ents.tag in ["type", "id"]:
                                    new_key = ents.tag+"_rel"
                                    gold_ent_dict[new_key].append(ents.text)
                                elif ents.tag == "properties":
                                    for ent in ents:
                                        new_key = ent.tag +"_id"
                                        gold_ent_dict[new_key].append(ent.text)

                    for span_str in gold_ent_dict["span"]:
                        span_ind = span_str.split(",")
                        start_ind, end_ind = int(span_ind[0]), int(span_ind[1])
                        gold_ent_dict["new_span"].append((start_ind, end_ind))
                        gold_ent_dict["ment"].append(note_lines[start_ind:end_ind])
                    gold_ent_dict["span"] = gold_ent_dict["new_span"]
                    del gold_ent_dict["new_span"]

                    len_val_ents = np.unique(([len(gold_ent_dict[key]) for key in gold_ent_dict.keys() if (not key.endswith("_rel")) and (not key.endswith("_id"))])) 
                    gold_ent_dict["raw_note"] = note_lines
                    gold_ent_dict["pair_wise"] = {"chemo": chemo_dict, "time": time_dict, "chemo_time_rel": chemo_time_dict}
                    # doc_create_time
                    if gold_ent_dict["type"][0] == "DOCTIME":
                        gold_ent_dict["doc_create_time"] = {"ment_id": gold_ent_dict["id"][0], "ment": gold_ent_dict["ment"][0], "span":gold_ent_dict["span"][0]}
                    else:
                        logger.debug(f" in {self.mode}-{self.cancer_type}-{patient_id}-{note_filename}, the ann file in gold file don't have doctime at 0 ind. need to check this file manually!!!")
                        gold_ent_dict["doc_create_time"] = {"ment_id": None, "ment": None, "span": tuple([None, None])}
                    # chemo
                    chemo_inds = [ind for ind, val in enumerate(gold_ent_dict["type"] )if val=="EVENT"]
                    span_lst = [gold_ent_dict["span"][ind] for ind in chemo_inds ]
                    gold_ent_dict["pair_wise"] ["chemo"]= {"ment_id":np.take(gold_ent_dict["id"], chemo_inds).tolist(), "ment":np.take(gold_ent_dict["ment"], chemo_inds).tolist(), "span":span_lst, "id":list(range(len(chemo_inds)))}
                    # time
                    time_inds = [ind for ind, val in enumerate(gold_ent_dict["type"] )if val=="TIMEX3"]
                    span_lst = [gold_ent_dict["span"][ind] for ind in time_inds ]
                    gold_ent_dict["pair_wise"] ["time"]= {"ment_id":np.take(gold_ent_dict["id"], time_inds).tolist(), "ment":np.take(gold_ent_dict["ment"], time_inds).tolist(), "span":span_lst, "id":list(range(len(time_inds)))}
                    # rel
                    gold_ent_dict["chemo_time_rel"] = {"rel_id": gold_ent_dict["id_rel"], "source_id":gold_ent_dict["Source_id"], "target_id":gold_ent_dict["Target_id"], "rel_type":gold_ent_dict["Type_id"], "tlink_type": gold_ent_dict["type_rel"]}
                    del gold_ent_dict["ment"]
                    del gold_ent_dict["id"]
                    del gold_ent_dict["span"]
                    del gold_ent_dict["type"]
                    del gold_ent_dict["id_rel"]
                    del gold_ent_dict["Source_id"]
                    del gold_ent_dict["Target_id"]
                    del gold_ent_dict["Type_id"]
                    del gold_ent_dict["type_rel"]
                    gold_ent_dict_filenames[note_filename] = gold_ent_dict
            gold_ent_dict_filenames_ids[patient_id] = gold_ent_dict_filenames
        return gold_ent_dict_filenames_ids

    # ========== ether_ent_dict from ether_ann_csv files ========== #
    def generate_ether_ent_dict(self): #->Dict[List]:
        """this func is to read a pair raw NOTE and ether annotated csv files to generate ether entities and their attributes
        in patient level
        outputs:
            {disease(str): {patient_id(str): {patient_filename(str): {
                                                'doc_create_time':{'ment':str, 'standard':str},
                                                'pair_wise':{'event':{'type':list of str, 'ment':list of str, 'span':list of tuple of int, 'normalized_related_time':list of string, 'id':list of int},
                                                            'time'{'ment':list of str, 'span':list of tuple of int, 'normalized_time':list of string, 'id':list of int},
                                                'raw_note': str
                                                }
        """

        ether_ent_dict_filenames_ids = defaultdict(dict)
        for filename in os.listdir(self.ether_dir):
            patient_id = filename.split("_")[2].split(".csv")[0]
            ether_ent_dict_filenames = defaultdict(dict)
            # read ETHER ann file
            ether_ann_patient_csv = os.path.join(self.ether_dir, filename)
            col_names = [i for i in range(0, 29)]

            ether_df = pd.read_csv(ether_ann_patient_csv, header=None, delimiter=",", names=col_names)
            patient_filename_lst = np.unique(ether_df[1])
            for patient_filename in patient_filename_lst:
                # print(patient_filename)
                ether_ent_dict, event_dict, time_dict = defaultdict(list), defaultdict(dict), defaultdict(dict)
                ether_ent_dict["pair_wise"] = {"event": event_dict, "time": time_dict}
                # read gold note file
                if patient_filename != "Note":
                    ether_gold_raw_dir = os.path.join(self.ether_gold_raw_dir, patient_id )
                    patient_note_file = os.path.join(ether_gold_raw_dir, patient_filename)
                    with open(patient_note_file, "r") as note_infile:
                        note_lines_lst = note_infile.readlines()
                    try:
                        assert note_lines_lst[6].strip()[0] == '='
                    except:
                        logger.debug(f"!!!the format of patient note file is different than typical one! need to check the file and change the logic here to map the ind to mention!!!")
                    main_note_lines_lst = note_lines_lst[8:] # skip header in patient note
                    main_note_str = ''.join(main_note_lines_lst)
                    # except time mention (read ETHER output file)
                    selected_ether_df = ether_df[ether_df[1] == patient_filename]
                    file_ether_df = selected_ether_df[np.logical_not(np.isnan(selected_ether_df[[7,8]]).any(axis=1))] 
                    file_ether_df["start_ind"], file_ether_df["end_ind"] = file_ether_df[7],  file_ether_df[8]
                    start_ind_arr, end_ind_arr = file_ether_df["start_ind"].values, file_ether_df["end_ind"].values
                    span_lst = []
                    for start_ind, end_ind in zip(start_ind_arr, end_ind_arr):
                        span = start_ind, end_ind+1
                        span_lst.append(span) 
                    ether_ent_dict["pair_wise"]["event"]["span"] = span_lst
                    ether_ent_dict["pair_wise"]["event"]["type"] = file_ether_df[5].values.tolist()
                    ether_ent_dict["pair_wise"]["event"]["ment"] = file_ether_df[6].values.tolist()
                    ether_ent_dict["pair_wise"]["event"]['normalized_related_time'] = file_ether_df[9].values.tolist()
                    ether_ent_dict["pair_wise"]["event"]["id"] = list(range(file_ether_df.shape[0]))
                    
                    # doc_create_time
                    ether_ent_dict["doc_create_time"] = np.unique(selected_ether_df[2])[0]
                    assert len(np.unique(selected_ether_df[2])) == 1
                    
                    # time mention (read ETHER output file)
                    file_ether_df = selected_ether_df[np.logical_and(np.logical_not(np.isnan(selected_ether_df[7])), (np.isnan(selected_ether_df[8])))]
                    time_n_rows = file_ether_df.shape[0]
                    time_start_ind_arr, time_end_ind_arr = file_ether_df[7].values, ["None"]*time_n_rows
                    time_span_lst = []
                    for time_start_ind, time_end_ind in zip(time_start_ind_arr, time_end_ind_arr):
                        time_span = time_start_ind, time_end_ind 
                        time_span_lst.append(time_span)
                    ether_ent_dict["pair_wise"]["time"]["span"] = time_span_lst
                    ether_ent_dict["pair_wise"]["time"]["type"] = ["TIME"] * time_n_rows
                    ether_ent_dict["pair_wise"]["time"]["ment"] = file_ether_df[5].values.tolist()
                    ether_ent_dict["pair_wise"]["time"]['normalized_time'] = file_ether_df[6].values.tolist()
                    ether_ent_dict["pair_wise"]["time"]["id"] = list(range(time_n_rows))

                    len_event_val = np.unique(([len(ether_ent_dict["pair_wise"]["event"][key]) for key in ether_ent_dict["pair_wise"]["event"].keys()])) 
                    len_time_val = np.unique(([len(ether_ent_dict["pair_wise"]["time"][key]) for key in ether_ent_dict["pair_wise"]["time"].keys()])) 
                    try: 
                        assert len(len_event_val)== 1
                        assert len(len_time_val) == 1
                    except:            
                        logger.debug("!!!len of all the keys in the ether_ent_dict should be the same!!!")
                    ether_ent_dict["raw_note"] = main_note_str
                    ether_ent_dict_filenames[patient_filename[10:-4]] = ether_ent_dict
            ether_ent_dict_filenames_ids[patient_id] = ether_ent_dict_filenames
        return ether_ent_dict_filenames_ids
    
    '''
    # standard doc_create_time
    def convert_date(self, ent_dict_filenames_ids, gold_or_ether):
        for patient_id in ent_dict_filenames_ids.keys():
            for note_filename in ent_dict_filenames_ids[patient_id].keys():
                if gold_or_ether == "gold":
                    date_string = ent_dict_filenames_ids[patient_id][note_filename]["doc_create_time"]["ment"]
                else:
                    date_string = ent_dict_filenames_ids[patient_id][note_filename]["doc_create_time"]
                if gold_date_string is not None:
                    try: 
                        standard_gold_date = datetime.strptime(gold_date_string, "%Y%m%d").strftime('%Y-%m-%d') #"20120402"
                    except: 
                        standard_gold_date = np.nan 
                        logger.info("here convert time by force")
                else: 
                    standard_gold_date = np.nan
            else: 
                standard_gold_date = np.nan
        else: 
            standard_gold_date = np.nan
        if patientid_in_ether_bool:
            if filename_in_ether_bool:
                ether_date_string = self.ether_ent_dict_filenames_ids[patient_id][note_filename]["doc_create_time"]
                standard_ether_date = datetime.strptime(ether_date_string, "%Y-%m-%d %H:%M:%S").strftime('%Y%m%d') #"2012-04-02 00:00:00"->"20120402"
            else: 
                standard_ether_date = np.nan 
        else: 
                standard_ether_date = np.nan
        return new_ent_dict_filenames_ids
    '''

    
class EntEvaluate():
    
    def __init__(self, gold_ent_dict_filenames_ids:dict, ether_ent_dict_filenames_ids:dict):
        self.gold_ent_dict_filenames_ids = gold_ent_dict_filenames_ids # notes in gold ann files for all patients
        self.ether_ent_dict_filenames_ids = ether_ent_dict_filenames_ids # notes in ether output files for all patients
        # self.filert_event = False

    def _check_patientid_exist(self, patient_id):
        if patient_id in self.gold_ent_dict_filenames_ids.keys() and patient_id in self.ether_ent_dict_filenames_ids.keys():
            return True, True 
        elif patient_id not in self.gold_ent_dict_filenames_ids.keys() and patient_id in self.ether_ent_dict_filenames_ids.keys():
            return False, True
        elif patient_id in self.gold_ent_dict_filenames_ids.keys() and patient_id not in self.ether_ent_dict_filenames_ids.keys():
            return True, False
        else:
            return False, False
        
    def _check_note_filename_exist(self, patient_id, note_filename):
        """To controll some corner cases such as gold pred files don't have any for this note_filename, given we have patient_id in both type"""
        gold_patientid_bool, ether_patientid_bool = self._check_patientid_exist(patient_id)
        if gold_patientid_bool and ether_patientid_bool:
            if note_filename in self.gold_ent_dict_filenames_ids[patient_id].keys() and note_filename in self.ether_ent_dict_filenames_ids[patient_id].keys() and (len(self.ether_ent_dict_filenames_ids[patient_id][note_filename]['doc_create_time']) > 0):
                return True, True
            elif note_filename not in self.gold_ent_dict_filenames_ids[patient_id].keys() and note_filename in self.ether_ent_dict_filenames_ids[patient_id].keys() and (len(self.ether_ent_dict_filenames_ids[patient_id][note_filename]['doc_create_time']) > 0):
                return False, True
            elif note_filename in self.gold_ent_dict_filenames_ids[patient_id].keys() and note_filename not in self.ether_ent_dict_filenames_ids[patient_id].keys():
                return True, False
            else:
                return False, False
        elif gold_patientid_bool and not ether_patientid_bool:
            if note_filename in self.gold_ent_dict_filenames_ids[patient_id].keys():
                return True, False 
            elif note_filename not in self.gold_ent_dict_filenames_ids[patient_id].keys():
                return False, False
        elif not gold_patientid_bool and ether_patientid_bool:
            if (note_filename in self.ether_ent_dict_filenames_ids[patient_id].keys()) and (len(self.ether_ent_dict_filenames_ids[patient_id][note_filename]['doc_create_time']) > 0):
                return False, True 
            elif note_filename not in self.ether_ent_dict_filenames_ids[patient_id].keys():
                return False, False
        else:
            return False, False
        
    # standard doc_create_time
    def convert_date(self, patient_id, note_filename):
        patientid_in_gold_bool, patientid_in_ether_bool = self._check_patientid_exist(patient_id)
        # try: 
        filename_in_gold_bool, filename_in_ether_bool = self._check_note_filename_exist(patient_id, note_filename)
        # except: 
        #     print(patient_id, note_filename)
        if patientid_in_gold_bool:
            if filename_in_gold_bool:
                gold_date_string = self.gold_ent_dict_filenames_ids[patient_id][note_filename]["doc_create_time"]["ment"]
                if gold_date_string is not None:
                    try: 
                        standard_gold_date = datetime.strptime(gold_date_string, "%Y%m%d").strftime('%Y-%m-%d') #"20120402"
                    except: 
                        standard_gold_date = np.nan 
                        logger.info("here convert time by force")
                else: 
                    standard_gold_date = np.nan
            else: 
                standard_gold_date = np.nan
        else: 
            standard_gold_date = np.nan
        if patientid_in_ether_bool:
            if filename_in_ether_bool:
                ether_date_string = self.ether_ent_dict_filenames_ids[patient_id][note_filename]["doc_create_time"]
                standard_ether_date = datetime.strptime(ether_date_string, "%Y-%m-%d %H:%M:%S").strftime('%Y%m%d') #"2012-04-02 00:00:00"->"20120402"
            else: 
                standard_ether_date = np.nan 
        else: 
                standard_ether_date = np.nan
        return standard_gold_date, standard_ether_date
    
    def calculate_doc_create_time(self, standard_gold_date, standard_ether_date):
        if standard_gold_date == standard_ether_date and standard_gold_date is not None and standard_ether_date is not None:
            return 1
        elif standard_gold_date != standard_ether_date:
            return 0
        elif standard_gold_date is None and standard_ether_date is None:
            logger.debug("both nan here!")
            return np.nan # use np.nanmean(will ignore nan)
    
    # raw.lower()
    def convert_chemo_event(self, patient_id, note_filename):
        patientid_in_gold_bool, patientid_in_ether_bool = self._check_patientid_exist(patient_id)
        filename_in_gold_bool, filename_in_ether_bool = self._check_note_filename_exist(patient_id, note_filename)
        if patientid_in_gold_bool:
            if filename_in_gold_bool: 
                gold_event_lst = self.gold_ent_dict_filenames_ids[patient_id][note_filename]["pair_wise"]["chemo"]["ment"]
                gold_lower_event_lst =  [gold_ment.lower() for gold_ment in gold_event_lst]
            else:
                gold_lower_event_lst = np.nan
        else:
            gold_lower_event_lst = np.nan
        if patientid_in_ether_bool:
            if filename_in_ether_bool: 
                ether_event_lst = self.ether_ent_dict_filenames_ids[patient_id][note_filename]["pair_wise"]["event"]["ment"]
                ether_lower_event_lst = [ether_event.lower() for ether_event in ether_event_lst]
            else:
                ether_lower_event_lst = np.nan
        else:
            ether_lower_event_lst = np.nan
        return gold_lower_event_lst, ether_lower_event_lst
    
    # raw.lower(), not normalized time yet, just time mention
    def convert_time(self, patient_id, note_filename):
        patientid_in_gold_bool, patientid_in_ether_bool = self._check_patientid_exist(patient_id)
        filename_in_gold_bool, filename_in_ether_bool = self._check_note_filename_exist(patient_id, note_filename)
        if patientid_in_gold_bool:
            if filename_in_gold_bool: 
                gold_time_lst = self.gold_ent_dict_filenames_ids[patient_id][note_filename]["pair_wise"]["time"]["ment"]
                gold_lower_time_lst =  [gold_time.lower() for gold_time in gold_time_lst]
            else:
                gold_lower_time_lst = np.nan
        else:
            gold_lower_time_lst = np.nan
        if patientid_in_ether_bool:
            if filename_in_ether_bool: 
                ether_time_lst = self.ether_ent_dict_filenames_ids[patient_id][note_filename]["pair_wise"]["time"]["ment"]
                ether_lower_time_lst = [ether_time.lower() for ether_time in ether_time_lst]
            else:
                ether_lower_time_lst = np.nan
        else:
            ether_lower_time_lst = np.nan
        return gold_lower_time_lst, ether_lower_time_lst

    
    def calculate_lst(self, gold_lower_lst, ether_lower_lst):
        logger.debug(f"gold_lower_lst: {gold_lower_lst}")
        logger.debug(f"ether_lower_lst: {ether_lower_lst}")
        if gold_lower_lst is not np.nan and ether_lower_lst is not np.nan:
            gold_counter, ether_counter = Counter(gold_lower_lst), Counter(ether_lower_lst)
            TP, FP, FN = 0, 0, 0
            for item in set(gold_lower_lst + ether_lower_lst):
                TP += min(gold_counter[item], ether_counter[item])
                FP += max(0, ether_counter[item]-gold_counter[item])
                FN += max(0, gold_counter[item]-ether_counter[item])
        elif gold_lower_lst is np.nan and ether_lower_lst is not np.nan:
            TP, FP, FN = 0, 0, 0
            FP = len(ether_lower_lst)
        else: 
            logger.debug(f"something wrong here!!!")
        return TP, FP, FN
            
def _patient_id_lst(disease="melanoma", mode="dev"):
    """return patient_id lst given the disease type and mode (train/dev)"""
    # dir = "S:\\Chemo_Challenge\\chemoTimelines2024_train_dev_labeled\\subtask1\\All_Patient_IDs"
    dir = "S:\Chemo_Challenge\subtask1\All_Patient_IDs"
    patID_lst = []
    patId_file = os.path.join(dir, disease+"_"+mode+"_patient_ids.txt")
    with open(patId_file, "r") as infile:
        lines = infile.readlines()
    for line in lines:
        if line[-1] == "\n":
            line = line[:-1]
        patID_lst.append(line)
    return patID_lst

"""
ent_dicts:
1. doc_create_time (match/no)
2. calculate overlap between chemo ment in gold & event ment in ether (tp/fp/fn)
3. calculate overlap between event ment in gold & time ment in ether (tp/fp/fn)

normalized time in gold ent vs normalized time in ether time

convert to tlink

apply before, etc

filter the chemo by drug only

need to save dict as json 

"""
def main(OUTPUT_DIR):
    total_gold_dct, total_ether_dct = defaultdict(dict), defaultdict(dict)
    total_gold_dct_file, total_ether_dct_file =os.path.join(OUTPUT_DIR, "0_total_gold_test_Dct.json"), os.path.join(OUTPUT_DIR, "0_total_ether_test_Dct.json")


    for cancer_type in ["breast", "ovarian", "melanoma"]:
        for mode in ["test"]:
            
            gold_root_dir = os.path.join("S:\\Chemo_Challenge\\chemoTimelines2024_train_dev_labeled\\subtask1\\Gold_PairWise_Annotations",cancer_type,mode)
            cancer_mode_patid_lst = _patient_id_lst(cancer_type, mode)

            # =========== EntDicts Class =========== #
            dicts_class = EntDicts(mode, cancer_type, OUTPUT_DIR)

            gold_ent_dict_filenames_ids = dicts_class.generate_gold_ent_dict()
            total_gold_dct[cancer_type][mode] = gold_ent_dict_filenames_ids
            cancer_mode_gold_dct_file = os.path.join(OUTPUT_DIR, "0_"+cancer_type + "_" + mode + "_"+"gold_dct.json")
            with open(cancer_mode_gold_dct_file, "w") as f:
                f.write(json.dumps(gold_ent_dict_filenames_ids, indent=4))
            '''
            ether_ent_dict_filenames_ids = dicts_class.generate_ether_ent_dict()
            total_ether_dct[cancer_type][mode] = ether_ent_dict_filenames_ids
            cancer_mode_ether_dct_file = os.path.join(OUTPUT_DIR, "0_"+cancer_type + "_" + mode + "_"+"ether_dct.json")
            with open(cancer_mode_ether_dct_file, "w") as f:
                f.write(json.dumps(ether_ent_dict_filenames_ids, indent=4))
           
            # ========== initiate EntEvaluate Class using outputs from EntDict.generate_gold_ent_dict() ========== #
            cancer_mode_gold_dct_file = os.path.join("S:\\Chemo_Challenge", "0_"+cancer_type + "_" + mode + "_"+"gold_dct.json")
            with open(cancer_mode_gold_dct_file, "r") as infile:
                gold_ent_dict_filenames_ids = json.load(infile)
            ent_eval_class = EntEvaluate(gold_ent_dict_filenames_ids,  ether_ent_dict_filenames_ids)
            
            doc_create_time_match_lst  = []
            event_match_tp_lst, event_match_fp_lst, event_match_fn_lst, event_recall_lst = [], [], [], []
            time_match_tp_lst, time_match_fp_lst, time_match_fn_lst, time_recall_lst = [], [], [], []
            doc_create_time_match_cnt_lst, doc_create_time_non_match_cnt_lst, doc_create_time_nan_match_cnt_lst = [], [], []
            # patient_id = "patient92"
            # if patient_id == "patient92":
            for patient_id in cancer_mode_patid_lst:
                patient_files_event, patient_files_time = defaultdict(list), defaultdict(list)
                for patient_filename in ether_ent_dict_filenames_ids[patient_id].keys():
                    
                    note_filename = patient_filename
                    
                    # ========== compare doc_create_time in ann gold and ann ether output files ========== #
                    gold_doc_create_time, ether_doc_create_time = ent_eval_class.convert_date(patient_id, note_filename)
                    doc_create_time_match_num = ent_eval_class.calculate_doc_create_time(gold_doc_create_time, ether_doc_create_time)
                    # logger.info("~~~~~CANCER_TYPE->PATIENT_ID->FILENAME level ~~~~~")
                    # logger.info(f"{dicts_class.mode}-{dicts_class.cancer_type}-{patient_id}-{note_filename}.txt")
                    logger.debug(f'gold doc_create_time: {gold_doc_create_time} \t \t \t ether doc_create_time: {ether_doc_create_time}')
                    # logger.info(f'doc_create_time match or not: {doc_create_time_match_num}') 
                    doc_create_time_match_lst.append(doc_create_time_match_num)
                    # logger.info("~~~~~RAW LOWERCASE CHEMO & EVENT~~~~~")
                    gold_chemo_ment, ether_event_ment = ent_eval_class.convert_chemo_event(patient_id, note_filename)
                    TP_event, FP_event, FN_event = ent_eval_class.calculate_lst(gold_chemo_ment, ether_event_ment)
                    patient_files_event["TP_event"].append(TP_event)
                    patient_files_event["FP_event"].append(FP_event)
                    patient_files_event["FN_event"].append(FN_event)
                    # logger.info("~~~~~RAW LOWERCASE TIME ~~~~~")
                    gold_time_ment, ether_time_ment = ent_eval_class.convert_time(patient_id, note_filename)
                    TP_time, FP_time, FN_time = ent_eval_class.calculate_lst(gold_time_ment, ether_time_ment)
                    patient_files_time["TP_time"].append(TP_time)
                    patient_files_time["FP_time"].append(FP_time)
                    patient_files_time["FN_time"].append(FN_time)

                logger.info("~~~~~CANCER_TYPE->PATIENT_ID level ~~~~~")
                doc_create_time_match_cnt = np.nansum(doc_create_time_match_lst)
                doc_create_time_non_match_cnt = Counter(doc_create_time_match_lst)[0]
                doc_create_time_nan_match_cnt = Counter(doc_create_time_match_lst)[np.nan]
                doc_create_time_match_percent = np.nanmean(doc_create_time_match_lst)
                logger.info(f"doc_create_time for the patient {dicts_class.mode}-{dicts_class.cancer_type}-{patient_id}:  match_cnt/1: {doc_create_time_match_cnt}, non_match_cnt/0: {doc_create_time_non_match_cnt}, nan_match_cnt: {doc_create_time_nan_match_cnt}, match percent(ignore nan): {doc_create_time_match_percent}")
                doc_create_time_match_cnt_lst.append(doc_create_time_match_cnt)
                doc_create_time_non_match_cnt_lst.append(doc_create_time_non_match_cnt)
                doc_create_time_nan_match_cnt_lst.append(doc_create_time_nan_match_cnt)
                
                
                event_match_cnt = np.sum(patient_files_event["TP_event"])
                event_match_fp, event_match_fn = np.sum(patient_files_event["FP_event"]), np.sum(patient_files_event["FN_event"])
                event_non_match_cnt = np.sum(patient_files_event["FP_event"]) + np.sum(patient_files_event["FN_event"])
                if (event_match_cnt+event_non_match_cnt) != 0:
                    event_match_percent = event_match_cnt / (event_match_cnt+event_non_match_cnt) 
                else:
                    event_match_percent = 0
                event_recall = np.sum(patient_files_event["TP_event"]) / (np.sum(patient_files_event["TP_event"]) + np.sum(patient_files_event["FN_event"]))
                logger.info(f"event/chemo for this patient {dicts_class.mode}-{dicts_class.cancer_type}-{patient_id}:  match_cnt/1/TP: {event_match_cnt}, FP: {event_match_fp}, FN: {event_match_fn}, non_match_cnt/0: {event_non_match_cnt}, match percent(ignore nan): {event_match_percent}, recall: {event_recall}") 
                event_match_tp_lst.append(event_match_cnt)
                event_match_fp_lst.append(event_match_fp)
                event_match_fn_lst.append(event_match_fn)
                event_recall_lst.append(event_recall)
                logger.debug(f"event_match_tp_lst: {event_match_tp_lst}")
                logger.debug(f"event_match_fn_lst: {event_match_fn_lst}")

                time_match_cnt = np.sum(patient_files_time["TP_time"])
                time_match_fp, time_match_fn = np.sum(patient_files_time["FP_time"]), np.sum(patient_files_time["FN_time"])
                time_non_match_cnt = np.sum(patient_files_time["FP_time"]) + np.sum(patient_files_time["FN_time"])
                if (time_match_cnt+time_non_match_cnt) != 0:
                    time_match_percent = time_match_cnt / (time_match_cnt+time_non_match_cnt) 
                else:
                    time_match_percent = 0
                time_recall = np.sum(patient_files_time["TP_time"]) / (np.sum(patient_files_time["TP_time"]) + np.sum(patient_files_time["FN_time"]))
                logger.info(f"time for this patient {dicts_class.mode}-{dicts_class.cancer_type}-{patient_id}:  match_cnt/1/TP: {time_match_cnt}, FP: {time_match_fp}, FN: {time_match_fn}, non_match_cnt/0: {time_non_match_cnt}, match percent(ignore nan): {time_match_percent}, recall: {time_recall}") 
                time_match_tp_lst.append(time_match_cnt)
                time_match_fp_lst.append(time_match_fp)
                time_match_fn_lst.append(time_match_fn)
                time_recall_lst.append(time_recall)
                logger.debug(f"time_match_tp_lst: {time_match_tp_lst}")
                logger.debug(f"time_match_fn_lst: {time_match_fn_lst}")


            logger.info(f"{event_match_tp_lst}")
            logger.info("~~~~~CANCER_TYPE level ~~~~~")
            cancer_type_doccreatetime_match_cnt = np.nansum(doc_create_time_match_cnt_lst)
            cancer_type_doccreatetime_non_match_cnt = np.nansum(doc_create_time_non_match_cnt_lst)
            percent = np.nansum(doc_create_time_match_cnt_lst) / (np.nansum(doc_create_time_match_cnt_lst)+np.nansum(doc_create_time_non_match_cnt_lst)+np.nansum(doc_create_time_nan_match_cnt_lst))
            logger.info(f"doc_created_time for {dicts_class.mode}-{dicts_class.cancer_type}:  match_cnt/1: {cancer_type_doccreatetime_match_cnt}, non_match_cnt/0: {cancer_type_doccreatetime_non_match_cnt}, nan_match_cnt: {np.nansum(doc_create_time_nan_match_cnt_lst)}, match percent(ignore nan): {percent}")
            
            percent = np.nansum(event_match_tp_lst) / (np.nansum(event_match_tp_lst) + np.nansum(event_match_fp_lst)+ np.nansum(event_match_fn_lst))
            recall = np.nansum(event_recall_lst) / len(event_recall_lst)
            logger.info(f"event/chemo for {dicts_class.mode}-{dicts_class.cancer_type}: match_cnt/1: {np.nansum(event_match_tp_lst)}, non_match_cnt/0: {np.nansum(event_match_fp_lst)+np.nansum(event_match_fn_lst)}, match percent(ignore nan): {percent}, recall: {recall}")

            percent = np.nansum(time_match_tp_lst) / (np.nansum(time_match_tp_lst) + np.nansum(time_match_fp_lst)+ np.nansum(time_match_fn_lst))
            recall = np.nansum(time_recall_lst) / len(time_recall_lst)
            logger.info(f"time for {dicts_class.mode}-{dicts_class.cancer_type}: match_cnt/1: {np.nansum(time_match_tp_lst)}, non_match_cnt/0: {np.nansum(time_match_fp_lst)+np.nansum(time_match_fn_lst)}, match percent(ignore nan): {percent}, recall: {recall}")
    '''
    with open(total_gold_dct_file, "w") as f:
        json.dump(total_gold_dct, f)

    # with open(total_ether_dct_file, "w") as f:
    #     json.dump(total_ether_dct, f)

if __name__ == "__main__":
#     ################
    OUTPUT_DIR = "S:\Chemo_Challenge"
    main(OUTPUT_DIR)