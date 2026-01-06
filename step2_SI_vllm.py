#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SI方法推理脚本：使用vllm进行批量推理
从jsonl文件读取数据（格式：image, instruction），使用vllm进行批量推理，保存推理结果
"""

import argparse
import json
import os
import sys
from tqdm import tqdm
from utils_local import api_call_mllm_vllm_batch
import multiprocessing

# 设置 multiprocessing 启动方式
os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'
# os.environ['VLLM_ATTENTION_BACKEND'] = 'FLASHINFER' #used for llava

def vllm_batch_inference_si(args, jsonl_filename):
    """
    使用vllm进行批量推理 (适配SI数据格式)
    
    Args:
        args: 命令行参数
        jsonl_filename: jsonl文件路径
    
    Returns:
        推理结果文件路径
    """
    print(f"\n{'='*60}")
    print(f"[SI推理] 开始vllm批量推理...")
    print(f"{'='*60}\n")
    
    if not args.local_model_path:
        raise ValueError("--local-model-path must be specified for vllm inference")
    
    # 读取jsonl文件
    print(f"[SI推理] 读取jsonl文件: {jsonl_filename}")
    jsonl_data = []
    if not os.path.exists(jsonl_filename):
         raise FileNotFoundError(f"输入文件不存在: {jsonl_filename}")

    with open(jsonl_filename, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                jsonl_data.append(json.loads(line.strip()))
    
    print(f"[SI推理] 共 {len(jsonl_data)} 条数据需要推理")
    
    # 准备批量推理数据 (适配SI格式: instruction, image)
    prompts_and_images = []
    for item_idx, item in enumerate(jsonl_data):
        #text是构造之后的提示词
        #hades: 图片中的行为 image pointer
        #SI shuffle之后的
        prompt_text = item['text']
        image_path = item.get('image', item.get('images', ''))
        
        # 验证：输出第一个数据的字段
        if item_idx == 0:
            print(f"\n{'='*60}")
            print(f"[验证] 第一条数据的字段内容:")
            print(f"{'='*60}")
            print(f"prompt_text (text字段): {prompt_text[:200]}..." if len(prompt_text) > 200 else f"prompt_text (text字段): {prompt_text}")
            print(f"image_path (image字段): {image_path}")
            print(f"{'='*60}\n")
        
        if not prompt_text:
            print(f"⚠️ Warning: 某条数据缺少 instruction/text 字段")
        if not image_path:
            print(f"⚠️ Warning: 某条数据缺少 image/images 字段")
            
        prompts_and_images.append((prompt_text, image_path))
    
    # 批量推理
    print(f"[SI推理] 开始批量推理（批次大小: {args.batch_size}）...")
    all_responses = []
    
    # 检测模型类型，决定是否使用message格式
    model_path_lower = args.local_model_path.lower()
    use_message_format = 'qwen' in model_path_lower and 'vl' in model_path_lower
    if use_message_format:
        print(f"[SI推理] 检测到Qwen-VL模型，将使用message协议格式")
    
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
            import traceback
            traceback.print_exc()
            # 填充空响应
            all_responses.extend(["[Error]"] * len(batch_data))
    
    # 保存推理结果
    input_filename = os.path.basename(jsonl_filename)
    
    # 从输入路径提取上级目录名（如 hades, SI, jbb 等）
    input_dir = os.path.dirname(jsonl_filename)
    parent_dir_name = os.path.basename(input_dir)
    
    # 构建输出目录：固定保存到 Baseline/results/{上级目录名}/
    # 假设项目根目录为 /path/to/workspace/models/mllm_attack
    base_output_dir = "/path/to/workspace/models/mllm_attack/Baseline/hades_results"
    output_dir = os.path.join(base_output_dir, parent_dir_name)
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出文件名添加模型后缀
    model_suffix = f"_{args.model_name}" if args.model_name else ""
    inference_result_filename = os.path.join(output_dir, input_filename.replace('.jsonl', f'{model_suffix}_inference.jsonl'))
    
    print(f"\n[SI推理] 输入文件目录: {parent_dir_name}")
    print(f"[SI推理] 输出目录: {output_dir}")
    print(f"[SI推理] 保存推理结果: {inference_result_filename}")
    
    with open(inference_result_filename, 'w', encoding='utf-8') as f:
        for item, response in zip(jsonl_data, all_responses):
            result_item = item.copy()
            result_item['response'] = response
            # 确保原来的字段都在，仅仅增加了 response
            f.write(json.dumps(result_item, ensure_ascii=False) + '\n')
    
    print(f"[SI推理] ✓ 完成！推理了 {len(all_responses)} 条数据")
    print(f"[SI推理] 推理结果文件: {inference_result_filename}")
    print(f"{'='*60}\n")
    
    return inference_result_filename


def main():
    parser = argparse.ArgumentParser(description="SI方法推理脚本")
    
    # 输入文件参数
    parser.add_argument("--jsonl-file", type=str, 
                        default='/path/to/workspace/models/mllm_attack/prompts/hades/hades_abstract_step5.jsonl',
                       help="输入的jsonl文件路径")
    
    # 模型参数
    parser.add_argument("--local-model-path", type=str, 
                        default='/path/to/workspace/model_zoo/Qwen3-VL-8B-Instruct',
                       help="本地模型路径")
    parser.add_argument("--model-name", type=str, default="qwen3vl",
                       help="模型名称简写，将用于输出文件名中")
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
    
    args = parser.parse_args()

     # 根据模型路径决定是否设置 VLLM_ATTENTION_BACKEND
    if 'llava' in args.local_model_path.lower():
        os.environ['VLLM_ATTENTION_BACKEND'] = 'FLASHINFER'
        print(f"[配置] 检测到 LLaVA 模型，设置 VLLM_ATTENTION_BACKEND=FLASHINFER")
    else:
        print(f"[配置] 非 LLaVA 模型，使用默认 attention backend")
    
    # 执行批量推理
    vllm_batch_inference_si(args, args.jsonl_file)


if __name__ == "__main__":
    main()
