# ECHA: Jailbreaking LVLMs via the Mismatch between Implicit Semantic Reconstruction and Explicit Safety Alignment

<p align="center">
  <b>ACL 2026 Findings</b>
</p>

<p align="center">
  <a href="https://github.com/KerryZack/ECHA"><img src="https://img.shields.io/badge/GitHub-Code-blue?logo=github" alt="GitHub"></a>
  <a href="https://arxiv.org/abs/xxx"><img src="https://img.shields.io/badge/arXiv-Paper-red?logo=arxiv" alt="arXiv"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

## Overview

We reveal a critical systemic vulnerability in Large Vision-Language Models (LVLMs): the **Mismatch between Implicit Semantic Reconstruction and Explicit Safety Alignment**. LVLMs can implicitly synthesize holistic malicious semantics from fragmented visual cues, while existing safety guardrails fail to intercept such latent intent.

To exploit this, we propose **ECHA (Emoji Chain Hinting Attack)**, a black-box visual typography jailbreaking framework that:

1. **Decouples** sensitive concepts into semantically related emoji chains and structural text masks
2. **Frames** the decoding within benign scenario-based prompts via in-context demonstrations
3. **Induces** the model to internally reconstruct prohibited intent from abstract visual symbols

ECHA achieves an Attack Success Rate (ASR) **exceeding 81%** across seven SOTA LVLMs with a single attempt.

<p align="center">
  <img src="images/overview.jpg" alt="ECHA Framework Overview" width="90%">
</p>

## Main Results

| Model | Hades (ASR%) | SafeBench (ASR%) |
|---|:---:|:---:|
| **Closed-Source** | | |
| Gemini-2.5-Flash | **96.9** | **91.5** |
| GPT-4o-Mini | **88.3** | **90.8** |
| GPT-4.1-Nano | **83.9** | **93.2** |
| **Open-Source** | | |
| Qwen2.5-VL-7B | **82.0** | **86.8** |
| Qwen3-VL-8B | **94.1** | **90.0** |
| LLaVA-NeXT-7B | **80.5** | **81.0** |
| InternVL-3.5-4B | **92.6** | **83.8** |

## Setup

### Prerequisites

- Python 3.10+
- CUDA 12.1+ (for local model inference)

### Installation

```bash
git clone https://github.com/KerryZack/ECHA.git
cd ECHA

pip install openai pandas tqdm Pillow pilmoji
pip install torch torchvision
pip install transformers accelerate

# For local inference with vLLM (optional)
pip install vllm
# For InternVL / LLaVA local inference (optional)
pip install lmdeploy
```

### Configuration

Copy the example config and fill in your API keys:

```bash
cp config.example.py config.py
```

Edit `config.py` with your credentials:

```python
API_KEY = "your-openai-api-key"
BASE_URL_GPT = "https://api.openai.com/v1"
QWEN_API_KEY = "your-qwen-api-key"
# ... other keys as needed
```

Alternatively, set environment variables:

```bash
export API_KEY="your-openai-api-key"
export QWEN_API_KEY="your-qwen-api-key"
```

## Project Structure

```
ECHA/
├── main.py                    # End-to-end API-based attack pipeline
├── main_vllm.py               # Orchestrator for vLLM-based pipeline
├── step1_generate_images.py   # Step 1: Generate adversarial images + JSONL
├── step2_vllm_inference.py    # Step 2: vLLM batch inference on target models
├── infer_target.py            # API inference on target models (Hades)
├── infer_target_safebench.py  # API inference on target models (SafeBench)
├── infer_target_bs.py         # API inference for baselines
│
├── data_pre.py                # Data preparation: emoji chain & mask generation
├── visual_encryption.py       # Visual symbol generation & cross-modal encoding
├── text2image.py              # Image rendering with emoji chains & text masks
├── image_mask.py              # Text-to-image rendering utilities
│
├── scenario_prompts.py        # Benign scenario prompt templates
├── hades_scenario_prompts.py  # Hades-specific scenario prompts
├── hades_scenario_prompts_gpt4.py  # GPT-4 variant scenario prompts
│
├── target_MLLM.py             # API-based target model wrapper
├── target_MLLM_local.py       # Local target model wrapper
├── target_llm.py              # Text-only LLM wrapper (auxiliary model)
├── utils.py                   # API clients (OpenAI, Gemini, Qwen, etc.)
├── utils_local.py             # Local model loading (HuggingFace, vLLM)
├── utils_logger.py            # Logging utilities
│
├── judge.py                   # GPT-4 based safety judge
├── judge_templete.py          # Judge prompt templates
├── safety_judge.py            # JSONL-based safety evaluation
├── evaluate_judge.py          # Batch evaluation with GPT4Judge
├── post_process.py            # HTML/response post-processing
├── results_count.py           # Result statistics
├── regenerate.py              # Regenerate failed samples
│
├── test_qwen3guard_batch.py   # Qwen3-Guard-Gen-8B evaluation
├── test_qwenguard_bl.py       # Qwen Guard baseline evaluation
├── test_vllmres_qwen3guard.py # Qwen Guard on vLLM results
│
├── Figstep_scripts/           # FigStep baseline scripts
├── data/                      # Datasets
│   ├── safebench.csv          # SafeBench benchmark
│   ├── hades_metadata.jsonl   # Hades benchmark
│   └── data_harmful_behaviors.csv
│
├── config.example.py          # API key configuration template
├── run.sh                     # Hades vLLM pipeline script
├── run_bs.sh                  # Baseline pipeline script
└── run_safebench.sh           # SafeBench vLLM pipeline script
```

## Usage

### Pipeline Overview

ECHA operates through a three-stage pipeline:

```
Step 1: Visual Payload Construction
  → Emoji chain mapping + text mask generation + image rendering

Step 2: Target Model Inference
  → Feed adversarial images to victim LVLMs

Step 3: Safety Evaluation
  → Judge responses with Qwen3-Guard-Gen-8B
```

### Option A: End-to-End API Pipeline

For attacking closed-source models (GPT, Gemini) or any model via API:

```bash
python main.py \
    --dataset safebench \
    --target-model gpt-4o-mini-2024-07-18 \
    --encryption-method visual_symbol \
    --start-idx 0 \
    --end-idx 400
```

Key arguments:
- `--dataset`: `hades` or `safebench`
- `--target-model`: Model name (e.g., `gpt-4.1-nano-2025-04-14`, `gemini-2.5-flash-lite`)
- `--encryption-method`: `visual_symbol` (default ECHA), `jigsaw`, `hybrid`, or `none`

### Option B: vLLM Local Inference Pipeline

For attacking open-source models locally:

**Step 1** — Generate adversarial images and JSONL:

```bash
python step1_generate_images.py \
    --input-file ./prompts/safebench/visual_symbol_qwen3-next-80b-a3b-instruct_0_500.json \
    --dataset safebench \
    --start-idx 0 \
    --end-idx 400
```

**Step 2** — Run vLLM batch inference:

```bash
python step2_vllm_inference.py \
    --jsonl-file ./prompts/safebench/vllm_input_0_400_universal.jsonl \
    --local-model-path /path/to/Qwen2.5-VL-7B-Instruct \
    --model-name qwen25vl
```

**Step 3** — Evaluate with Qwen3-Guard:

```bash
python test_vllmres_qwen3guard.py \
    --input-file ./results/safebench/vllm_input_0_400_universal_qwen25vl_inference.jsonl \
    --output-file ./results/safebench/qwen25vl_qwen3guard.json \
    --group-size 50
```

Or use the provided shell scripts:

```bash
# Hades dataset
bash run.sh

# SafeBench dataset
bash run_safebench.sh

# Baselines (SI)
bash run_bs.sh
```

> **Note:** Update the paths in the shell scripts to match your environment before running.

### Running Baselines

**FigStep:**

```bash
cd Figstep_scripts
bash run_fs.sh
```

**SI (Shuffle Inconsistency):**

```bash
bash run_bs.sh
```

## Datasets

| Dataset | # Queries | Categories | Source |
|---------|:---------:|:----------:|--------|
| **Hades** | 750 | 5 (Animal, Financial, Privacy, Self-Harm, Violence) | [Li et al., 2024](https://github.com/AoiDragon/HADES) |
| **SafeBench** | 400 | 8 (Illegal Activity, Hate Speech, Malware, Physical Harm, Fraud, Adult Content, Privacy Violation, Legal Opinion) | [Gong et al., 2025](https://github.com/CryptoAILab/FigStep/tree/main/data) ([paper](https://arxiv.org/abs/2311.05608)) |

## Target Models

| Model | Type | Access |
|-------|------|--------|
| GPT-4.1-Nano | Closed-source | API |
| GPT-4o-Mini | Closed-source | API |
| Gemini-2.5-Flash | Closed-source | API |
| Qwen2.5-VL-7B-Instruct | Open-source | Local / API |
| Qwen3-VL-8B-Instruct | Open-source | Local / API |
| LLaVA-NeXT-Mistral-7B | Open-source | Local |
| InternVL-3.5-4B-Instruct | Open-source | Local |

## Evaluation

We use **Qwen3-Guard-Gen-8B** as the automated safety judge, which provides a three-tier classification (Safe / Controversial / Unsafe) and verifies whether the response substantively fulfills the prohibited objective. A jailbreak is deemed successful if and only if the judge returns **Unsafe** and confirms no refusal was triggered.

## Ethical Statement

This research is conducted to expose systemic vulnerabilities in LVLM safety alignment and to accelerate the development of more robust defenses. The techniques presented are intended solely for academic red-teaming purposes. We strongly oppose any misuse of these methods to generate harmful content.

## License

This project is released under the [MIT License](LICENSE).
