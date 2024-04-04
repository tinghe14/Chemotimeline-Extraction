#!/bin/bash
#SBATCH --job-name=run_tdd_ft_deberta_rel_class
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
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

export batch_size=2
export model_ids=( "microsoft/deberta-v3-base" ) #"michiyasunaga/BioLinkBERT-large" "sultan/BioM-ALBERT-xxlarge-PMC"
export num_epoch=3
export precision_type=bfloat16
export finetune_type=peft
export peft_type=lora
export lora_dimensions=( 16 )
export lora_alphas=( 16 )
export lora_dropout=0.1

learning_rates=( 1e-5 )


for model_id in "${model_ids[@]}"; do
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
done