#!/bin/bash
#SBATCH --job-name=run_nli_ft_deberta_tf_rel
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=20
#SBATCH -o /users/the/NER_MTB/timeset/my_code_result/log/train_tf_rel_task_deberta_o.log
#SBATCH -e /users/the/NER_MTB/timeset/my_code_result/log/train_tf_rel_task_deberta_e.log 
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

source ativate timeset


export dirpath_output=/users/the/NER_MTB/timeset/my_code_result/model/tf_rel_task

export dirpath_log=/users/the/NER_MTB/timeset/my_code_result/log
export filepath_data_train=/users/the/NER_MTB/timeset/my_code_result/input_data/tf_rel_task/temporal-nli/train.json
export filepath_data_dev=/users/the/NER_MTB/timeset/my_code_result/input_data/tf_rel_task/temporal-nli/dev.json

export dataset_name=temporal-nli

export batch_size=2
export model_id=microsoft/deberta-v3-base
export num_epoch=5
export precision_type=bfloat16
export finetune_type=peft
export peft_type=lora
export lora_dimensions=( 16 )
export lora_alphas=( 16 )
export lora_dropout=0.1

learning_rates=( 0.001 0.01 )

for lora_alpha in "${lora_alphas[@]}"; do
    for lora_dimension in "${lora_dimensions[@]}"; do
        for learning_rate in "${learning_rates[@]}"; do

            python -u /users/the/NER_MTB/timeset/src/finetune_classification.py \
                --batch_size $batch_size \
                --dataset_name $dataset_name \
                --dirpath_log $dirpath_log \
                --dirpath_output "$dirpath_output" \
                --filepath_data_train $filepath_data_train \
                --filepath_data_dev $filepath_data_dev \
                --finetune_type $finetune_type \
                --learning_rate "$learning_rate" \
                --lora_alpha "$lora_alpha" \
                --lora_dimension "$lora_dimension" \
                --lora_dropout $lora_dropout \
                --model_id $model_id \
                --num_epoch $num_epoch \
                --peft_type $peft_type \
                --precision_type $precision_type \
                --save_model_weight \
                --warmup
        done
    done
done
