"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def __init__(self):
        self.model_name = "Mock Offline"
        self._call_count = 0

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        self._call_count += 1

        # Kiểm tra nếu đang dùng baseline chatbot prompt (không có ReAct)
        if "chatbot tư vấn quà tặng thông thường" in system_prompt.lower():
            if "hướng nội" in text or "đọc sách" in text:
                return ("Bạn có thể tặng sách, trà, hoặc nến thơm cho người hướng nội thích đọc sách. "
                        "Tuy nhiên, tôi không có quyền truy cập cơ sở dữ liệu sản phẩm cụ thể nên không thể gợi ý giá cả chính xác.")
            elif "k-pop" in text or "mỹ phẩm" in text:
                return ("Với người thích K-pop và mỹ phẩm, bạn có thể tặng album, lightstick, hoặc set skincare. "
                        "Tôi chỉ gợi ý chung, không có thông tin giá cả cụ thể.")
            elif "thủ đô" in text or "lập trình" in text or "phổ biến" in text:
                return "Đây là câu hỏi kiến thức chung. Tôi có thể trả lời dựa trên hiểu biết có sẵn của mình."
            elif "ngoài hành tinh" in text or "zorgon" in text or "atlantis" in text:
                return "Xin lỗi, tôi không thể tư vấn quà cho đối tượng không có thật. Vui lòng mô tả một người thật."
            return "🤖 [Mock Chatbot]: Tôi có thể gợi ý quà tặng chung, nhưng không truy cập được dữ liệu sản phẩm cụ thể."

        # ReAct Agent mode — sinh response theo format Thought -> Action
        if "observation:" in text:
            # Đã có observation → sinh Final Answer
            return "Thought: Tôi đã có đủ thông tin từ các công cụ để trả lời người dùng.\nFinal Answer: Dựa trên phân tích tính cách và tìm kiếm sản phẩm, tôi gợi ý bạn tặng sách hoặc set trà cao cấp. Đây là quà phù hợp với người hướng nội thích đọc sách và uống trà."
        elif "tính cách" in text or "hướng nội" in text or "sở thích" in text:
            return "Thought: Cần phân tích tính cách người nhận quà trước.\nAction: analyze_personality[hướng nội, thích đọc sách, uống trà]"
        elif "sản phẩm" in text or "ngân sách" in text or "search" in text:
            return "Thought: Cần tìm sản phẩm quà tặng phù hợp.\nAction: search_gift_products[sách, 500000]"
        elif "ngoài hành tinh" in text or "zorgon" in text:
            return "Thought: Cần phân tích tính cách đối tượng.\nAction: analyze_personality[người ngoài hành tinh Zorgon]"
        elif "phổ biến" in text or "lý thuyết" in text or "lập trình" in text:
            return "Thought: Đây là câu hỏi kiến thức chung, không cần tool.\nFinal Answer: Quà phổ biến cho nam 25-30 gồm: đồ công nghệ, ví da, nước hoa, sách self-help."
        else:
            return "Thought: Cần phân tích thêm thông tin từ người dùng.\nAction: analyze_personality[chưa rõ tính cách]"


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
