import json
import pandas as pd 
import numpy as np
import re

# BASELINE PREDICTION: extract raw time
def find_strings_between_flags(main_string):
    pattern = re.compile(r'<t>(.*?)</t>', re.DOTALL)
    matches = pattern.findall(main_string)
    return matches

baseline_pred_file = "/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/all_except_breast_dev_unsummarized_output.tsv"
# generate raw timex for baseline pred file 
baseline_pred_df = pd.read_csv(baseline_pred_file, delimiter="\t")
pred_unique_note_name = list(set(baseline_pred_df["note_name"]))
pred_unique_pat_id = list(set(baseline_pred_df["patient_id"]))
time_lst = baseline_pred_df["tlink_inst"].apply(find_strings_between_flags)
baseline_pred_df["timex"] = [x[0] if len(x)> 0 else "none" for x in time_lst]
baseline_pred_df.replace({"none": np.nan}, inplace=True)
baseline_pred_df.drop(columns=["patient_id", "chemo_annotation_id", "timex_annotation_id", "tlink"], inplace=True)
baseline_pred_df.dropna(subset=["normed_timex"], inplace=True)

id = baseline_pred_df.pop("note_name")
baseline_pred_df.insert(0, "note_name", id)
raw_time = baseline_pred_df.pop("timex")
baseline_pred_df.insert(3, "timex", raw_time)

baseline_pred_df.to_csv("./time_ment/chemo_time_rel.csv", index=None)

# Explore
## time ment accuracy
"""how well of the system to extract time ment"""
# GOLD: raw time related to chemo
# BASELINE PREDICTION: raw time related to chemo
# ETHER PREDICTION: all raw time

gold_json_file = "/users/the/NER_MTB/0_breast_train_gold_dct.json"
gold_ids_file = "/users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/breast_train_patient_ids.txt"
ether_pred_file = "/users/the/NER_MTB/temp_0_breast_ether_dct.json"

gold_ids = []
with open(gold_ids_file, "r") as infile:
    lines = infile.readlines()
gold_ids.extend([id.strip() for id in lines])
sorted(gold_ids)
with open(gold_json_file, "r") as infile:
    gold_dct = json.load(infile)

with open(ether_pred_file, "r") as infile:
    ether_dct = json.load(infile)

def _helper_baseline(baseline_pred_df, pat_id, filename):
    print("BASELINE PREDICTION: ")
    baseline_pred_chemo = baseline_pred_df[baseline_pred_df["note_name"] == pat_id+"_"+filename][["DCT","chemo_text","normed_timex","timex"]]
    baseline_pred_chemo.drop_duplicates(inplace=True)
    sorted_baseline_pred_chemo = baseline_pred_chemo.sort_values(by="timex").reset_index(drop=True)
    sorted_baseline_pred_chemo.columns = ["DCT","chemo_text","normed_rel_time","rel_raw_time"]
    print(sorted_baseline_pred_chemo)

def _helper_ether(ether_dct, pat_id, filename):
    print("ETHER PREDICTION: ")
    ether_time_lst, ether_normed_time_lst = ether_dct[pat_id][filename]["pair_wise"]["time"]["ment"], ether_dct[pat_id][filename]["pair_wise"]["time"]["normalized_time"]
    ether_dctime = ether_dct[pat_id][filename]["doc_create_time"]
    ether_df = pd.DataFrame({"DCT": ether_dctime, "normed_all_timex": ether_normed_time_lst, "all_timex":ether_time_lst})
    ether_df = ether_df.sort_values(by="all_timex").reset_index(drop=True)
    # ether_df["DCT"], ether_df["normed_all_timex"] = pd.to_datetime(ether_df["DCT"], errors='coerce'), pd.to_datetime(ether_df["normed_all_timex"], errors='coerce')
    print(ether_df)

def _helper_gold(gold_dct, pat_id, filename):
    print("GOLD:")
    # not always: source: chemo, target: time
    gold_chemo_id_lst, gold_time_id_lst = gold_dct[pat_id][filename]["chemo_time_rel"]["source_id"], gold_dct[pat_id][filename]["chemo_time_rel"]["target_id"]
    gold_tlink_lst = gold_dct[pat_id][filename]["chemo_time_rel"]["rel_type"]
    gold_dct_str = gold_dct[pat_id][filename]["doc_create_time"]["ment"]
    if (gold_dct_str is not None) and (gold_dct_str[-1] == "\n"):
        gold_dct_str = gold_dct_str[:-1]
    gold_tuple= []
    for gold_chemo_id, gold_time_id in zip(gold_chemo_id_lst, gold_time_id_lst):
        if gold_chemo_id in gold_dct[pat_id][filename]["pair_wise"]["chemo"]["ment_id"]:
            gold_chemo_ind, gold_timex_ind = gold_dct[pat_id][filename]["pair_wise"]["chemo"]["ment_id"].index(gold_chemo_id), gold_dct[pat_id][filename]["pair_wise"]["time"]["ment_id"].index(gold_time_id)
        else:
            gold_chemo_ind, gold_timex_ind = gold_dct[pat_id][filename]["pair_wise"]["chemo"]["ment_id"].index(gold_time_id), gold_dct[pat_id][filename]["pair_wise"]["time"]["ment_id"].index(gold_chemo_id)
        gold_chemo, gold_timex =  gold_dct[pat_id][filename]["pair_wise"]["chemo"]["ment"][gold_chemo_ind], gold_dct[pat_id][filename]["pair_wise"]["time"]["ment"][gold_timex_ind]
        gold_tuple.append([gold_chemo, gold_timex])
    sorted_gold_tuple = sorted(gold_tuple, key=lambda x: x[1])
    gold_df = pd.DataFrame(sorted_gold_tuple, columns=["chemo", "rel_raw_time"])
    gold_df.insert(0, "DCT", gold_dct_str)
    gold_df["original_DCT"] = gold_df["DCT"]
    gold_df["DCT"] = pd.to_datetime(gold_df["DCT"], format="%Y%m%d")
    gold_df["DCT"] = gold_df["DCT"].fillna(gold_df["original_DCT"])
    gold_df["tlink"] = gold_tlink_lst
    gold_df.drop(columns=["original_DCT"], inplace=True)
    if gold_df.shape[0] == 0:
        print("The GOLD file didn't find any chemo related time")
    else:
        print(gold_df)

for pat_id in gold_ids:
    print(f"~~~~~~~~{pat_id}~~~~~~~~")
    if pat_id in gold_dct.keys():
        baseline_patid_bool, ether_patid_bool = pat_id in pred_unique_pat_id, pat_id in ether_dct.keys()
        if baseline_patid_bool and ether_patid_bool:
            for filename in sorted(list(gold_dct[pat_id].keys())):
                print("~~~~~~~~filename: ", pat_id+"_"+filename, "~~~~~~~~")

                _helper_gold(gold_dct, pat_id, filename)

                baseline_bool, ether_bool = (pat_id+"_"+filename) in pred_unique_note_name, filename in ether_dct[pat_id].keys() 
                if (not baseline_bool) and ether_bool:
                    print("The BASELINE pred file didn't find this filename")
                    #_helper_ether(ether_dct, pat_id, filename)
                elif baseline_bool and (not ether_bool):
                    _helper_baseline(baseline_pred_df, pat_id, filename)
                    print("The ETHER pred file for didn't find this filename")
                elif baseline_bool and ether_bool:
                    _helper_baseline(baseline_pred_df, pat_id, filename)
                    #_helper_ether(ether_dct, pat_id, filename)
                else:
                    print("BASELINE AND ETHER pred file didn't this filename")
        elif (not baseline_patid_bool) and ether_patid_bool:

            for filename in sorted(list(gold_dct[pat_id].keys())):
                print("~~~~~~~~filename: ", pat_id+"_"+filename, "~~~~~~~~")
                _helper_gold(gold_dct, pat_id, filename)
                
                print("The BASELINE pred file didn't have this patient_id")

                ether_bool = filename in ether_dct[pat_id].keys() 
                if ether_bool:
                    _helper_ether(ether_dct, pat_id, filename)
                else:
                    print("The ETHER pred file for didn't find this filename")

        elif baseline_patid_bool and (not ether_patid_bool):
            pass # do something with baseline 
            print("~~~~~~~~filename: ", pat_id+"_"+filename, "~~~~~~~~")
            _helper_gold(gold_dct, pat_id, filename)
            
            baseline_bool = (pat_id+"_"+filename) in pred_unique_note_name
            if not baseline_bool:
                print("The BASELINE pred file didn't find this filename")
                print("The ETHER pred file didn't have this patient_id")
            else:
                _helper_baseline(baseline_pred_df, pat_id, filename)
                print("The ETHER pred file for didn't find this filename")
        else: 
            print("The BASELINE AND ETHER pred file didn't have this patient_id")
    else: 
        continue

from datasets import load_dataset
# <formulation> = {nli, pairwise, mrc, timeline}
dataset = load_dataset("kimihiroh/timeset", formulation={"timeline"}, trust_remote_code=True)
