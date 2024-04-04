#!/bin/bash
#SBATCH --job-name=test_all
#SBATCH --partition=gpu
#SBATCH --nodes=1 # Run all processes on a single node
#SBATCH --gres=gpu:1 #--gres=gpu:tesv100:2 
#SBATCH --time=128:00:00 # Time limit hrs:min:sec
#SBATCH -o /users/the/NER_MTB/my/1_change_n2space/0326_n2space_cancer_test.log
#SBATCH --mail-type=begin
#SBATCH --mail-type=end
#SBATCH --mail-user=the14@jh.edu

# something wrong with the script!!! use the single one!!!!
cd /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/timelines

echo "**** Job starts ****"
date
# load conda env
module load conda
source activate timelines
echo "**** JHPCE info ****"
echo "User: ${USER}"
echo "Job id: ${JOB_ID}"
echo "Job name: ${JOB_NAME}"
echo "Hostname: ${HOSTNAME}"
echo "Task id: ${SGE_TASK_ID}"
echo "Conda Env: ${CONDA_DEFAULT_ENV}"
echo "Conda Env: ${CONDA_PREFIX}"

mvn -U clean package
/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/timelines/mybroker/bin/artemis-service start
date
CANCER_TYPE=("breast" "ovarian" "melanoma")
export mode=test
for cancer in "${CANCER_TYPE[@]}"
do
    echo "Running Command for ${cancer} ..."
    java -cp instance-generator/target/instance-generator-5.0.0-SNAPSHOT-jar-with-dependencies.jar \
        org.apache.ctakes.core.pipeline.PiperFileRunner \
        -p org/apache/ctakes/timelines/pipeline/Timelines \
        -a  mybroker \
        -v /users/the/.conda/envs/timelines \
        -i /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/input/change_n2space/input_${cancer}_${mode} \
        -o /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/change_n2space \
        -l org/apache/ctakes/dictionary/lookup/fast/bsv/Unified_Gold_Dev.xml \
        --pipPbj yes
    echo "Finish Running Command for ${cancer} ..."
    cd /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/change_n2space # can't work don no why
    mv -- unsummarized_output.tsv unsummarized_${cancer}_${mode}_output.tsv
    mybroker/bin/artemis stop
    date

    # echo "Running Command to Summarize ${cancer} File ..."
    # python /users/the/NER_MTB/timelines/docker_output_to_timeline/docker_output_to_timeline.py \
    # --docker_tsv_output_path /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/change_n2space/unsummarized_${cancer}_train_output.tsv \
    # --cancer_type ${cancer} \
    # --output_dir /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/change_n2space
    # echo "Finish Running Command to Summarize ${cancer} File ..."
    # date 

    # echo "Running Command to Clean ${cancer} File ..."
    # python /users/the/NER_MTB/my/change_n2space/run_after.py \
    # --summarized_timeline_file /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/change_n2space/${cancer}_train_system_timelines.json \
    # --all_ids_file "/users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_train_patient_ids.txt" \
    # --cancer ${cancer}
    # echo "Finish Running Command to Clean ${cancer} File ..."
    # date 

    # echo "Running Command to eval ${cancer} File ..."
    # echo "!!!strict!!!..."
    # python /users/the/NER_MTB/timelines/docker_output_to_timeline/eval_timeline.py \
    # --gold_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/Gold_Timelines_allPatients/${cancer}_train_all_patients_gold_timelines.json \
    # --pred_path /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/change_n2space/cleaned_${cancer}_train.json \
    # --all_id_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_train_patient_ids.txt \
    # --strict

    # echo "!!!relax day!!!..."
    # python /users/the/NER_MTB/timelines/docker_output_to_timeline/eval_timeline.py \
    # --gold_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/Gold_Timelines_allPatients/${cancer}_train_all_patients_gold_timelines.json \
    # --pred_path /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/change_n2space/cleaned_${cancer}_train.json \
    # --all_id_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_train_patient_ids.txt \
    # --relaxed_to day

    # echo "!!!relax month!!!..."
    # python /users/the/NER_MTB/timelines/docker_output_to_timeline/eval_timeline.py \
    # --gold_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/Gold_Timelines_allPatients/${cancer}_train_all_patients_gold_timelines.json \
    # --pred_path /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/change_n2space/cleaned_${cancer}_train.json \
    # --all_id_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_train_patient_ids.txt \
    # --relaxed_to month

    # echo "!!!relax year!!!..."
    # python /users/the/NER_MTB/timelines/docker_output_to_timeline/eval_timeline.py \
    # --gold_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/Gold_Timelines_allPatients/${cancer}_train_all_patients_gold_timelines.json \
    # --pred_path /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/change_n2space/cleaned_${cancer}_train.json \
    # --all_id_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_train_patient_ids.txt \
    # --relaxed_to year
done
date



