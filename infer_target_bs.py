import argparse
import json
import os
import sys
from datetime import datetime
from target_MLLM import TargetLLM
from target_MLLM_local import TargetLLMLocal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="推理脚本：调用target_model生成响应（仅支持JSONL输入）")
    
    # 模型参数
    parser.add_argument("--target-model", type=str, default="gpt-4.1-nano-2025-04-14", help="目标模型名称")
    parser.add_argument("--target-max-n-tokens", type=int, default=1000, help="最大生成token数")
    parser.add_argument("--num-samples", type=int, default=1, help="每个prompt生成的样本数")
    parser.add_argument("--temperature", type=float, default=0.0, help="生成温度")
    
    # 数据参数
    parser.add_argument("--start-idx", type=int, default=0, help="起始索引")
    parser.add_argument("--end-idx", type=int, default=-1, help="结束索引")
    parser.add_argument("--jsonl-file", type=str, default="/path/to/workspace/models/FigStep/safebench_400.jsonl", help="输入的jsonl文件路径")
    
    # 本地模型参数
    parser.add_argument("--use-api", action="store_true", default=True,
                       help="使用API推理。如果为False，使用本地模型")
    parser.add_argument("--local-model-path", type=str, default="",
                       help="本地模型路径（当use-api为False时使用）")
    parser.add_argument("--device", type=str, default="cuda",
                       choices=["cuda", "cpu"],
                       help="本地模型推理设备")
    
    # 输出参数
    parser.add_argument("--output-dir", type=str, default="/path/to/workspace/models/mllm_attack/Baseline/safebench_results/FigStep",
                       help="推理结果保存目录")
    
    args = parser.parse_args()
    
    print(f"[Mode] 目标模型: {args.target_model}")
    print(f"[Mode] 样本数: {args.num_samples}")
    
    # 检查本地模型参数
    if not args.use_api and not args.local_model_path:
        raise ValueError("--local-model-path 必须在 --use-api 为 False 时指定")
    
    # 从jsonl文件加载数据
    print(f"[Data] 从jsonl文件加载数据: {args.jsonl_file}")
    datas = []
    with open(args.jsonl_file, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if line.strip():
                data_item = json.loads(line.strip())
                # 确保每个数据项都有唯一标识（强制使用全局行号索引，避免原始数据中idx重复导致断点续传失效）
                # if 'idx' not in data_item:
                data_item['idx'] = args.start_idx + idx
                datas.append(data_item)
    
    if args.end_idx == -1:
        args.end_idx = len(datas)
    datas = datas[args.start_idx: args.end_idx]
    print(f"[Data] 加载了 {len(datas)} 个样本")
    
    # 处理模型名称 (用于文件名) - 提前到这里
    if args.target_model == "meta-llama/Meta-Llama-3.1-70B-Instruct":
        target_model = "llama"
    elif args.target_model == "deepseek-ai/DeepSeek-V3":
        target_model = "deepseek-v3"
    elif args.target_model == "Qwen/Qwen3-VL-30B-A3B-Instruct":
        target_model = "Qwen3-VL-30B-A3B-Instruct"
    else:
        target_model = args.target_model
    
    # 确定输出文件路径（提前确定以支持断点续传）
    input_dir = os.path.dirname(args.jsonl_file)
    input_filename = os.path.basename(args.jsonl_file)
    
    # if 'prompts' in input_dir:
    #     output_dir = input_dir.replace('prompts', 'results')
    # else:
    #     output_dir = args.output_dir
        
    os.makedirs(args.output_dir, exist_ok=True)
    
    model_name_safe = target_model.replace('/', '_')

    output_basename = input_filename.replace(".jsonl", f"_{model_name_safe}_inference.jsonl")
    output_filename = os.path.join(args.output_dir, output_basename)
    # output_filename = os.path.join(args.output_dir, f"{input_filename}_{model_name_safe}_inference.jsonl")
    
    # 断点续传：检查已完成的样本
    completed_indices = set()
    if os.path.exists(output_filename):
        print(f"[Resume] 检测到已存在的输出文件，加载已完成的样本...")
        with open(output_filename, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    completed_item = json.loads(line.strip())
                    # 使用idx字段作为唯一标识
                    if 'idx' in completed_item:
                        completed_indices.add(completed_item['idx'])
        print(f"[Resume] 已完成 {len(completed_indices)} 个样本，将跳过")
    
    # 过滤掉已完成的样本
    original_count = len(datas)
    datas = [d for d in datas if d.get('idx', -1) not in completed_indices]
    print(f"[Resume] 过滤后剩余 {len(datas)} 个待处理样本（总共 {original_count} 个）")
    
    # 初始化目标模型
    if args.use_api:
        targetLLM = TargetLLM(
            args.target_model,
            max_tokens=args.target_max_n_tokens,
            temperature=args.temperature,
        )
    else:
        targetLLM = TargetLLMLocal(
            model_path=args.local_model_path,
            max_tokens=args.target_max_n_tokens,
            temperature=args.temperature,
            device=args.device,
        )
    
    # 执行推理 - 实时写入模式
    print(f"[输出] 结果将实时写入到: {output_filename}")
    processed_count = 0
    
    # 使用追加模式打开文件
    with open(output_filename, 'a', encoding='utf-8') as f_out:
        for idx, data in enumerate(datas):
            # 从jsonl格式读取：适配新格式
            # image -> 图片路径, instruction -> plain_attack, text -> encrypted_text
            image_path = data.get("images", "")
            encrypted_text = data.get("text", "")
            plain_attack = data.get("plain_attack", "")
            prompt_text = encrypted_text  # 使用encrypted_text作为实际的提示文本
            data_idx = data.get("idx", idx)
            
            if not image_path or not prompt_text:
                print(f"[错误] 样本 {data_idx} 缺少必要的字段: image={image_path}, text={prompt_text}")
                continue
            
            # 验证图片路径是否存在
            if not os.path.exists(image_path):
                print(f"[警告] 图片路径不存在: {image_path}")
            
            target_response_list = []
            
            try:
                for j in range(args.num_samples):
                    print(f"\n{'='*60}")
                    print(f"[样本 {j+1}/{args.num_samples}] 处理索引 {data_idx} ({idx+1}/{len(datas)})")
                    print(f"{'='*60}")
                    print(f"[图像路径]: {image_path}")
                    print(f"[文本提示]:\n{prompt_text[:200]}...")
                    
                    # 调用目标模型
                    target_response = targetLLM.generate(prompt_text, image_path)
                    print(f"\n[目标响应]:\n{target_response[:200]}...")

                    if target_response == "All retry attempts failed.":
                        target_response = "[Content filtered by API safety policy]"
                    
                    # 检查空响应
                    if not target_response or target_response.strip() == "":
                        print(f"\n[警告] 收到空响应")
                        target_response = "[Model returned empty response]"
                    
                    target_response_list.append(target_response)
                
                # 构造结果项（保持与step2一致的结构，复制原数据）
                result_item = data.copy()
                
                # 添加推理结果
                if args.num_samples == 1:
                    result_item['response'] = target_response_list[0]
                else:
                    result_item['response'] = target_response_list
                    
                # 保留额外的推理信息（可选，为了兼容性）
                result_item["qA_pairs"] = [{
                    "Q": encrypted_text if encrypted_text else prompt_text,
                    "A": target_response_list
                }]
                
                # 立即写入结果
                f_out.write(json.dumps(result_item, ensure_ascii=False) + '\n')
                f_out.flush()  # 强制刷新缓冲区，确保写入磁盘
                
                processed_count += 1
                
                print(f"\n{'='*60}")
                print(f"[摘要] 索引: {data_idx}, 生成了 {len(target_response_list)} 个响应")
                print(f"[原始攻击]: {plain_attack[:100] if plain_attack else 'N/A'}...")
                print(f"[进度] 已处理: {processed_count}/{len(datas)}")
                print(f"{'='*60}\n")
                
            except Exception as e:
                print(f"\n[错误] 处理样本 {data_idx} 时出错: {e}")
                print(f"[提示] 可以重新运行脚本从此处继续（断点续传）")
                # 继续处理下一个样本而不是中断整个程序
                continue
    
    print(f"\n[完成] 共处理 {processed_count} 个样本")
    print(f"[结果] 推理结果已保存到: {output_filename}")
