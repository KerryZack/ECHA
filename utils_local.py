import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer, AutoProcessor
from typing import Union, List, Dict, Tuple
import os

# 🆕 尝试导入vllm
from vllm import LLM, SamplingParams
VLLM_AVAILABLE = True

# 🆕 尝试导入lmdeploy
from lmdeploy import pipeline, PytorchEngineConfig, ChatTemplateConfig
from lmdeploy.vl import load_image
LMDEPLOY_AVAILABLE = True


class LocalModelManager:
    """管理本地多模态模型的加载和推理"""
    
    def __init__(self, model_path, device="cuda" if torch.cuda.is_available() else "cpu"):
        self.model_path = model_path
        self.device = device
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.model_type = self._detect_model_type()
        
    def _detect_model_type(self):
        """根据模型路径检测模型类型"""
        model_name_lower = self.model_path.lower()
        if 'qwen' in model_name_lower and 'vl' in model_name_lower:
            return 'qwen-vl'
        elif 'internvl' in model_name_lower:
            return 'internvl'
        elif 'llava' in model_name_lower:
            return 'llava'
        elif 'cogvlm' in model_name_lower:
            return 'cogvlm'
        elif 'deepseek-vl' in model_name_lower:
            return 'deepseek-vl'
        else:
            return 'generic'
    
    def load_model(self):
        """加载模型和相关组件"""
        print(f"Loading model from {self.model_path}...")
        print(f"Detected model type: {self.model_type}")
        
        try:
            if self.model_type == 'qwen-vl':
                self._load_qwen_vl()
            elif self.model_type == 'internvl':
                self._load_internvl()
            elif self.model_type == 'llava':
                self._load_llava()
            elif self.model_type == 'deepseek-vl':
                self._load_deepseek_vl()
            else:
                self._load_generic()
            
            print(f"Model loaded successfully on {self.device}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
    
    def _load_qwen_vl(self):
        """加载Qwen-VL系列模型"""
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
        
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.processor = AutoProcessor.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        self.tokenizer = self.processor.tokenizer
    
    def _load_internvl(self):
        """加载InternVL系列模型"""
        self.model = AutoModel.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        self.model.eval()
    
    def _load_llava(self):
        """加载LLaVA系列模型"""
        from transformers import LlavaForConditionalGeneration, LlavaProcessor
        
        self.model = LlavaForConditionalGeneration.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.processor = LlavaProcessor.from_pretrained(self.model_path)
        self.tokenizer = self.processor.tokenizer
    
    def _load_deepseek_vl(self):
        """加载DeepSeek-VL系列模型"""
        self.model = AutoModel.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
    
    def _load_generic(self):
        """通用加载方法"""
        self.model = AutoModel.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True
        )
        try:
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
        except:
            self.processor = None
    
    def generate(self, query, image_path=None, max_tokens=1000, temperature=0.0):
        """
        生成响应
        
        Args:
            query: 文本查询
            image_path: 图片路径
            max_tokens: 最大生成token数
            temperature: 采样温度
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            if self.model_type == 'qwen-vl':
                return self._generate_qwen_vl(query, image_path, max_tokens, temperature)
            elif self.model_type == 'internvl':
                return self._generate_internvl(query, image_path, max_tokens, temperature)
            elif self.model_type == 'llava':
                return self._generate_llava(query, image_path, max_tokens, temperature)
            elif self.model_type == 'deepseek-vl':
                return self._generate_deepseek_vl(query, image_path, max_tokens, temperature)
            else:
                return self._generate_generic(query, image_path, max_tokens, temperature)
        except Exception as e:
            print(f"Error during generation: {e}")
            return f"Error: {str(e)}"
    
    def _generate_qwen_vl(self, query, image_path, max_tokens, temperature):
        """Qwen-VL生成"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": []}
        ]
        
        if image_path:
            messages[1]["content"].append({"type": "image", "image": image_path})
        messages[1]["content"].append({"type": "text", "text": query})
        
        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        
        inputs = self.processor(
            text=[text],
            images=[Image.open(image_path)] if image_path else None,
            return_tensors="pt",
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature if temperature > 0 else 1.0,
                do_sample=temperature > 0
            )
        
        # 只解码生成的部分
        generated_ids = output_ids[0][len(inputs.input_ids[0]):]
        response = self.processor.decode(generated_ids, skip_special_tokens=True)
        return response
    
    def _generate_internvl(self, query, image_path, max_tokens, temperature):
        """InternVL生成"""
        if image_path:
            image = Image.open(image_path).convert('RGB')
            pixel_values = self.model.load_image(image_path).to(
                dtype=self.model.dtype, device=self.device
            )
            
            generation_config = dict(
                num_beams=1,
                max_new_tokens=max_tokens,
                do_sample=temperature > 0,
                temperature=temperature if temperature > 0 else 1.0,
            )
            
            response = self.model.chat(
                self.tokenizer,
                pixel_values,
                query,
                generation_config
            )
        else:
            # 纯文本模式
            response = self.model.chat(
                self.tokenizer,
                None,
                query,
                dict(max_new_tokens=max_tokens)
            )
        
        return response
    
    def _generate_llava(self, query, image_path, max_tokens, temperature):
        """LLaVA生成"""
        if image_path:
            image = Image.open(image_path)
            prompt = f"USER: <image>\n{query}\nASSISTANT:"
            inputs = self.processor(text=prompt, images=image, return_tensors="pt").to(self.device)
        else:
            prompt = f"USER: {query}\nASSISTANT:"
            inputs = self.processor(text=prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature if temperature > 0 else 1.0,
                do_sample=temperature > 0
            )
        
        response = self.processor.decode(output_ids[0], skip_special_tokens=True)
        # 提取ASSISTANT后的内容
        if "ASSISTANT:" in response:
            response = response.split("ASSISTANT:")[-1].strip()
        
        return response
    
    def _generate_deepseek_vl(self, query, image_path, max_tokens, temperature):
        """DeepSeek-VL生成"""
        if image_path:
            image = Image.open(image_path).convert('RGB')
            messages = [{"role": "user", "content": query, "images": [image]}]
        else:
            messages = [{"role": "user", "content": query}]
        
        inputs = self.model.prepare_inputs_for_generation(
            messages, self.tokenizer
        ).to(self.device)
        
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature if temperature > 0 else 1.0,
                do_sample=temperature > 0
            )
        
        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return response
    
    def _generate_generic(self, query, image_path, max_tokens, temperature):
        """通用生成方法"""
        if image_path and self.processor:
            image = Image.open(image_path)
            inputs = self.processor(
                text=query,
                images=image,
                return_tensors="pt"
            ).to(self.device)
        else:
            inputs = self.tokenizer(
                query,
                return_tensors="pt"
            ).to(self.device)
        
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature if temperature > 0 else 1.0,
                do_sample=temperature > 0
            )
        
        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return response


# 全局模型管理器缓存
_model_cache = {}


def get_local_model(model_path, device="cuda" if torch.cuda.is_available() else "cpu"):
    """获取或创建本地模型管理器（带缓存）"""
    if model_path not in _model_cache:
        manager = LocalModelManager(model_path, device)
        manager.load_model()
        _model_cache[model_path] = manager
    return _model_cache[model_path]


def api_call_mllm_local(
    model_path,
    query: str,
    image_path=None,
    max_tokens=1000,
    temperature=0.0,
    device="cuda" if torch.cuda.is_available() else "cpu"
):
    """
    本地模型推理接口，与原有api_call_mllm接口保持一致
    
    Args:
        model_path: 本地模型路径
        query: 查询文本
        image_path: 图片路径
        max_tokens: 最大生成token数
        temperature: 采样温度
        device: 设备
    
    Returns:
        生成的响应文本
    """
    model_manager = get_local_model(model_path, device)
    response = model_manager.generate(query, image_path, max_tokens, temperature)
    return response


# 🆕 vllm批量推理函数
def api_call_mllm_vllm_batch(
    model_path: str,
    prompts_and_images: List[Tuple[str, str]],
    max_tokens: int = 1000,
    temperature: float = 0.0,
    device: str = "cuda",
    use_message_format: bool = True  # 🆕 是否使用message格式
) -> List[str]:
    """
    使用vllm进行批量多模态推理
    (如果检测到是InternVL模型，将自动切换为使用LMDeploy)
    
    Args:
        model_path: 模型路径
        prompts_and_images: List of (prompt_text, image_path) tuples
        max_tokens: 最大生成token数
        temperature: 采样温度
        device: 设备
        use_message_format: 是否使用message协议格式（对于需要chat template的模型）
    
    Returns:
        生成的响应列表
    """
    # 🆕 针对 InternVL 和 LLaVA 模型，自动切换到 LMDeploy
    model_name_lower = model_path.lower()
    if 'internvl' in model_name_lower:
        if not LMDEPLOY_AVAILABLE:
            raise ImportError("LMDeploy is required for InternVL/LLaVA batch inference. Install with: pip install lmdeploy")
        model_type = "InternVL" if 'internvl' in model_name_lower else "LLaVA"
        print(f"[Info] Detected {model_type} model, switching to LMDeploy backend for better compatibility.")
        return _api_call_mllm_lmdeploy_batch(model_path, prompts_and_images, max_tokens, temperature)

    if not VLLM_AVAILABLE:
        raise ImportError("vllm is required for batch inference. Install with: pip install vllm")
    
    # 初始化vllm模型（只初始化一次）
    if not hasattr(api_call_mllm_vllm_batch, '_llm_cache'):
        api_call_mllm_vllm_batch._llm_cache = {}
        api_call_mllm_vllm_batch._tokenizer_cache = {}
    
    if model_path not in api_call_mllm_vllm_batch._llm_cache:
        print(f"Loading vllm model from {model_path}...")
        llm = LLM(
            model=model_path,
            trust_remote_code=True,
            max_model_len=8192,
            gpu_memory_utilization=0.9,
            # enforce_eager=True,
        )
        api_call_mllm_vllm_batch._llm_cache[model_path] = llm
        # 🆕 获取tokenizer（用于chat template）
        try:
            tokenizer = llm.get_tokenizer()
            api_call_mllm_vllm_batch._tokenizer_cache[model_path] = tokenizer
        except:
            api_call_mllm_vllm_batch._tokenizer_cache[model_path] = None
    else:
        llm = api_call_mllm_vllm_batch._llm_cache[model_path]
    
    tokenizer = api_call_mllm_vllm_batch._tokenizer_cache.get(model_path)
    
    # 构建多模态输入（只支持图像+文本的多模态输入）
    inputs_list = []
    
    # 🆕 尝试引入 qwen_vl_utils (如果环境中有)
    try:
        from qwen_vl_utils import process_vision_info
        QWEN_UTILS_AVAILABLE = True
    except ImportError:
        QWEN_UTILS_AVAILABLE = False
        print("⚠️ Warning: qwen_vl_utils not found. Advanced vision processing for Qwen-VL disabled.")

    for img_idx, (prompt_text, image_path) in enumerate(prompts_and_images):
        # 验证图片路径（必须存在）
        if not image_path or not os.path.exists(image_path):
            raise ValueError(f"Image path does not exist: {image_path}")
            
        # 🆕 加载图像 (必须使用 PIL 读取)
        from PIL import Image
        pil_image = Image.open(image_path).convert("RGB")
        
        prompt = prompt_text
        mm_data = {}
        mm_processor_kwargs = None # 默认为 None

        if use_message_format and tokenizer:
            # 使用message协议格式（适用于需要chat template的模型，如Qwen-VL）
            try:
                # 🆕 特殊处理 LLaVA 模型
                if 'llava' in model_path.lower():
                    # LLaVA v1.6 Mistral 格式: [INST] <image>\nPrompt [/INST]
                    # vLLM 会自动处理 <image> 占位符的替换
                    # 但为了安全起见，我们手动构建包含 <image> 的 prompt
                    prompt = f"USER: <image>\n{prompt_text}\nASSISTANT:"
                    if 'mistral' in model_path.lower():
                         prompt = f"[INST] <image>\n{prompt_text} [/INST]"
                    elif 'vicuna' in model_path.lower():
                         prompt = f"A chat between a curious human and an artificial intelligence assistant. The assistant gives helpful, detailed, and polite answers to the human's questions. USER: <image>\n{prompt_text} ASSISTANT:"

                    mm_data['image'] = pil_image
                elif 'qwen' in model_path.lower() and '2.5' in model_path.lower():
                    # Qwen2.5-VL 的 tokenizer 模板可能不兼容列表输入，手动构建以避开 TypeError
                    prompt = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n<|vision_start|><|image_pad|><|vision_end|>{prompt_text}<|im_end|>\n<|im_start|>assistant\n"
                    mm_data['image'] = pil_image
                else:
                    # 其他模型（如 Qwen-VL）使用标准的 chat template
                    # 按照指定格式构建message
                    messages = [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "image", "image": pil_image}, # 这里直接传 pil_image，供 process_vision_info 使用
                                {"type": "text", "text": prompt_text},
                            ],
                        }
                    ]
                    # 1. 生成 Prompt 文本
                    # Qwen2-VL 的 chat template 需要正确的占位符
                    prompt = tokenizer.apply_chat_template(
                        messages, 
                        tokenize=False, 
                        add_generation_prompt=True
                    )
                    
                    # 2. 处理视觉信息 (针对 Qwen2-VL 等新模型)
                    # 只有当模型是 Qwen 且工具可用时才使用高级处理
                    is_qwen = 'qwen' in model_path.lower()
                    
                    if is_qwen and QWEN_UTILS_AVAILABLE:
                        # 使用 process_vision_info 处理
                        # 注意：process_vision_info 需要 messages 里的 image 是 PIL 对象或路径
                        image_inputs, video_inputs, video_kwargs = process_vision_info(
                            messages,
                            return_video_kwargs=True
                        )
                        
                        if image_inputs is not None:
                            mm_data['image'] = image_inputs
                        if video_inputs is not None:
                            mm_data['video'] = video_inputs
                        
                        # 传递额外的 processor 参数 (如 patch size, resolution 等)
                        mm_processor_kwargs = video_kwargs
                    else:
                        # 通用回退逻辑：直接传递 PIL Image
                        mm_data['image'] = pil_image

            except Exception as e:
                print(f"⚠️ Warning: Failed to use message format/vision info, falling back to basic: {e}")
                import traceback
                traceback.print_exc()
                
                # 回退策略：如果是 LLaVA，必须保留 <image>
                if 'llava' in model_path.lower():
                     prompt = f"[INST] <image>\n{prompt_text} [/INST]" if 'mistral' in model_path.lower() else f"USER: <image>\n{prompt_text}\nASSISTANT:"
                else:
                    prompt = prompt_text
                    
                mm_data['image'] = pil_image
        else:
            # 不使用 chat template 的情况
            if 'llava' in model_path.lower():
                 prompt = f"[INST] <image>\n{prompt_text} [/INST]" if 'mistral' in model_path.lower() else f"USER: <image>\n{prompt_text}\nASSISTANT:"
            else:
                 # 这种情况下 prompt 可能没有 <image>，vLLM 可能会报错
                 prompt = prompt_text
            
            mm_data['image'] = pil_image
        
        # 🆕 构造符合 vLLM 规范的输入字典
        input_dict = {
            "prompt": prompt,
            "multi_modal_data": mm_data
        }
        
        # 如果有额外的 processor 参数 (Qwen2-VL 需要)，则添加
        if mm_processor_kwargs:
             input_dict['mm_processor_kwargs'] = mm_processor_kwargs
             
        inputs_list.append(input_dict)
    
    # 批量推理
    sampling_params = SamplingParams(
        temperature=temperature,
        max_tokens=max_tokens,
        top_k=-1,
    )
    
    # 🆕 传入 inputs_list 而不是 prompts_list
    outputs = llm.generate(inputs_list, sampling_params)
    
    # 提取结果
    responses = []
    for output in outputs:
        if output.outputs:
            response = output.outputs[0].text
            responses.append(response)
        else:
            responses.append("")
    
    return responses


def _api_call_mllm_lmdeploy_batch(
    model_path: str,
    prompts_and_images: List[Tuple[str, str]],
    max_tokens: int = 1000,
    temperature: float = 0.0
) -> List[str]:
    """
    内部函数：使用 LMDeploy 进行批量推理 (专用于 InternVL 和 LLaVA)
    """
    # 初始化 LMDeploy pipeline (带有缓存)
    if not hasattr(_api_call_mllm_lmdeploy_batch, '_pipe_cache'):
        _api_call_mllm_lmdeploy_batch._pipe_cache = {}
        
    if model_path not in _api_call_mllm_lmdeploy_batch._pipe_cache:
        print(f"Loading LMDeploy pipeline from {model_path}...")
        
        # 🆕 LLaVA 模型强制使用 PyTorch 引擎以获得更好的兼容性
        model_name_lower = model_path.lower()
        if 'llava' in model_name_lower:
            print(f"[Info] Using PyTorch backend for LLaVA model")
            backend_config = PytorchEngineConfig(
                session_len=8192,
                cache_max_entry_count=0.5,
            )
            pipe = pipeline(model_path, backend_config=backend_config)
        else:
            # InternVL 和其他模型使用默认配置，LMDeploy 会自动选择最优引擎
            print(f"[Info] Using default backend (auto-select)")
            pipe = pipeline(model_path)
        
        _api_call_mllm_lmdeploy_batch._pipe_cache[model_path] = pipe
    else:
        pipe = _api_call_mllm_lmdeploy_batch._pipe_cache[model_path]

    # 构建输入数据
    # LMDeploy 的 pipeline 接受 (prompt, image) 或者 列表
    # 对于多模态，输入格式为 [(prompt, image_path), ...] 
    # 或者直接使用内部的 promt 模板格式
    
    batch_inputs = []
    for prompt_text, image_path in prompts_and_images:
        # 验证图片路径
        if not image_path or not os.path.exists(image_path):
             raise ValueError(f"Image path does not exist: {image_path}")
        
        # 加载图片
        image = load_image(image_path)
        batch_inputs.append((prompt_text, image))

    # 执行批量推理
    # gen_config 可以控制生成参数
    from lmdeploy import GenerationConfig
    gen_config = GenerationConfig(
        max_new_tokens=max_tokens,
        temperature=temperature if temperature > 0 else 0.01, # lmdeploy temperature不能为0
        top_p=0.8 if temperature > 0 else 1.0,
        top_k=40
    )

    print(f"Running LMDeploy inference on batch of {len(batch_inputs)} items...")
    responses_obj = pipe(batch_inputs, gen_config=gen_config)
    
    # 提取文本结果
    results = [resp.text for resp in responses_obj]
    
    return results


if __name__ == "__main__":
    # 测试代码：验证 vLLM 批量推理能否正确处理 Qwen3-VL 的图片输入
    
    # 指定路径
    model_path = "/path/to/workspace/model_zoo/Qwen3-VL-8B-Instruct"
    image_path = "/path/to/workspace/paddle/test.jpeg"
    
    # 检查路径是否存在
    if not os.path.exists(model_path):
        print(f"⚠️ Warning: Model path does not exist locally: {model_path}")
    if not os.path.exists(image_path):
        print(f"⚠️ Warning: Image path does not exist locally: {image_path}")

    if os.path.exists(image_path):
        # 构造批量输入
        # 1. 详细描述（验证视觉理解）
        # 2. OCR 测试（如果有文字）或者询问具体颜色/物体（验证细节关注）
        prompts_and_images = [
            ("Describe this image in detail.", image_path),
            ("What are the main colors in this image?", image_path)
        ]

        print(f"\n🧪 Testing api_call_mllm_vllm_batch with model: {model_path}")
        try:
            responses = api_call_mllm_vllm_batch(
                model_path=model_path,
                prompts_and_images=prompts_and_images,
                max_tokens=200,
                temperature=0.01,  # 低温度以获得确定性结果
                use_message_format=True # Qwen3-VL 通常需要 chat template
            )

            print("\n✅ Inference Results:")
            for i, (prompt, _) in enumerate(prompts_and_images):
                print(f"\n[Test Case {i+1}]")
                print(f"Prompt: {prompt}")
                print(f"Response: {responses[i]}")
                print("-" * 30)

        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Skipping test: No image available.")