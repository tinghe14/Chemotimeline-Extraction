import json
import pandas as pd 

# Explore
## chemo ment accuracy
"""how well of the system to extract chemo ment"""
# 0. check the index from chemo -> checked 
# 1. percentage of match, miss, over predict
# 2. those 3 percents group by cancer type 
cancer, mode = "ovarian", "dev"
pred_file = f"/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/change_n2space/unsummarized_{cancer}_{mode}_output.tsv"
gold_json_file = f"/users/the/NER_MTB/0_{cancer}_{mode}_gold_dct.json"
gold_ids_file = f"/users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/{cancer}_{mode}_patient_ids.txt"

gold_ids = []
with open(gold_ids_file, "r") as infile:
    lines = infile.readlines()
gold_ids.extend([id.strip() for id in lines])
sorted(gold_ids)
with open(gold_json_file, "r") as infile:
    gold_dct = json.load(infile)

pred_df = pd.read_csv(pred_file, delimiter="\t")
pred_unique_note_name = list(set(pred_df["note_name"]))
pred_unique_pat_id = list(set(pred_df["patient_id"]))

gold_chemo_all, pred_chemo_all = [], []
for pat_id in gold_ids:
    print(f"~~~~~~~~{pat_id}~~~~~~~~")
    gold_chemo = []
    if pat_id in gold_dct.keys() :
        for filename in sorted(list(gold_dct[pat_id].keys())):
            if (pat_id+"_"+filename) not in pred_unique_note_name:
                print("The pred file for didn't find this patient with this filename")
                continue
            print("~~~~~~~~filename: ", pat_id+"_"+filename, "~~~~~~~~")
            gold_chemo = sorted(list(set(gold_dct[pat_id][filename]["pair_wise"]["chemo"]["ment"])))
            print("GOLD:")
            print(gold_chemo)
            pred_chemo = sorted(list(set(pred_df[pred_df["note_name"] == pat_id+"_"+filename]["chemo_text"].tolist())))
            print("PREDICTION: ")
            print(pred_chemo)
    else: 
        continue
        '''
        print("The gold file for this patient didn't find any chemo mention at all")
        if pat_id not in pred_unique_pat_id:
            print("The pred file for this patient didn't find any chemo mention at all")
        else:
            pred_pat_id_df = pred_df[pred_df.loc[:,"patient_id"] == pat_id]
            pred_note_name = sorted(list(set(pred_pat_id_df["note_name"])))
            for filename in pred_note_name:
                pred_chemo = pred_pat_id_df[pred_pat_id_df["note_name"] == pat_id+"_"+filename]["chemo_text"].tolist()
                print("~~~~~~~~filename: ", pat_id+"_"+filename, "~~~~~~~~")
                if len(pred_chemo) == 0:
                    print("The pred file for didn't find this patient with this filename")
                    continue
                print("PREDICTION:")
                print(sorted(list(set(pred_chemo))))
        '''
     # copy from above 
# 0. check the index from chemo -> checked 
# 1. percentage of match, miss, over predict
# 2. those 3 percents group by cancer type 
pred_file = "/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/change_n2space/unsummarized_melanoma_train_output.tsv"
gold_json_file = "/users/the/NER_MTB/0_melanoma_train_gold_dct.json"
gold_ids_file = "/users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/melanoma_train_patient_ids.txt"

gold_ids = []
with open(gold_ids_file, "r") as infile:
    lines = infile.readlines()
gold_ids.extend([id.strip() for id in lines])
sorted(gold_ids)
with open(gold_json_file, "r") as infile:
    gold_dct = json.load(infile)

pred_df = pd.read_csv(pred_file, delimiter="\t")
pred_unique_note_name = list(set(pred_df["note_name"]))
pred_unique_pat_id = list(set(pred_df["patient_id"]))

gold_chemo_all, pred_chemo_all = [], []
for pat_id in gold_ids:
    print(f"~~~~~~~~{pat_id}~~~~~~~~")
    gold_chemo = []
    if pat_id in gold_dct.keys() :
        for filename in sorted(list(gold_dct[pat_id].keys())):
            if (pat_id+"_"+filename) not in pred_unique_note_name:
                print("The pred file for didn't find this patient with this filename")
                continue
            print("~~~~~~~~filename: ", pat_id+"_"+filename, "~~~~~~~~")
            gold_chemo = sorted(list(set(gold_dct[pat_id][filename]["pair_wise"]["chemo"]["ment"])))
            print("GOLD:")
            print(gold_chemo)
            pred_chemo = sorted(list(set(pred_df[pred_df["note_name"] == pat_id+"_"+filename]["chemo_text"].tolist())))
            print("PREDICTION: ")
            print(pred_chemo)
    else: 
        continue
