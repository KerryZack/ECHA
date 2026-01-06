#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主脚本：统一调用三个步骤
已解耦为三个独立脚本：
- step1_generate_images.py: 生成图片和jsonl
- step2_vllm_inference.py: vllm批量推理
- step3_judge_scoring.py: judge评分

此脚本作为统一入口，按顺序调用三个步骤
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime

from utils_logger import Logger


def run_step1(args):
    """运行步骤1：生成图片和jsonl"""
    cmd = [
        sys.executable, "step1_generate_images.py",
        "--input-file", args.input_file,
        "--dataset", args.dataset,
        "--start-idx", str(args.start_idx),
        "--end-idx", str(args.end_idx),
        "--target-model", args.target_model,
        "--rewrite-model", args.rewrite_model,
        "--prompt-type", args.prompt_type,
        "--encryption-method", args.encryption_method,
    ]
    
    if args.images_directory:
        cmd.extend(["--images-directory", args.images_directory])
    if args.use_joint_reasoning:
        cmd.append("--use-joint-reasoning")
    if args.gen_new_file:
        cmd.append("--gen-new-file")
    if args.query_file:
        cmd.extend(["--query-file", args.query_file])
    
    print(f"\n{'='*60}")
    print(f"[主脚本] 执行步骤1：生成图片和jsonl")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"步骤1执行失败，退出码: {result.returncode}")
    
    # 返回生成的jsonl文件路径
    jsonl_filename = (
        f"./results/{args.dataset}/vllm_input_"
        f"{args.target_model.replace('/', '_')}_"
        f"{args.start_idx}_{args.end_idx}.jsonl"
    )
    return jsonl_filename


def run_step2(args, jsonl_filename):
    """运行步骤2：vllm批量推理"""
    cmd = [
        sys.executable, "step2_vllm_inference.py",
        "--jsonl-file", jsonl_filename,
        "--local-model-path", args.local_model_path,
        "--device", args.device,
        "--batch-size", str(args.batch_size),
        "--max-tokens", str(args.target_max_n_tokens),
        "--temperature", str(args.temperature),
    ]
    
    print(f"\n{'='*60}")
    print(f"[主脚本] 执行步骤2：vllm批量推理")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"步骤2执行失败，退出码: {result.returncode}")
    
    # 返回推理结果文件路径
    inference_filename = jsonl_filename.replace('.jsonl', '_inference.jsonl')
    return inference_filename


def run_step3(args, inference_filename):
    """运行步骤3：judge评分"""
    output_file = (
        f"./results/{args.dataset}/attack_"
        f"{args.target_model.replace('/', '_')}_rewrite_{args.rewrite_model}_"
        f"temp_{args.temperature}_results_{args.start_idx}_{args.end_idx}.json"
    )
    
    cmd = [
        sys.executable, "step3_judge_scoring.py",
        "--inference-file", inference_filename,
        "--output-file", output_file,
        "--judge-model", args.judge_model,
    ]
    
    print(f"\n{'='*60}")
    print(f"[主脚本] 执行步骤3：judge评分")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"步骤3执行失败，退出码: {result.returncode}")
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="主脚本：统一调用三个步骤（生成图片、vllm推理、judge评分）"
    )
    
    # 数据相关参数
    parser.add_argument("--input-file", type=str, required=True,
                       help="输入JSON文件路径")
    parser.add_argument("--dataset", type=str, default="hades",
                       choices=["jbb", "advbench", "hades"],
                       help="数据集名称")
    parser.add_argument("--start-idx", type=int, default=0,
                       help="起始索引")
    parser.add_argument("--end-idx", type=int, default=-1,
                       help="结束索引（-1表示到末尾）")
    
    # 模型相关参数
    parser.add_argument("--target-model", type=str, default="gpt-4.1-nano-2025-04-14",
                       help="目标模型名称（用于数据准备）")
    parser.add_argument("--judge-model", type=str, default="gpt-4.1-nano-2025-04-14",
                       help="Judge模型名称")
    parser.add_argument("--rewrite-model", type=str, default="gpt-4.1-nano-2025-04-14",
                       help="重写模型名称")
    parser.add_argument("--prompt-type", type=str, default="visual_symbol",
                       help="提示词类型")
    
    # vllm推理参数
    parser.add_argument("--local-model-path", type=str, required=True,
                       help="本地模型路径（用于vllm推理）")
    parser.add_argument("--device", type=str, default="cuda",
                       choices=["cuda", "cpu"],
                       help="推理设备")
    parser.add_argument("--batch-size", type=int, default=8,
                       help="批量推理的批次大小")
    parser.add_argument("--target-max-n-tokens", type=int, default=1000,
                       help="最大生成token数")
    parser.add_argument("--temperature", type=float, default=0.0,
                       help="生成温度")
    
    # 加密和场景相关参数
    parser.add_argument("--encryption-method", type=str, default="jigsaw",
                       choices=["none", "visual_symbol", "jigsaw", "hybrid"],
                       help="视觉加密方法")
    parser.add_argument("--use-joint-reasoning", action="store_true", default=True,
                       help="启用跨模态联合推理")
    
    # 数据生成参数
    parser.add_argument("--gen-new-file", action="store_true", default=True,
                       help="是否生成新的提示文件")
    parser.add_argument("--query-file", type=str, default="./data/safebench.csv",
                       help="查询文件路径（用于生成新文件）")
    
    # 输出路径参数
    parser.add_argument("--images-directory", type=str, default=None,
                       help="图片保存目录（默认: ./images/{dataset}）")
    
    # 步骤选择参数
    parser.add_argument("--step", type=str, default="all",
                       choices=["1", "2", "3", "all"],
                       help="执行哪个步骤: 1=生成图片和jsonl, 2=vllm推理, 3=judge评分, all=执行所有步骤")
    parser.add_argument("--jsonl-file", type=str, default="",
                       help="jsonl文件路径（步骤2需要，如果只执行步骤2）")
    parser.add_argument("--inference-file", type=str, default="",
                       help="推理结果文件路径（步骤3需要，如果只执行步骤3）")
    
    # 日志参数
    parser.add_argument("--log-dir", type=str, default="./logs",
                       help="日志文件目录")
    
    args = parser.parse_args()
    
    # 设置日志
    os.makedirs(args.log_dir, exist_ok=True)
    cur_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_filename = os.path.join(
        args.log_dir,
        f"main_vllm_{args.dataset}_{cur_time}.log"
    )
    
    # 重定向输出到日志
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = Logger(log_filename)
    sys.stderr = Logger(log_filename.replace('.log', '_error.log'))
    
    try:
        print(f"[LOG] 开始时间: {cur_time}")
        print(f"[LOG] 日志文件: {log_filename}")
        print(f"[LOG] 执行步骤: {args.step}")
        
        jsonl_filename = None
        inference_filename = None
    
        # 执行步骤1
        if args.step in ["1", "all"]:
            jsonl_filename = run_step1(args)
            print(f"[主脚本] ✓ 步骤1完成，jsonl文件: {jsonl_filename}")
    
        # 执行步骤2
        if args.step in ["2", "all"]:
            if args.step == "2":
                if not args.jsonl_file:
                    raise ValueError("--jsonl-file must be specified for step 2")
                jsonl_filename = args.jsonl_file
            inference_filename = run_step2(args, jsonl_filename)
            print(f"[主脚本] ✓ 步骤2完成，推理结果文件: {inference_filename}")
        
        # 执行步骤3
        if args.step in ["3", "all"]:
            if args.step == "3":
                if not args.inference_file:
                    raise ValueError("--inference-file must be specified for step 3")
                inference_filename = args.inference_file
            output_file = run_step3(args, inference_filename)
            print(f"[主脚本] ✓ 步骤3完成，最终结果文件: {output_file}")
        
        print(f"\n[LOG] 完成时间: {datetime.now().strftime('%Y%m%d-%H%M%S')}")
        print(f"[LOG] 所有步骤执行完成！")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        raise
    finally:
        # 恢复原始输出
        if hasattr(sys.stdout, 'close'):
            sys.stdout.close()
        if hasattr(sys.stderr, 'close'):
            sys.stderr.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr

    
if __name__ == "__main__":
    main()
