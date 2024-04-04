from collections import defaultdict
import json
import os
import argparse
# from patient note to summarized output using baseline

# ZERO. Convert \n to Space

# ONE. From Patient Note to Unsummarized Baseline Output
# src 1

# TWO.Add Lookup Dict
# TO-DO

# THREE. From Unsummarized Output to Patient Level
# src 2
parser = argparse.ArgumentParser(description="")

parser.add_argument("--summarized_timeline_file", type=str)
parser.add_argument("--all_ids_file", type=str)
parser.add_argument("--cancer", type=str)
parser.add_argument("--mode", choices=["train", "dev"])

# FOUR. Add Empty Patient Pair
def clean_file(summarized_timeline_file, all_ids_file, cancer, mode):
    out_dct = defaultdict(list)
    with open(summarized_timeline_file, "r") as infile:
        dct = json.load(infile)
    out_lst = []
    with open(all_ids_file, "r") as infile:
        lines = infile.readlines()
        for line in lines: 
            out_lst.append(line[:-1])
    # remove not from pat all id file
    for pat_id in dct.keys():
        if pat_id in out_lst:
            out_dct[pat_id] = dct[pat_id]
    # add pred file but missing pat id in pat all id file
    for pat_id in out_lst:
        if pat_id not in out_dct.keys():
            out_dct[pat_id] = []
    outfile = os.path.join("/users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/2_change_t2space",\
                           f"cleaned_{cancer}_{mode}.json")
    with open(outfile, "w") as outfile: 
        json.dump(out_dct, outfile)
# Five. Eval


def main():
    args = parser.parse_args()
    clean_file(args.summarized_timeline_file, args.all_ids_file, args.cancer, args.mode)

if __name__ == "__main__":
    main()