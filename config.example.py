"""
API配置示例文件

使用方法：
1. 复制此文件为 config.py
2. 填入你的真实API密钥
3. config.py 已在 .gitignore 中，不会被上传

或者使用环境变量：
export API_KEY="your-api-key-here"
export QWEN_API_KEY="your-qwen-api-key-here"
等等...
"""

# OpenAI / GPT API
API_KEY = "your-api-key-here"
BASE_URL_GPT = "https://api.openai.com/v1"  # 或者你使用的其他API服务地址

# Qwen API
QWEN_API_KEY = "your-qwen-api-key-here"
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# ModelScope Token
MODELSCOPE_TOKEN = "your-modelscope-token-here"

# Volces API Key
VOLCES_API_KEY = "your-volces-api-key-here"

# InternVL API Key
INTERNVL_API_KEY = "your-internvl-api-key-here"

# DeepInfra API
DEEPINFRA_API_KEY = "your-deepinfra-api-key-here"
DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai"

# DeepSeek API (可选)
# DEEPSEEK_API_KEY = "your-deepseek-api-key-here"
# DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
