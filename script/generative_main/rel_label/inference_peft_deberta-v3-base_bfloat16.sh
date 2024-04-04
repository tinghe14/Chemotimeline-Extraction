#!/bin/bash
#SBATCH --job-name=inference_finetune_rel
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --gres=gpu:1
#SBATCH -o /users/the/NER_MTB/timeset/my_code_result/log/infer_finetune_rel_dev_o.log
#SBATCH -e /users/the/NER_MTB/timeset/my_code_result/log/infer_finetune_rel_dev_e.log 

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

export cancer=breast
export mode=dev

export dirpath_output=/users/the/NER_MTB/timeset/my_code_result/model/rel_label_task/tddiscourse/inference/$cancer/$mode
export dirpath_output_score=/users/the/NER_MTB/timeset/my_code_result/model/output_score/benchmark/inference
export dirpath_log=/users/the/NER_MTB/timeset/my_code_result/log
export filepath_test=/users/the/NER_MTB/timeset/my_code_result/input_data/rel_label_task/inference/$cancer/$mode/test.json

export dataset_name=tddiscourse
export inference_type=peft
export seeds=( 7 )

export batch_size=2
export model_id=microsoft/deberta-v3-base
export precision_type=bfloat16
export num_gpu=1

export max_new_tokens=64
export num_demonstration=0
export temperature=0

export dirpath_model=None
export peft_model_path=/users/the/NER_MTB/timeset/my_code_result/model/rel_label_task/tddiscourse/deberta-v3-base_bfloat16_peft_sequence_classification/seed7_bs2_lr1e-05_dim16_alpha16_drop0.1

for seed in "${seeds[@]}"; do
    python -u /users/the/NER_MTB/timeset/src/inference_classification_vllm.py \
        --batch_size $batch_size \
        --dataset_name $dataset_name \
        --dirpath_log $dirpath_log \
        --dirpath_model $dirpath_model \
        --dirpath_output $dirpath_output \
        --dirpath_output_score $dirpath_output_score \
        --filepath_test $filepath_test \
        --inference_type $inference_type \
        --model_id $model_id \
        --num_gpu $num_gpu \
        --precision_type $precision_type \
        --peft_model_path $peft_model_path \
        --max_new_tokens $max_new_tokens \
        --num_demonstration $num_demonstration \
        --temperature $temperature \
        --seed "$seed"
done
