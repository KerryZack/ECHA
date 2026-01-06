# step2_vllm_inference_SI.py 的参数
JSONL_FILE="/path/to/workspace/models/mllm_attack/prompts/hades/hades_abstract_step5.jsonl"
LOCAL_MODEL_PATH="/path/to/models/Qwen2.5-VL-7B-Instruct"
MODEL_NAME="qwen25vl"

# test_baseline.py 的参数
INPUT_FILE="/path/to/workspace/models/mllm_attack/Baseline/hades_results/hades/hades_abstract_step5_qwen25vl_inference.jsonl"

# ====================================================================
# 脚本执行部分 - 一般不需要修改
# ====================================================================

/path/to/miniconda3/condabin/conda init 
source ~/.bashrc 
cd /path/to/workspace/models/mllm_attack/


conda activate qwen3vl  # used for qwen llava
# conda activate vllm_env  # used for internvl
python ./step2_SI_vllm.py \
    --jsonl-file "${JSONL_FILE}" \
    --local-model-path "${LOCAL_MODEL_PATH}" \
    --model-name "${MODEL_NAME}"


conda activate vllm_env
python ./test_qwenguard_bl.py \
    --input-file "${INPUT_FILE}"