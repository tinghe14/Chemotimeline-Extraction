
"""
1. read ether output json file as dict
2. assign relation between every chemo entities & time entities, default as CONTAIN
3. convert to the format eval script takes as input
4. convert
5. get performance
"""
import os 
import json
import pandas as pd 
import numpy as np 
import datetime
import logging
import json


logger = logging.getLogger("my_logger."+__name__)

def _read_json_dct(DCT_DIR, cancer_type_mode, gold_or_ether):
    """cancer_type_mode: breast_train, breast_dev ... or total"""
    DCT_FILE = os.path.join(DCT_DIR, "0_"+cancer_type_mode+"_"+gold_or_ether+"_"+"dct.json")
    with open(DCT_FILE, "r") as infile:
        dct = json.load(infile) 
        return dct 

def convert_tsv(dct, OUT_DIR):
    """convert ether dct output to tsv format"""
    df = pd.DataFrame()
    for pid in dct.keys():
        temp_pid = pd.DataFrame()
        event_ment_lst, time_ment_lst = [], [] 
        for file in dct[pid].keys():
            temp_pid_file = pd.DataFrame()

            chemo_id_lst = dct[pid][file]["pair_wise"]["event"]["id"]
            time_id_lst = dct[pid][file]["pair_wise"]["time"]["id"]
            comb_ids = [(x, y) for x in chemo_id_lst for y in time_id_lst]
            temp_pid_file["chemo_annotation_id"] = [int(x) for (x,y) in comb_ids]
            temp_pid_file["timex_annotation_id"] = [int(y) for (x,y) in comb_ids]
            temp_pid_file["DCT"], temp_pid_file["patient_id"], temp_pid_file["note_name"] = datetime.datetime.fromisoformat(dct[pid][file]["doc_create_time"]).date().isoformat(), pid, file
            # PRED TLINK
            temp_pid_file["tlink"] = "contains-1"
            temp_pid_file["chemo_text"] = np.take(dct[pid][file]["pair_wise"]["event"]["ment"], [x for (x,y) in comb_ids], axis=0)
            temp_pid_file["normed_timex"] = np.take(dct[pid][file]["pair_wise"]["time"]["normalized_time"], [y for (x,y) in comb_ids], axis=0)
            # temp_pid_file["tlink_inst"] = temp_pid_file["chemo_text"].str.cat(temp_pid_file["normed_timex"], sep=" VS ") need to deal with []
            temp_pid_file["normed_timex"] = temp_pid_file["normed_timex"].replace("nan", np.nan)
            temp_pid_file["normed_timex"] = temp_pid_file["normed_timex"].apply(lambda x: datetime.datetime.fromisoformat(x).date().isoformat() if pd.notnull(x) else x)
            temp_pid = pd.concat([temp_pid, temp_pid_file], axis=0)
        df = pd.concat([df, temp_pid], axis=0)
    df.to_csv(OUT_DIR, sep="\t",index=False) 

def main(DCT_DIR, MODE):
    for cancer in ["breast", "ovarian", "melanoma"]:
        ether_or_gold = "ether"
        OUT_FILE = os.path.join(DCT_DIR, "1_"+cancer+"_"+MODE+"_ether.tsv")
        cancer_mode = cancer+"_"+MODE
        dct = _read_json_dct(DCT_DIR, cancer_mode, ether_or_gold, )
        convert_tsv(dct, OUT_FILE)
    


if __name__ == "__main__":
    ################
    # OUTPUT_DIR = "S:\\Chemo_Challenge\\0309_new_cancer_drug_lexicon"
    # main(OUTPUT_DIR)
    DCT_DIR, MODE = "S:\Chemo_Challenge\\0312_temp_test\\0318_check_true_lexicon","dev"
    main(DCT_DIR, MODE)
                