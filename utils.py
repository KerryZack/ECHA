import time
# from fsspec.caching import P  # 未使用的导入
from openai import OpenAI
from typing import Union, List
import os
import json
import base64
# API配置 - 请在本地设置环境变量或创建 config.py
# 示例: export API_KEY="your_api_key_here"
import os

qwen_API_KEY = os.getenv("QWEN_API_KEY", "your-qwen-api-key-here")
qwen_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


API_KEY = os.getenv("API_KEY", "your-api-key-here")
BASE_URL_GPT = os.getenv("BASE_URL_GPT", "https://api.openai.com/v1")
gpt_client = OpenAI(base_url=BASE_URL_GPT, api_key=API_KEY)
claude_client = OpenAI(base_url=BASE_URL_GPT, api_key=API_KEY)
gemini_client = OpenAI(base_url=BASE_URL_GPT, api_key=API_KEY)
deepseek_client = OpenAI(base_url=BASE_URL_GPT, api_key=API_KEY)



qwen_client =OpenAI(
    base_url=os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
    api_key=os.getenv('MODELSCOPE_TOKEN', 'your-modelscope-token-here'),
)


seed_client = OpenAI(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=os.getenv('VOLCES_API_KEY', 'your-volces-api-key-here'),
)

internvl_client = OpenAI(
    api_key=os.getenv('INTERNVL_API_KEY', 'your-internvl-api-key-here'),
    base_url="https://chat.intern-ai.org.cn/api/v1/",
)

# qwen_client = OpenAI(base_url=qwen_BASE_URL, api_key=qwen_API_KEY)

# DeepSeek 配置示例
# deep_api_key = os.getenv('DEEPSEEK_API_KEY', 'your-deepseek-api-key-here')
# deep_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
# deepseek_cilent = OpenAI(base_url=deep_url, api_key=deep_api_key)

llama_url = os.getenv('DEEPINFRA_BASE_URL', 'https://api.deepinfra.com/v1/openai')
llama_key = os.getenv('DEEPINFRA_API_KEY', 'your-deepinfra-api-key-here')
llama_client = OpenAI(base_url=llama_url, api_key=llama_key)



def get_image_base64_url(image_path):
    if image_path:
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        image_base64 = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{image_base64}"
    return None

def api_call_mllm(client, query: Union[List, str],
             image,
             model_name="deepseek-chat",
             response_format='text',
             temperature=0.0,
             max_tokens=1000):
    if isinstance(query, List):
        messages = query
    elif isinstance(query, str):
        # 如果有图片，转成base64
        image_url = None
        if image:
            image_url = get_image_base64_url(image)

        # 构造消息列表
        messages = []
        
        # 添加系统提示词
        messages.append({
            "role": "system",
            "content": "You are a helpful assistant."
        })
        
        # 添加用户查询
        current_user_content = [{"type": "text", "text": query}]
        if image_url:
            current_user_content.append({"type": "image_url", "image_url": {"url": image_url}})

        messages.append({
            "role": "user",
            "content": current_user_content,
        })

        # messages = json.dumps(messages)
    for _ in range(3):
        if 'gpt-5' in model_name or 'gpt5' in model_name:
            print(f"use {model_name}")
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                )

                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue
        
        elif 'gpt' in model_name:
            # print(f"use {model_name}")
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )

                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'deepseek' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format},
                    stream=False
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue
        
        elif 'gemini' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue
            
        elif 'claude' in model_name:
            # print("use claude model")
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'Qwen' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'seed' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'internvl' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'meta' in model_name:

            try:

                completion = client.chat.completions.create(

                    model=model_name,

                    messages=messages,

                    max_tokens=max_tokens,

                    temperature=temperature,

                    response_format={"type": response_format},

                    # stream=True

                )

                resp = completion.choices[0].message.content

                return resp

            except Exception as e:

                print(messages)

                print(f"API_CALL Error: {e}")

                time.sleep(3)

                continue

    return ""


def api_call(client, query: Union[List, str],
             model_name="deepseek-chat",
             response_format='text',
             temperature=0.0,
             max_tokens=1000):
    if isinstance(query, List):
        messages = query
    elif isinstance(query, str):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query}
                    ]
        # messages = json.dumps(messages)
    for _ in range(3):
        if 'gpt' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'gemini' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format},
                    stream=False
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'deepseek' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format},
                    stream=False
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'claude' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue

        elif 'qwen' in model_name:
            try:
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": response_format}
                )
                resp = completion.choices[0].message.content
                return resp
            except Exception as e:
                print(f"API_CALL Error: {e}")
                time.sleep(3)
                continue


        elif 'meta' in model_name:

            try:

                completion = client.chat.completions.create(

                    model=model_name,

                    messages=messages,

                    max_tokens=max_tokens,

                    temperature=temperature,

                    response_format={"type": response_format},

                    # stream=True

                )

                resp = completion.choices[0].message.content

                return resp

            except Exception as e:

                print(messages)

                print(f"API_CALL Error: {e}")

                time.sleep(3)

                continue

    return ""



def get_client(model_name):
    if 'gpt' in model_name:
        return gpt_client
    elif 'claude' in model_name:
        return claude_client
    elif 'deepseek' in model_name:
        return deepseek_client
    elif 'Qwen' in model_name:
        print("qwen")
        return qwen_client
    elif 'Meta' in model_name:
        return llama_client
    elif 'gemini' in model_name:
        return gemini_client
    elif 'seed' in model_name:
        return seed_client
    elif 'internvl' in model_name:
        return internvl_client

def change_type(value):
    if isinstance(value, int):
        # 如果是整数类型，保持不变
        return value
    elif isinstance(value, str):
        # 如果是字符串类型，将其转换为整数
        try:
            return int(value)
        except ValueError:
            print(value)
            value = 1
            # print("无法将字符串转换为整数")
            return value
    else:
        value = 1
        print("不支持的类型")
        return value

def delete_files_in_directory_if_exists(directory_path):
    if os.path.exists(directory_path):
        print(f"路径 '{directory_path}' 存在，正在删除其中的所有文件...")
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # 删除文件或符号链接
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # 删除目录及其所有内容
            except Exception as e:
                print(f"删除 {file_path} 时出错: {e}")
        print(f"已删除路径 '{directory_path}' 下的所有文件。")
    else:
        print(f"路径 '{directory_path}' 不存在，无需删除文件。")


if __name__ == "__main__":
    query = "who are you"
    model_name = "Qwen/Qwen3-VL-30B-A3B-Instruct"
    image_path = "./emojis/Decryption.png"
    client = get_client(model_name)
    print("start")
    res = api_call_mllm(client, query, image = image_path, model_name=model_name)
    print(res)

