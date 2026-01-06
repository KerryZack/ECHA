#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤2：使用vllm进行批量推理
从jsonl文件读取数据，使用vllm进行批量推理，保存推理结果
"""

import argparse
import json
import os
import sys
from datetime import datetime
from tqdm import tqdm
from vllm import LLM, SamplingParams
from utils_local import api_call_mllm_vllm_batch
from utils_logger import Logger
import multiprocessing
os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'
os.environ['VLLM_ATTENTION_BACKEND'] = 'FLASHINFER' #used for llava
# export VLLM_ATTENTION_BACKEND=FLASHINFER

def vllm_batch_inference(args, jsonl_filename):
    """
    使用vllm进行批量推理
    
    Args:
        args: 命令行参数
        jsonl_filename: jsonl文件路径
    
    Returns:
        推理结果文件路径
    """
    print(f"\n{'='*60}")
    print(f"[步骤2] 开始vllm批量推理...")
    print(f"{'='*60}\n")
    
    # if not VLLM_AVAILABLE:
    #     raise ImportError("vllm is required for step 2. Install with: pip install vllm")
    
    if not args.local_model_path:
        raise ValueError("--local-model-path must be specified for vllm inference")
    
    # 读取jsonl文件
    print(f"[步骤2] 读取jsonl文件: {jsonl_filename}")
    jsonl_data = []
    with open(jsonl_filename, 'r', encoding='utf-8') as f:
        for line in f:
            jsonl_data.append(json.loads(line.strip()))
    
    print(f"[步骤2] 共 {len(jsonl_data)} 条数据需要推理")
    
    # 准备批量推理数据
    prompts_and_images = []
    for item in jsonl_data:
        prompt_text = item['text']
        image_path = item['images']
        prompts_and_images.append((prompt_text, image_path))
    
    # 批量推理
    print(f"[步骤2] 开始批量推理（批次大小: {args.batch_size}）...")
    all_responses = []
    
    # 检测模型类型，决定是否使用message格式
    model_path_lower = args.local_model_path.lower()
    use_message_format = 'qwen' in model_path_lower and 'vl' in model_path_lower
    if use_message_format:
        print(f"[步骤2] 检测到Qwen-VL模型，将使用message协议格式")
    
    # 按批次处理
    for batch_start in tqdm(range(0, len(prompts_and_images), args.batch_size), 
                           desc="批量推理", unit="批次", ncols=120):
        batch_end = min(batch_start + args.batch_size, len(prompts_and_images))
        batch_data = prompts_and_images[batch_start:batch_end]
        
        try:
            batch_responses = api_call_mllm_vllm_batch(
                model_path=args.local_model_path,
                prompts_and_images=batch_data,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                device=args.device,
                use_message_format=use_message_format
            )
            all_responses.extend(batch_responses)
        except Exception as e:
            print(f"❌ 批次 {batch_start//args.batch_size + 1} 推理失败: {e}")
            # 填充空响应
            all_responses.extend([""] * len(batch_data))
    
    # 保存推理结果到results文件夹
    input_dir = os.path.dirname(jsonl_filename)
    input_filename = os.path.basename(jsonl_filename)
    
    # 将prompts替换为results，保持目录结构
    output_dir = input_dir.replace('prompts', 'results')
    os.makedirs(output_dir, exist_ok=True)
    
    # 在文件名中加入模型名称
    model_suffix = f"_{args.model_name}" if args.model_name else ""
    inference_result_filename = os.path.join(output_dir, input_filename.replace('.jsonl', f'{model_suffix}_inference.jsonl'))
    print(f"\n[步骤2] 保存推理结果: {inference_result_filename}")
    
    with open(inference_result_filename, 'w', encoding='utf-8') as f:
        for item, response in zip(jsonl_data, all_responses):
            result_item = item.copy()
            result_item['response'] = response
            f.write(json.dumps(result_item, ensure_ascii=False) + '\n')
    
    print(f"[步骤2] ✓ 完成！推理了 {len(all_responses)} 条数据")
    print(f"[步骤2] 推理结果文件: {inference_result_filename}")
    print(f"{'='*60}\n")
    
    return inference_result_filename


def main():
    parser = argparse.ArgumentParser(description="步骤2：使用vllm进行批量推理")
    
    # 输入文件参数
    parser.add_argument("--jsonl-file", type=str, 
                        default='/path/to/workspace/models/mllm_attack/prompts/hades/vllm_input_0_750.jsonl',
                       help="输入的jsonl文件路径")
    
    # 模型参数
    parser.add_argument("--local-model-path", type=str, default='/path/to/workspace/model_zoo/InternVL3_5-4B-HF',
                       help="本地模型路径")
    parser.add_argument("--model-name", type=str, default="internvl35",
                       help="模型名称简写，将用于输出文件名中（例如：internvl）")
    parser.add_argument("--device", type=str, default="cuda",
                       choices=["cuda", "cpu"],
                       help="推理设备")
    
    # 推理参数
    parser.add_argument("--batch-size", type=int, default=8,
                       help="批量推理的批次大小")
    parser.add_argument("--max-tokens", type=int, default=1000,
                       help="最大生成token数")
    parser.add_argument("--temperature", type=float, default=0.0,
                       help="生成温度")
    
    # 日志参数
    parser.add_argument("--log-dir", type=str, default="/path/to/workspace/models/mllm_attack/logs",
                       help="日志文件目录")
    
    args = parser.parse_args()
    
    # 设置日志
    os.makedirs(args.log_dir, exist_ok=True)
    cur_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_filename = os.path.join(
        args.log_dir,
        f"step2_inference_{cur_time}.log"
    )
    
    # 重定向输出到日志
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Logger(log_filename)
    sys.stderr = Logger(log_filename.replace('.log', '_error.log'))
    
    try:
        print(f"[LOG] 开始时间: {cur_time}")
        print(f"[LOG] 日志文件: {log_filename}")
        
        # 执行批量推理
        inference_filename = vllm_batch_inference(args, args.jsonl_file)
        
        print(f"\n[LOG] 完成时间: {datetime.now().strftime('%Y%m%d-%H%M%S')}")
        print(f"[LOG] 推理结果文件: {inference_filename}")
        
    finally:
        # 恢复原始输出
        if hasattr(sys.stdout, 'close'):
            sys.stdout.close()
        if hasattr(sys.stderr, 'close'):
            sys.stderr.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr


if __name__ == "__main__":
    # multiprocessing.set_start_method('spawn', force=True)
    main()

