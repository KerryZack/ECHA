#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全测试脚本：对模型响应进行安全评分
使用 judge_templete.py 中定义的模板进行评判
"""

import json
import os
from tqdm import tqdm
import argparse
from openai import OpenAI

# 从 judge_templete.py 导入必要的函数和模板
from judge_templete import judge_template, extract_content

# 默认配置 - 请设置环境变量
import os
API_KEY = os.getenv("API_KEY", "your-api-key-here")
BASE_URL_GPT = os.getenv("BASE_URL_GPT", "https://api.openai.com/v1")


def format_judge_prompt(instruction, response):
    """
    格式化评判 prompt
    
    Args:
        instruction: 用户指令
        response: 模型响应
    
    Returns:
        格式化后的 prompt
    """
    # 使用模板格式化
    prompt = judge_template % (instruction, response)
    return prompt


def judge_response_with_gpt(instruction, response, model_name="gpt-4", api_key=None, base_url=None):
    """
    使用 GPT 模型评判响应的安全性
    
    Args:
        instruction: 用户指令
        response: 模型响应
        model_name: GPT 模型名称
        api_key: OpenAI API key
        base_url: OpenAI API base URL
    
    Returns:
        dict: {"reason": str, "score": int}
    """
    # 使用提供的 API key 或默认值
    if api_key is None:
        api_key = API_KEY
    if base_url is None:
        base_url = BASE_URL_GPT
    
    # 初始化 OpenAI 客户端
    client = OpenAI(base_url=base_url, api_key=api_key)
    
    prompt = format_judge_prompt(instruction, response)
    
    try:
        response_obj = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1000
        )
        
        result_text = response_obj.choices[0].message.content.strip()
        
        # 尝试解析 JSON 格式的结果
        try:
            result = json.loads(result_text)
            reason = result.get("reason", "")
            score = result.get("score", None)
            
            # 如果 score 是字符串，尝试转换为整数
            if isinstance(score, str):
                score = int(score)
        except json.JSONDecodeError:
            # 如果无法解析 JSON，使用 extract_content 函数提取
            reason = extract_content("#thereason:", result_text)
            score = extract_content("#thescore:", result_text)
            
            if reason is None:
                reason = result_text
            if score is None:
                score = -1
        
        return {
            "reason": reason,
            "score": score
        }
        
    except Exception as e:
        print(f"Error during API call: {e}")
        return {
            "reason": f"Error: {str(e)}",
            "score": -1
        }


def process_jsonl_file(input_file, output_file, model_name="gpt-4", api_key=None, base_url=None, skip_existing=True):
    """
    处理 JSONL 文件，对每一行进行安全评判
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        model_name: GPT 模型名称
        api_key: OpenAI API key
        base_url: OpenAI API base URL
        skip_existing: 是否跳过已存在的结果
    """
    # 读取已有结果（如果存在）
    processed_items = {}
    if skip_existing and os.path.exists(output_file):
        print(f"Loading existing results from {output_file}...")
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    # 使用 instruction 作为 key
                    if 'instruction' in item and 'score' in item:
                        processed_items[item['instruction']] = item
        print(f"Found {len(processed_items)} existing results")
    
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    print(f"Processing {len(lines)} items from {input_file}...")
    
    # 处理每一行
    results = []
    skipped = 0
    
    for line in tqdm(lines, desc="Judging responses"):
        item = json.loads(line)
        
        instruction = item.get('instruction', '')
        response = item.get('response', '')
        
        # 检查是否已经处理过
        if skip_existing and instruction in processed_items:
            results.append(processed_items[instruction])
            skipped += 1
            continue
        
        # 进行评判
        judge_result = judge_response_with_gpt(
            instruction=instruction,
            response=response,
            model_name=model_name,
            api_key=api_key,
            base_url=base_url
        )
        
        # 合并结果
        result_item = item.copy()
        result_item['reason'] = judge_result['reason']
        result_item['score'] = judge_result['score']
        
        results.append(result_item)
        
        # 实时保存（避免中断导致数据丢失）
        with open(output_file, 'w', encoding='utf-8') as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    if skipped > 0:
        print(f"Skipped {skipped} already processed items")
    
    # 保存最终结果
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    print(f"Results saved to {output_file}")
    
    # 统计结果
    scores = [r['score'] for r in results if r['score'] != -1]
    if scores:
        print(f"\n=== Statistics ===")
        print(f"Total items: {len(results)}")
        print(f"Valid scores: {len(scores)}")
        print(f"Average score: {sum(scores) / len(scores):.2f}")
        print(f"Score distribution:")
        for i in range(1, 6):
            count = scores.count(i)
            percentage = count / len(scores) * 100
            print(f"  Score {i}: {count} ({percentage:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description='对模型响应进行安全评判')
    parser.add_argument('--input', '-i', type=str, required=True,
                        help='输入 JSONL 文件路径')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出 JSONL 文件路径（默认为输入文件名_judged.jsonl）')
    parser.add_argument('--model', '-m', type=str, default='gpt-3.5-turbo',
                        help='GPT 模型名称（默认: gpt-4）')
    parser.add_argument('--api-key', '-k', type=str, default=None,
                        help='OpenAI API key（默认使用脚本中的默认值）')
    parser.add_argument('--base-url', '-b', type=str, default=None,
                        help='OpenAI API base URL（默认使用脚本中的默认值）')
    parser.add_argument('--no-skip', action='store_true',
                        help='不跳过已存在的结果，重新评判所有项目')
    
    args = parser.parse_args()
    
    # 生成输出文件名
    if args.output is None:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}_judged.jsonl"
    
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    print(f"Model: {args.model}")
    print(f"API Key: {args.api_key if args.api_key else API_KEY[:20]}...")
    print(f"Base URL: {args.base_url if args.base_url else BASE_URL_GPT}")
    print(f"Skip existing: {not args.no_skip}")
    print()
    
    # 处理文件
    process_jsonl_file(
        input_file=args.input,
        output_file=args.output,
        model_name=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        skip_existing=not args.no_skip
    )


if __name__ == "__main__":
    # 示例用法
    # python safety_judge.py -i /path/to/input.jsonl -o /path/to/output.jsonl -m gpt-4
    
    # 或者直接运行默认配置
    input_file = "/path/to/workspace/models/mllm_attack/Baseline/hades_results/SI/hades_SI_attack_data_shuffled_llava_inference.jsonl"
    output_file = "/path/to/workspace/models/mllm_attack/Baseline/hades_results/SI/hades_SI_attack_data_shuffled_llava_inference_judged.jsonl"
    
    if os.path.exists(input_file):
        process_jsonl_file(
            input_file=input_file,
            output_file=output_file,
            model_name="gpt-3.5-turbo",
            api_key=API_KEY,
            base_url=BASE_URL_GPT,
            skip_existing=True
        )
    else:
        print("请使用命令行参数运行脚本，或修改脚本中的默认路径")
        main()

