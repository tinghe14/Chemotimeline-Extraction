#!/bin/bash
#SBATCH --job-name=maven_test
#SBATCH --partition=gpu
#SBATCH --nodes=1 # Run all processes on a single node
#SBATCH --gres=gpu:1 #--gres=gpu:tesv100:2 
#SBATCH --time=10:00:00 # Time limit hrs:min:sec
#SBATCH -o /users/the/NER_MTB/my/1_change_n2space/0328_n2space_melanoma_test_task2.log
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

mvn -U clean package

/users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/timelines/mybroker/bin/artemis-service start

date
echo "Running Command ..."  
java -cp instance-generator/target/instance-generator-5.0.0-SNAPSHOT-jar-with-dependencies.jar \
org.apache.ctakes.core.pipeline.PiperFileRunner \
-p org/apache/ctakes/timelines/pipeline/Timelines \
-a  mybroker \
-v /users/the/.conda/envs/timelines \
-i /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/input/change_n2space_task2/input_melanoma_test_task2 \
-o /users/the/NER_MTB/timelines/chemoTimelinesBaselineSystem/output/change_n2space_task2 \
-l org/apache/ctakes/dictionary/lookup/fast/bsv/Unified_Gold_Dev.xml \
--pipPbj yes

date
echo "Finish Running Command..."
mybroker/bin/artemis stop

date
