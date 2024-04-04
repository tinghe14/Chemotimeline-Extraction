
import os, sys
from typing import List, Dict, Optional, Union
import logging
import numpy as np
import pandas as pd
import json
import xml.etree.ElementTree as et 
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime
from collections import Counter

sys.path.append("S:\\Chemo_Challenge")
from collections import defaultdict, namedtuple
import argparse
import zero_gen_ann_dict_gold_dict as zero 
import one_convert_ether_eval_pairwise_input as one
import two_docker_output_to_timeline as two
import three_eval_timeline as three
import random 

parser = argparse.ArgumentParser(description="")
# ETHERArguments:
parser.add_argument("--output_dir", type=str)
parser.add_argument("--mode", type=Optional[str], help="select mode of dataset",choices=["train", "dev", "test"])

# Debug Arguments:
parser.add_argument("--rerun", type=bool, help="wether need to generate the pred patient-level triple relationship again")
parser.add_argument("--gold_id_path", type=Union[str, None], default=None,
                    help="(Only for test evaluation) Path to file with list of gold annotated ids, delimited by new line characters")
parser.add_argument("--debug_mode", type=bool, help="Whether turn on debug mode")
parser.add_argument("--cancer_type", type=Optional[str], help="For debugging purposes, select certain cancer type for evaluation")


def main(): 
    if len(sys.argv)==2 and sys.argv[1].endswith(".json"):
        with open(sys.argv[1], "r") as json_file:
            data = json.load(json_file)
        AllArgs = namedtuple("AllArgs", list(data.keys()))
        args = AllArgs(**data)
    else:
        print("Need to have a JSON file with argument")

    
    date = datetime.now().date() 
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m/%d%Y %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(os.path.join(args.output_dir, f"{date}.log"), mode="w")
    logger.addHandler(fh)
    logger.info(args)

    if not args.debug_mode:
        if args.rerun:
            # Generate Cancer-Level Dcts
            zero.main(args.output_dir)
            # Convert to Pair-wise Level
            one.main(args.output_dir, args.mode)
            for cancer_type in ["breast", "ovarian", "melanoma"]:
                # Convert Pair-wise to Patient-level 
                two.main(args.output_dir, cancer_type, args.mode)
        for cancer_type in ["breast", "ovarian", "melanoma"]:
            logger.info(f"#####################################")
            logger.info(f"################### cancer type:{cancer_type} ###################")
            # Final Evaluation
            subtask1_dir = "S:\Chemo_Challenge\chemoTimelines2024_train_dev_labeled\subtask1"
            gold_path = os.path.join(subtask1_dir, "Gold_Timelines_allPatients", f"{cancer_type}_{args.mode}_all_patients_gold_timelines.json")
            pred_path = os.path.join(args.output_dir, f"2_{cancer_type}_{args.mode}_system_timelines.json")
            all_id_path = os.path.join(subtask1_dir, "All_Patient_IDs", f"{cancer_type}_{args.mode}_patient_ids.txt")
            three.main(gold_path, pred_path, all_id_path, args)
    else: 
        # Random Choose One in Gold Dict and Compare with the Same One in Pred Dict
        GOLD_DCT_FILE = os.path.join("S:\\Chemo_Challenge",f"0_{args.cancer_type}_{args.mode}_gold_dct.json")
        with open(GOLD_DCT_FILE, "r") as goldfile:
            gold_dct = json.load(goldfile)
        PRED_DCT_FILE = os.path.join(args.output_dir, f"0_{args.cancer_type}_{args.mode}_ether_dct.json")
        with open(PRED_DCT_FILE, "r") as predfile:
            pred_dct = json.load(predfile)
        selected_patientid = random.choice(list(gold_dct.keys()))
        selected_filename = random.choice(list(gold_dct[selected_patientid].keys()))
        gold_doc_create_time = gold_dct[selected_patientid][selected_filename]["doc_create_time"]["ment"]
        ether_doc_create_time = pred_dct[selected_patientid][selected_filename]["doc_create_time"]

        print(f"GOLD: {gold_doc_create_time} PRED: {ether_doc_create_time}")
 

if __name__ == "__main__":
#   python 4_run_all.py S:\Chemo_Challenge\2024-03-08_0_kory_chemo_drug.json
    main()