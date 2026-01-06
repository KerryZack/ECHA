import time
from utils import api_call, get_client,api_call_mllm


class TargetLLM:
    def __init__(self, model_name, max_tokens=512, seed=725, temperature=0.0):
        self.client = get_client(model_name)
        self.model_name = model_name
        self.max_retry = 3
        self.timeout = 200
        self.query_sleep = 20
        self.max_tokens = max_tokens
        self.seed = seed
        self.temperature = temperature

    def generate(self, prompt_text, image_path, ):
        # api_call_mllm 已经包含重试逻辑（3次重试）
        # 所以这里不需要额外的重试和异常处理
        resp = api_call_mllm(
            client=self.client,
            query=prompt_text,
            image=image_path,
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        # api_call_mllm 失败时会返回空字符串
        if not resp or resp.strip() == "":
            
            return "All retry attempts failed."
        
        return resp