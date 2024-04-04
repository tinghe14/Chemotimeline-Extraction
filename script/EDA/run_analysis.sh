#!/bin/bash
#SBATCH --job-name=maven_test
#SBATCH --partition=shared
#SBATCH --nodes=1 # Run all processes on a single node
#SBATCH --cpus-per-task=2
#SBATCH --time=128:00:00 # Time limit hrs:min:sec
#SBATCH -o /users/the/NER_MTB/my/2_change_t2space/0325_eval_t2space_melanoma_dev_cpu.log
#SBATCH --mail-type=begin
#SBATCH --mail-type=end
#SBATCH --mail-user=the14@jh.edu

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

# mvn -U clean package
/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/timelines/mybroker/bin/artemis-service start
date
CANCER_TYPE=("breast" "melanoma")
for cancer in "${CANCER_TYPE[@]}"
do
    echo "Running Command for ${cancer} ..."
    # java -cp instance-generator/target/instance-generator-5.0.0-SNAPSHOT-jar-with-dependencies.jar \
    #     org.apache.ctakes.core.pipeline.PiperFileRunner \
    #     -p org/apache/ctakes/timelines/pipeline/Timelines \
    #     -a  mybroker \
    #     -v /users/the/.conda/envs/timelines \
    #     -i ../input/change_n2space/input_${cancer}_train \
    #     -o ../output/change_n2space \
    #     -l org/apache/ctakes/dictionary/lookup/fast/bsv/Unified_Gold_Dev.xml \
    #     --pipPbj yes
    # mv /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/change_n2space/unsummarized_output.tsv /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/change_n2space/unsummarized_${cancer}_train_output.tsv
    echo "Finish Running Command for ${cancer} ..."
    date

    echo "Running Command to Summarize ${cancer} File ..."
    python /users/the/NER_MTB/timelines/docker_output_to_timeline/docker_output_to_timeline.py \
    --docker_tsv_output_path /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/2_change_t2space/unsummarized_${cancer}_dev_output.tsv \
    --cancer_type ${cancer} \
    --output_dir /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/2_change_t2space
    echo "Finish Running Command to Summarize ${cancer} File ..."
    date 

    echo "Running Command to Clean ${cancer} File ..."
    python /users/the/NER_MTB/my/change_n2space/run_after.py \
    --summarized_timeline_file /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/2_change_t2space/${cancer}_dev_system_timelines.json \
    --all_ids_file "/users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_dev_patient_ids.txt" \
    --cancer ${cancer}
    echo "Finish Running Command to Clean ${cancer} File ..."
    date 

    echo "Running Command to eval ${cancer} File ..."
    echo "!!!strict!!!..."
    python /users/the/NER_MTB/timelines/docker_output_to_timeline/eval_timeline.py \
    --gold_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/Gold_Timelines_allPatients/${cancer}_dev_all_patients_gold_timelines.json \
    --pred_path /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/2_change_t2space/cleaned_${cancer}_dev.json \
    --all_id_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_dev_patient_ids.txt \
    --strict

    echo "!!!relax day!!!..."
    python /users/the/NER_MTB/timelines/docker_output_to_timeline/eval_timeline.py \
    --gold_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/Gold_Timelines_allPatients/${cancer}_dev_all_patients_gold_timelines.json \
    --pred_path /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/2_change_t2space/cleaned_${cancer}_dev.json \
    --all_id_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_dev_patient_ids.txt \
    --relaxed_to day

    echo "!!!relax month!!!..."
    python /users/the/NER_MTB/timelines/docker_output_to_timeline/eval_timeline.py \
    --gold_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/Gold_Timelines_allPatients/${cancer}_dev_all_patients_gold_timelines.json \
    --pred_path /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/2_change_t2space/cleaned_${cancer}_dev.json \
    --all_id_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_dev_patient_ids.txt \
    --relaxed_to month

    echo "!!!relax year!!!..."
    python /users/the/NER_MTB/timelines/docker_output_to_timeline/eval_timeline.py \
    --gold_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/Gold_Timelines_allPatients/${cancer}_dev_all_patients_gold_timelines.json \
    --pred_path /users/the/NER_MTB/timelines/docker_output_to_timeline/summarized_output/2_change_t2space/cleaned_${cancer}_dev.json \
    --all_id_path /users/the/NER_MTB/chemoTimelines2024_train_dev_labeled/subtask1/All_Patient_IDs/${cancer}_dev_patient_ids.txt \
    --relaxed_to year
done
date
mybroker/bin/artemis stop


