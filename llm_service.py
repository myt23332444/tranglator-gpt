#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
大语言模型服务模块 - 支持不同的翻译API
"""

import os
import json
import requests
from typing import Dict, Any, Optional

class TranslationService:
    """翻译服务基类"""
    
    def __init__(self, config_path="config.json"):
        """初始化翻译服务
        
        参数:
            config_path (str): 配置文件路径
        """
        self.config = self.load_config(config_path)
        self.service_type = self.config.get("translation_service", "openai")
    
    def load_config(self, config_path: str) -> Dict[str, Any]:

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 返回默认配置
            return {
                "translation_service": "openai",
                "services": {
                    "openai": {
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.3,
                        "api_endpoint": "https://api.openai.com/v1/chat/completions"
                    }
                }
            }
    
    def translate(self, text: str, target_lang: str = "中文") -> str:

        if self.service_type == "openai":
            return self.translate_with_openai(text, target_lang)
        elif self.service_type == "local_llm":
            return self.translate_with_local_llm(text, target_lang)
        else:
            return f"不支持的翻译服务: {self.service_type}"
    
    def translate_with_openai(self, text: str, target_lang: str) -> str:

        try:
            import openai
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return f"错误: 未设置OpenAI API密钥。原文: {text}"
            
            openai.api_key = api_key
            
            service_config = self.config["services"]["openai"]
            
            response = openai.ChatCompletion.create(
                model=service_config.get("model", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": f"你是一个翻译助手，请将以下文本翻译成{target_lang}，只输出翻译结果，不要加任何解释。"},
                    {"role": "user", "content": text}
                ],
                temperature=service_config.get("temperature", 0.3),
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"OpenAI翻译错误: {str(e)}\n原文: {text}"
    
    def translate_with_local_llm(self, text: str, target_lang: str) -> str:

        try:
            service_config = self.config["services"]["local_llm"]
            api_endpoint = service_config.get("api_endpoint", "http://localhost:8000/v1/chat/completions")
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # 如果有API密钥
            api_key = os.getenv("LOCAL_LLM_API_KEY")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            payload = {
                "model": service_config.get("model", "model_name"),
                "messages": [
                    {"role": "system", "content": f"你是一个翻译助手，请将以下文本翻译成{target_lang}，只输出翻译结果，不要加任何解释。"},
                    {"role": "user", "content": text}
                ],
                "temperature": service_config.get("temperature", 0.3)
            }
            
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                return f"本地LLM API错误: HTTP {response.status_code}\n原文: {text}"
        
        except Exception as e:
            return f"本地LLM翻译错误: {str(e)}\n原文: {text}"


def translate_text(text: str, target_lang: str = "中文", config_path: str = "config.json") -> str:

    service = TranslationService(config_path)
    return service.translate(text, target_lang)
