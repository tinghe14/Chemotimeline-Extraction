#!/bin/bash
#SBATCH --job-name=run_tdd_ft_deberta_rel_class
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=20
#SBATCH -o /users/the/NER_MTB/timeset/my_code_result/log/train_rel_label_task_many_o.log
#SBATCH -e /users/the/NER_MTB/timeset/my_code_result/log/train_rel_label_task_many_e.log 
#SBATCH --mail-type=begin
#SBATCH --mail-type=end
#SBATCH --mail-user=the14@jh.edu

echo "**** Job starts ****"
date

echo "**** JHPCE info ****"
echo "User: ${USER}"
echo "Job id: ${JOB_ID}"
echo "Job name: ${JOB_NAME}"
echo "Hostname: ${HOSTNAME}"
echo "Task id: ${SGE_TASK_ID}"
echo "Conda Env: ${CONDA_DEFAULT_ENV}"
echo "Conda Env: ${CONDA_PREFIX}"

echo "Running GPU job on $SLURM_JOB_NODELIST"
echo "Available GPUs: $CUDA_VISIBLE_DEVICES"

source activate timeset

export dirpath_output=/users/the/NER_MTB/timeset/my_code_result/model/rel_label_task # TODO: dir for output files
export dirpath_log=/users/the/NER_MTB/timeset/my_code_result/log
export filepath_data_train=/users/the/NER_MTB/timeset/my_code_result/input_data/rel_label_task/tddiscourse/train.json
export filepath_data_dev=/users/the/NER_MTB/timeset/my_code_result/input_data/rel_label_task/tddiscourse/dev.json

export dataset_name=tddiscourse

batch_sizes=( 4 )
export model_id=(microsoft/deberta-v3-large michiyasunaga/BioLinkBERT-large sultan/BioM-ALBERT-xxlarge-PMC)
export num_epoch=10
export num_gpu=3
export precision_type=bfloat16
export finetune_type=ft

export learning_rates=( 1e-5 )

for batch_size in "${batch_sizes[@]}"
do
    for learning_rate in "${learning_rates[@]}"
    do
        python -u /users/the/NER_MTB/timeset/src/finetune_classification.py \
            --batch_size "$batch_size" \
            --dataset_name $dataset_name \
            --dirpath_log $dirpath_log \
            --dirpath_output "$dirpath_output" \
            --filepath_data_train $filepath_data_train \
            --filepath_data_dev $filepath_data_dev \
            --finetune_type $finetune_type \
            --learning_rate "$learning_rate" \
            --model_id $model_id \
            --num_epoch $num_epoch \
            --num_gpu $num_gpu \
            --precision_type $precision_type \
            --save_model_weight \
            --warmup
    done
done

date
