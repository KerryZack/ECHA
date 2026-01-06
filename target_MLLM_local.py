import time
from utils_local import api_call_mllm_local, get_local_model


class TargetLLMLocal:
    """本地多模态大语言模型推理类"""
    
    def __init__(self, model_path, max_tokens=512, temperature=0.0, device="cuda"):
        """
        初始化本地模型
        
        Args:
            model_path: 本地模型文件路径
            max_tokens: 最大生成token数
            temperature: 采样温度
            device: 设备 ("cuda" 或 "cpu")
        """
        self.model_path = model_path
        self.max_retry = 3
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.device = device
        
        # 预加载模型
        print(f"Initializing local model from {model_path}...")
        self.model_manager = get_local_model(model_path, device)
        print("Model initialized successfully.")
    
    def generate(self, prompt_text, image_path=None):
        """
        生成响应
        
        Args:
            prompt_text: 提示文本
            image_path: 图片路径（可选）
        
        Returns:
            生成的响应文本
        """
        for attempt in range(self.max_retry):
            try:
                resp = api_call_mllm_local(
                    model_path=self.model_path,
                    query=prompt_text,
                    image_path=image_path,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    device=self.device
                )
                return resp
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.max_retry} failed: {e}")
                if attempt < self.max_retry - 1:
                    time.sleep(2)  # 短暂等待后重试
                else:
                    summ = f"All {self.max_retry} retry attempts failed. Last error: {str(e)}"
                    return summ
    
    def generate_batch(self, prompts_and_images, use_vllm=True):
        """
        批量生成
        
        Args:
            prompts_and_images: List of (prompt_text, image_path) tuples
            use_vllm: 是否使用vllm进行批量推理（默认True）
        
        Returns:
            生成的响应列表
        """
        # 🆕 如果vllm可用且启用，使用vllm批量推理
        if use_vllm and VLLM_AVAILABLE:
            try:
                return api_call_mllm_vllm_batch(
                    model_path=self.model_path,
                    prompts_and_images=prompts_and_images,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    device=self.device
                )
            except Exception as e:
                print(f"⚠️ vllm batch inference failed: {e}, falling back to serial processing")
                # 降级到串行处理
                pass
        
        # 串行处理（降级方案）
        results = []
        for prompt_text, image_path in prompts_and_images:
            result = self.generate(prompt_text, image_path)
            results.append(result)
        return results


# 兼容性包装：保持与原有TargetLLM相同的接口
class TargetLLM(TargetLLMLocal):
    """别名，保持向后兼容"""
    pass


if __name__ == "__main__":
    # 测试代码
    model_path = "/path/to/your/local/model"  # 替换为实际的模型路径
    
    # 创建模型实例
    target_llm = TargetLLMLocal(
        model_path=model_path,
        max_tokens=512,
        temperature=0.0,
        device="cuda"
    )
    
    # 测试单个查询
    query = "请描述这张图片的内容"
    image_path = "./demo/demo1.png"
    
    print("Generating response...")
    response = target_llm.generate(query, image_path)
    print(f"Response: {response}")
    
    # 测试批量查询
    batch_queries = [
        ("图片中有什么？", "./images/0.png"),
        ("这是什么场景？", "./images/1.png"),
    ]
    
    print("\nGenerating batch responses...")
    batch_responses = target_llm.generate_batch(batch_queries)
    for i, resp in enumerate(batch_responses):
        print(f"Response {i+1}: {resp}")