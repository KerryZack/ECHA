#!/usr/bin/env python3
"""
重新生成使用了 fallback 的 emoji 序列
用法: python regenerate_fallback_emojis.py --input <json_file> --model <model_name>
"""

import argparse
import json
import os
from datetime import datetime
from visual_encryption import VisualSymbolGenerator, CrossModalJigsawAttack

def regenerate_fallback_samples(input_file, encryption_model, output_file=None, max_retries=3):
    """
    重新生成 fallback 样本的 emoji 序列
    
    Args:
        input_file: 输入的JSON文件路径
        encryption_model: 用于生成emoji的模型名称
        output_file: 输出文件路径（可选，默认覆盖原文件）
        max_retries: 每个样本的最大重试次数
    """
    
    print(f"{'='*70}")
    print(f"Emoji Regeneration Script")
    print(f"{'='*70}")
    print(f"Input file: {input_file}")
    print(f"Encryption model: {encryption_model}")
    print(f"Max retries per sample: {max_retries}")
    print(f"{'='*70}\n")
    
    # 1. 读取JSON文件
    print("[Step 1] Loading JSON file...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} samples\n")
    except FileNotFoundError:
        print(f"❌ Error: File not found: {input_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON file: {e}")
        return
    
    # 2. 初始化加密器
    print("[Step 2] Initializing encryption model...")
    try:
        visual_generator = VisualSymbolGenerator(encryption_llm_model=encryption_model)
        jigsaw_attack = CrossModalJigsawAttack()
        print(f"✅ Model initialized: {encryption_model}\n")
    except Exception as e:
        print(f"❌ Error initializing model: {e}")
        return
    
    # 3. 统计需要重新生成的样本
    print("[Step 3] Analyzing samples...")
    needs_regeneration = []
    already_perfect = []
    
    for idx, sample in enumerate(data):
        fallback_count = sample.get('fallback_count', 0)
        if fallback_count > 0:
            needs_regeneration.append(idx)
        else:
            already_perfect.append(idx)
    
    print(f"📊 Statistics:")
    print(f"   Total samples: {len(data)}")
    print(f"   Need regeneration (fallback_count > 0): {len(needs_regeneration)}")
    print(f"   Already perfect (fallback_count = 0): {len(already_perfect)}")
    print(f"   Regeneration rate: {len(needs_regeneration)/len(data)*100:.1f}%\n")
    
    if len(needs_regeneration) == 0:
        print("✅ All samples are already perfect! No regeneration needed.")
        return
    
    # 4. 重新生成emoji序列
    print(f"[Step 4] Regenerating {len(needs_regeneration)} samples...")
    print(f"{'='*70}\n")
    
    success_count = 0
    improved_count = 0
    still_fallback_count = 0
    
    for count, idx in enumerate(needs_regeneration, 1):
        sample = data[idx]
        plain_attack = sample.get('plain_attack', '')
        old_fallback_count = sample.get('fallback_count', 0)
        old_generation_method = sample.get('generation_method', 'unknown')
        
        print(f"[{count}/{len(needs_regeneration)}] Processing sample #{idx}")
        print(f"   Original: {plain_attack[:60]}...")
        print(f"   Old status: {old_generation_method} (fallback: {old_fallback_count})")
        
        best_result = None
        best_fallback_count = old_fallback_count
        
        # 多次尝试
        for attempt in range(1, max_retries + 1):
            try:
                print(f"   Attempt {attempt}/{max_retries}...", end=' ')
                
                # 重新生成加密结果
                encrypted_result = visual_generator.encrypt_query_with_visual_symbols(plain_attack)
                
                # 重新创建跨模态组件
                jigsaw_components = jigsaw_attack.create_jigsaw_components(
                    encrypted_result, plain_attack
                )
                
                new_fallback_count = encrypted_result.get('fallback_count', 0)
                new_generation_method = encrypted_result.get('generation_method', 'unknown')
                
                print(f"Result: {new_generation_method} (fallback: {new_fallback_count})")
                
                # 如果这次结果更好，保存它
                if new_fallback_count < best_fallback_count:
                    best_fallback_count = new_fallback_count
                    best_result = {
                        'encrypted_result': encrypted_result,
                        'jigsaw_components': jigsaw_components
                    }
                    
                    # 如果已经完美了，不需要继续尝试
                    if new_fallback_count == 0:
                        print(f"   ✅ Perfect result achieved!")
                        break
                
            except Exception as e:
                print(f"Failed: {e}")
                continue
        
        # 更新样本
        if best_result and best_fallback_count < old_fallback_count:
            encrypted_result = best_result['encrypted_result']
            jigsaw_components = best_result['jigsaw_components']
            
            # 更新所有相关字段
            sample['attack_visual_symbol'] = encrypted_result['encrypted_text']
            sample['visual_mapping'] = encrypted_result['visual_mapping']
            sample['decryption_hint'] = encrypted_result['decryption_hint']
            sample['text_prompt'] = jigsaw_components['text_prompt']
            sample['image_content'] = jigsaw_components['image_content']
            sample['joint_reasoning_instruction'] = jigsaw_components['joint_reasoning_instruction']
            sample['generation_method'] = encrypted_result['generation_method']
            sample['generation_status'] = encrypted_result['generation_status']
            sample['llm_generated_count'] = encrypted_result['llm_generated_count']
            sample['fallback_count'] = encrypted_result['fallback_count']
            
            if best_fallback_count == 0:
                success_count += 1
                print(f"   🎯 SUCCESS: Improved from {old_fallback_count} to 0 fallbacks!")
            else:
                improved_count += 1
                print(f"   ⬆️  IMPROVED: Reduced from {old_fallback_count} to {best_fallback_count} fallbacks")
        else:
            still_fallback_count += 1
            print(f"   ⚠️  NO IMPROVEMENT: Still has {old_fallback_count} fallbacks")
        
        print()
    
    # 5. 保存结果
    print(f"\n{'='*70}")
    print("[Step 5] Saving results...")
    
    if output_file is None:
        # 创建备份
        backup_file = input_file.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        print(f"   Creating backup: {backup_file}")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        output_file = input_file
    
    print(f"   Writing to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Results saved!\n")
    
    # 6. 最终统计
    print(f"{'='*70}")
    print("FINAL STATISTICS")
    print(f"{'='*70}")
    print(f"Total processed: {len(needs_regeneration)}")
    print(f"  ✅ Perfect (0 fallbacks): {success_count} ({success_count/len(needs_regeneration)*100:.1f}%)")
    print(f"  ⬆️  Improved: {improved_count} ({improved_count/len(needs_regeneration)*100:.1f}%)")
    print(f"  ⚠️  No improvement: {still_fallback_count} ({still_fallback_count/len(needs_regeneration)*100:.1f}%)")
    print(f"\nOverall success rate: {(success_count + improved_count)/len(needs_regeneration)*100:.1f}%")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Regenerate emoji sequences for samples that used fallback',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        '--input', '-i',
        default='/path/to/workspace/models/mllm_attack/prompts/safebench/1216/visual_symbol_qwen3-next-80b-a3b-instruct_0_500.json',
        help='Input JSON file path (e.g., prompts/jbb/target_model.json)'
    )
    
    parser.add_argument(
        '--model', '-m',
        default='gemini-3-pro-preview',
        # default='gpt-4.1-nano-2025-04-14',
        # default='gpt-4o-2024-08-06',
        # default = 'gemini-2.5-pro-all',
        # default='qwen3-next-80b-a3b-instruct',
        help='Encryption model name (e.g., gpt-4o, claude-3-7-sonnet-20250219)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='/path/to/workspace/models/mllm_attack/prompts/safebench/1216/visual_symbol_qwen3-next-80b-a3b-instruct_0_500_r1.json',
        help='Output file path (default: overwrite input file with backup)'
    )
    
    parser.add_argument(
        '--retries', '-r',
        type=int,
        default=20,
        help='Max retries per sample (default: 3)'
    )
    
    args = parser.parse_args()
    
    # 验证输入文件存在
    if not os.path.exists(args.input):
        print(f"❌ Error: Input file not found: {args.input}")
        return
    
    # 执行重新生成
    regenerate_fallback_samples(
        input_file=args.input,
        encryption_model=args.model,
        output_file=args.output,
        max_retries=args.retries
    )


if __name__ == "__main__":
    main()