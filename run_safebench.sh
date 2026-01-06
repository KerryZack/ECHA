# step2_vllm_inference_SI.py 的参数
JSONL_FILE="/path/to/workspace/models/mllm_attack/prompts/safebench/vllm_input_0_400_universal.jsonl"
LOCAL_MODEL_PATH="/path/to/workspace/model_zoo/InternVL3_5-4B-HF"
MODEL_NAME="internvl"

# test_baseline.py 的参数
INPUT_FILE="/path/to/workspace/models/mllm_attack/results/safebench/vllm_input_0_400_universal_internvl_inference.jsonl"
GROUP_SIZE=50

# ====================================================================
# 脚本执行部分 - 一般不需要修改
# ====================================================================

/path/to/miniconda3/condabin/conda init 
source ~/.bashrc 
cd /path/to/workspace/models/mllm_attack/

# conda activate mllm_env
# python ./step1_generate_images.py

echo "=================================================="
echo "Step 1: 运行 vllm 推理"
echo "=================================================="
echo "JSONL文件: ${JSONL_FILE}"
echo "模型路径: ${LOCAL_MODEL_PATH}"
echo "模型名称: ${MODEL_NAME}"
echo ""

# conda activate qwen3vl_env  # used for qwen llava
conda activate vllm_env  # used for internvl
python ./step2_vllm_inference.py \
    --jsonl-file "${JSONL_FILE}" \
    --local-model-path "${LOCAL_MODEL_PATH}" \
    --model-name "${MODEL_NAME}"

if [ $? -ne 0 ]; then
    echo "❌ step2_vllm_inference.py 执行失败"
    exit 1
fi

echo ""
echo "=================================================="
echo "Step 2: 运行 Qwen Guard 测试"
echo "=================================================="
echo "输入文件: ${INPUT_FILE}"
# 自动生成输出文件名：将 .jsonl 替换为 _qwen3guard.json
OUTPUT_FILE="${INPUT_FILE%.jsonl}_qwen3guard.json"
echo "输出文件: ${OUTPUT_FILE}"
echo ""

conda activate vllm_env
python ./test_vllmres_qwen3guard.py \
    --input-file "${INPUT_FILE}" \
    --output-file "${OUTPUT_FILE}" \
    --group-size "${GROUP_SIZE}"

if [ $? -ne 0 ]; then
    echo "❌ test_baseline.py 执行失败"
    exit 1
fi

echo ""
echo "✅ 所有步骤执行完成！"