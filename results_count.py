import json
from collections import Counter


def process_json(input_file, output_file):
    # 打开原始 JSON 文件并读取数据
    with open(input_file, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    # 用来保存提取后的数据
    extracted_data = []
    score_counter = Counter()  # 统计judge_score的出现次数

    # 遍历数据并提取 plain_attack 和 judge_score
    for item in data:
        if 'plain_attack' in item and 'judge_score' in item:
            plain_attack = item['plain_attack']
            judge_score = item['judge_score']

            # # 如果 judge_score 是 -1，则将其视为 1
            if judge_score == -1:
                judge_score = 1

            # 将 plain_attack 和 judge_score 作为一个新字典保存
            extracted_data.append({
                'plain_attack': plain_attack,
                'judge_score': judge_score
            })

            # 统计 judge_score 出现的次数
            score_counter[judge_score] += 1

    # 将提取的数据保存到新的 JSON 文件中
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(extracted_data, outfile, ensure_ascii=False, indent=4)

    # 输出统计结果
    print("Judge score counts:")
    for score in range(1, 6):
        print(f"{score}: {score_counter[score]}")


def count_answers(file):
    # 用来统计每个 plain_attack 下 A 的数量
    # 打开原始 JSON 文件并读取数据
    with open(file, 'r', encoding='utf-8') as infile:
        data = json.load(infile)
    # 用来统计每个 plain_attack 下 A 的数量
    plain_attack_counts = {}
    # 用来统计所有 A 的总数
    total_A_count = 0

    # 遍历数据中的每个 plain_attack 项
    for item in data:
        plain_attack = item.get("plain_attack", {})
        qA_pairs = item.get("qA_pairs", [])

        # 遍历 qA_pairs 列表中的每个问答对
        for qA_pair in qA_pairs:
            answers = qA_pair.get("A", [])

            # 如果 A 是列表，统计其长度并增加到 total_A_count
            count_A = len(answers)

            # 统计每个 plain_attack 下的 A 数量
            if plain_attack not in plain_attack_counts:
                plain_attack_counts[plain_attack] = 0
            plain_attack_counts[plain_attack] += count_A
            total_A_count += count_A

    return plain_attack_counts, total_A_count


 
if __name__ == "__main__":
    input_file = '/path/to/workspace/models/mllm_attack/results/hades/attack_gemini-2.5-flash-lite_rewrite_gpt-4.1-nano-2025-04-14_temp_0.0_results_0_750.json'  # 原始 JSON 文件
    output_file = '/path/to/workspace/models/mllm_attack/results/hades/hades_gemini-2.5-flash-lite.json'  # 输出的 JSON 文件

    plain_attack_counts, total_A_count = count_answers(input_file)
    print("每个plain_attack下的A数量:", plain_attack_counts)
    print("所有A的总数:", total_A_count)
    process_json(input_file, output_file)