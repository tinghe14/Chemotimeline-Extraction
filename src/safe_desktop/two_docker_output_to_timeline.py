
"""
Convert predictions of run_glue.py to event-timex pairs and summarize to timelines.
"""
import re
import os
import json
from typing import List, Set, Tuple
import pandas as pd
from collections import defaultdict
import numpy as np 
import logging

logger = logging.getLogger("my_logger")

CHEMO_MENTIONS = {
    "chemotherapy",
    "chemo",
    "chem",
    "chemo therapy",
    "chemo-radiation",
    "chemo-rt",
    "chemoembolization",
    "chemorad",
    "chemoirradiation",
    "chemort",
    "chemotherapeutic",
    "chemotherap",
    "chemotherapies",
    "chemotherapeutic",
    "chemotherapy's",
    "chemotheray",
    "chemoradiation",
}

label_to_hierarchy = {
    "begins-on": 1,
    "ends-on": 1,
    "contains": 2,
    "contains-1": 2,
    "before": 3,
}

NORMALIZED_TIMEXES_TO_SKIP = {"Luz 5", "P2000D"}


def rank_labels(labels):
    label_rankings = {lbl: label_to_hierarchy[lbl] for lbl in labels}
    label_rankings = sorted(label_rankings.items(), key=lambda x: x[1])
    return label_rankings[0][0]


def deduplicate(timelines):
    merged_rows = defaultdict(lambda: defaultdict(set))
    chemo_date_map = defaultdict(lambda: defaultdict(list))
    for row in timelines:
        pid, note_name, source_id, source_text, rel, target_id, target_text = row
        source_text = source_text.lower()
        target_text = target_text.lower()
        # Taking care of timex like this: 2013-10-30T06:47
        if "t" in target_text:
            target_text = target_text.split("t")[0]
        if "p" == target_text[0] and "d" in target_text[-1]:
            continue
        note_id = pid+"_"+note_name
        patient_id = pid

        merged_rows[patient_id][(source_text, rel)].add(target_text)

        chemo_date_map[patient_id][(target_text, rel)].append(source_text)

    deduplicated = defaultdict(list)
    for patient, treatments in merged_rows.items():
        one_patient_timelines = []
        chemos_same_day_rel = chemo_date_map[patient]
        for k, v in treatments.items():
            for target in v:
                if k[0] in CHEMO_MENTIONS:
                    has_specific_chemo = False
                    if (target, k[1]) in chemos_same_day_rel:
                        for medication in chemos_same_day_rel[(target, k[1])]:
                            if medication not in CHEMO_MENTIONS:
                                has_specific_chemo = True
                    if not has_specific_chemo:
                        if [k[0], k[1], target] not in one_patient_timelines:
                            one_patient_timelines.append([k[0], k[1], target])
                else:
                    if [k[0], k[1], target] not in one_patient_timelines:
                        one_patient_timelines.append([k[0], k[1], target])
        deduplicated[patient] = one_patient_timelines

    return deduplicated


def conflict_resolution(timelines):
    resolved_timelines = defaultdict(list)
    for patient, treatments in timelines.items():
        source_target_to_rel = defaultdict(list)
        for tup in treatments:
            s, r, t = tup
            source_target_to_rel[(s, t)].append(r)
        for pair, labels in source_target_to_rel.items():
            if len(labels) > 1:
                more_specific_lbl = rank_labels(labels)
                resolved_timelines[patient].append(
                    [pair[0], more_specific_lbl, pair[1]]
                )
            else:
                resolved_timelines[patient].append([pair[0], labels[0], pair[1]])
    return resolved_timelines


def write_to_output(data, outfile_name):
    with open(outfile_name, "w", encoding="utf-8") as fw:
        json.dump(data, fw)


def keep_normalized_timex(pandas_col) -> bool:
    normalized_timex = pandas_col.normed_timex
    return normalized_timex.split("-")[0].isnumeric()


# not implementing prune by modality and
# prune by polarity since that's currently happening
# upstream to save processing time.
# you can turn that off in
# timeline_delegator.py in the Docker
def convert_docker_output(OUTPUT_DIR: str, cancer_type, mode) -> Tuple[List[str], Set[str]]:
    docker_output_dataframe = pd.read_csv(os.path.join(OUTPUT_DIR, f"1_{cancer_type}_{mode}_ether.tsv"), sep="\t")
    no_none_tlinks = docker_output_dataframe[
        ~docker_output_dataframe["tlink"].isin(["none"]) # this won't happen in our case
    ]

    normed_timexes_with_tlinks = no_none_tlinks[
        ~no_none_tlinks["normed_timex"].isin([np.nan])
    ]

    # print(normed_timexes_with_tlinks["normed_timex"])
    # print(type(normed_timexes_with_tlinks.loc[1,"normed_timex"]), normed_timexes_with_tlinks.loc[1,"normed_timex"])

    acceptable_normed_timexes_with_tlinks = normed_timexes_with_tlinks[
    normed_timexes_with_tlinks.apply(keep_normalized_timex, axis=1)
    ]

    no_discovery_pt_ids = set(docker_output_dataframe["patient_id"]) - set(
        acceptable_normed_timexes_with_tlinks["patient_id"]
    )

    timeline_tups = acceptable_normed_timexes_with_tlinks[
        [   "patient_id",
            "note_name",
            "chemo_annotation_id",
            "chemo_text",
            "tlink",
            "timex_annotation_id",
            "normed_timex",
        ]
    ].values.tolist()

    return timeline_tups, no_discovery_pt_ids


def main(OUTPUT_DIR, cancer_type, mode):

    timelines_tups, no_discovery_pt_ids = convert_docker_output(OUTPUT_DIR, cancer_type, mode)

    timelines_deduplicated = deduplicate(timelines_tups)
    resolved_timelines = conflict_resolution(timelines_deduplicated)

    # dumbest hack I've written so far this year but
    for patient_id in no_discovery_pt_ids:
        resolved_timelines[patient_id] = []

    outfile_name = "2_"+cancer_type + f"_{mode}_system_timelines"

    outfile_name += ".json"

    write_to_output(
        resolved_timelines,
        os.path.join(OUTPUT_DIR, outfile_name),
    )
    print(f"Wrote summarized outputs to {outfile_name}")

'''
if __name__ == "__main__":
    main()
'''

#python 2_docker_output_to_timeline.py --output_dir S:\Chemo_Challenge\0309_new_cancer_drug_lexicon\1_ovarian_dev_ether.tsv --cancer_type ovarian --output_dir S:\Chemo_Challenge\0309_new_cancer_drug_lexicon
# WHEN DIRECTLY RUN, will get: ValueError: Invalid file path or buffer object type: <class 'NoneType'>
# python 2_docker_output_to_timeline.py --output_dir S:\Chemo_Challenge\0309_new_cancer_drug_lexicon\1_breast_dev_ether.tsv --cancer_type breast --output_dir S:\Chemo_Challenge\0309_new_cancer_drug_lexicon
# python 2_docker_output_to_timeline.py --output_dir S:\Chemo_Challenge\0309_new_cancer_drug_lexicon\1_melanoma_dev_ether.tsv --cancer_type melanoma --output_dir S:\Chemo_Challenge\0309_new_cancer_drug_lexicon