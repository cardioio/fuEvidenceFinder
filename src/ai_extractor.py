"""
AI信息提取模块 - 负责使用AI API从摘要中提取结构化信息
"""
import json
import logging
import time
import requests
import re
from typing import Dict, Any, Optional
from src.config import ConfigManager

logger = logging.getLogger(__name__)


class AIExtractor:
    """AI信息提取器"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化AI提取器"""
        self.config = config_manager or ConfigManager()
        self.api_endpoints = self.config.get('api_endpoints', [])
        # 建议配置：优先使用较强的模型处理翻译和提取
        self.model_configs = [
            ("gpt-4o-mini", self.api_endpoints[0] if self.api_endpoints else "https://api.gptgod.online/v1/chat/completions"),
            ("gpt-3.5-turbo", self.api_endpoints[0] if self.api_endpoints else "https://api.gptgod.online/v1/chat/completions"),
            ("deepseek-chat", self.api_endpoints[2] if len(self.api_endpoints) > 2 else "https://api.deepseek.com/v1/chat/completions")
        ]
        self.request_delay = self.config.get('request_delay', 1.0)
        self.max_retries_per_config = 3
    
    def build_extraction_prompt(self, abstract_text: str, title: str = None) -> str:
        """构建包含标题翻译的AI提取提示词"""
        # 使用 json.dumps 确保标题中的引号等特殊字符被正确转义，避免破坏 Prompt 结构
        safe_title = title if title else "未提供标题"
        
        return f"""
请分析以下英文学术文献的标题和摘要，并提取相关信息。

**文献标题：**
{safe_title}

**摘要原文：**
{abstract_text}

**任务要求：**

1. **翻译标题**：将英文标题翻译成专业的中文标题。
   - 必须准确、学术、通顺。
   - 如果未提供标题，请填"无标题"。

2. **提取摘要信息**：从摘要中提取以下信息（如果未提及请标注"未明确说明"）：
   - **研究对象**：人群特征（如：18-65岁健康成年人，黑人，白人，高加索人，老年人等等，可以是多种人口学描述）。
   - **样本量**：参与者数量（如：120名参与者）。
   - **推荐补充剂量/用法**：(重中之重的内容！！如：每日30ml MCT油；摘要仅报告含中链甘油三酯的餐相比含长链甘油三酯的餐产热更高，但未给出剂量或用法;
等能量极低热量饮食（每份578.5 kcal）的配方食物（Adinax）中使用中链甘油三酯，配方中MCT含量为每100克Adinax含8.0克，干预持续4周;
研究中测试早餐为3.3兆焦，含52克脂质（占能量的58%），中链脂肪酸来源为椰子油；为单次餐饮干预，未提供长期补充方案;
能量和长链脂肪酸限制，富含中链脂肪酸和碳水化合物的饮食，夜间添加生玉米淀粉;等等；多思考一下，有时不是非常明显)。
   - **作用机理**：(多考虑生化方面的描述，如：通过生酮作用促进脂肪燃烧)。
   - **摘要主要内容**：1-2句话概括重点。
   - **结论摘要**：核心结论（**必须中文**）。
   - **国家**：仅国家名称（如：美国、中国），不含城市。
   - **数据收集年份**：具体年份范围，非发表年份。

**请严格按照以下JSON格式直接返回结果（不要包含Markdown代码块标记）：**

{{
  "翻译标题": "这里填入翻译后的中文标题",
  "研究对象": "内容...",
  "样本量": "内容...", 
  "推荐补充剂量/用法": "内容...",
  "作用机理": "内容...",
  "摘要主要内容": "内容...",
  "结论摘要": "内容...",
  "国家": "内容...",
  "数据收集年份": "内容..."
}}
"""
# 注意：我在JSON示例中去掉了 "原文标题"，因为我们已经有这个数据了，不需要AI重复，节省Token并减少错误。

    def extract_with_retry(self, api_key: str, api_base_url: str, model_name: str, prompt: str, max_retries: int = 3) -> Optional[Dict[str, str]]:
        """带重试机制的API调用"""
        # 移除search_status检查，避免在测试环境中出现问题
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "你是一个专业的医学文献分析助手，请只返回合法的JSON数据。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.1,
            # 强制让模型返回 JSON 模式 (部分模型支持)
            "response_format": {"type": "json_object"} 
        }
        
        for attempt in range(max_retries):
            logger.debug(f"第 {attempt + 1} 次尝试调用 API: {model_name} at {api_base_url}")
            
            try:
                time.sleep(self.request_delay)
                
                # 确保API端点有效
                if not api_base_url or not api_base_url.startswith('http'):
                    logger.error(f"API端点无效: {api_base_url}")
                    continue
                
                # 确保API密钥有效
                if not api_key or api_key == 'default':
                    logger.error("API密钥无效")
                    continue
                    
                # 如果是某些不支持 response_format 的旧模型接口，可能需要移除该字段
                response = None
                try:
                    logger.debug(f"发送API请求到 {api_base_url}，模型: {model_name}")
                    response = requests.post(api_base_url, headers=headers, json=payload, timeout=20)
                    logger.debug(f"API响应状态码: {response.status_code}")
                    logger.debug(f"API响应内容: {response.text[:300]}...")
                except requests.exceptions.ConnectionError:
                    logger.error(f"无法连接到API端点: {api_base_url}")
                    # 如果请求失败，尝试移除 response_format 再次请求 (兼容性处理)
                    if "response_format" in payload:
                        del payload["response_format"]
                        try:
                            logger.debug(f"移除response_format后再次尝试请求")
                            response = requests.post(api_base_url, headers=headers, json=payload, timeout=20)
                            logger.debug(f"移除response_format后响应状态码: {response.status_code}")
                        except requests.exceptions.ConnectionError:
                            logger.error(f"移除response_format后仍无法连接到API端点: {api_base_url}")
                            continue
                    else:
                        continue
                except requests.exceptions.Timeout:
                    logger.error(f"API请求超时: {api_base_url}")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.error(f"API请求异常: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

                if response is None:
                    continue
                    
                if response.status_code == 200:
                    try:
                        result = response.json()
                        ai_content = result['choices'][0]['message']['content']
                        logger.debug(f"AI响应内容: {ai_content[:300]}...")
                        
                        # 更加鲁棒的 JSON 提取逻辑
                        try:
                            # 尝试直接解析
                            return self._parse_json(ai_content)
                        except json.JSONDecodeError:
                            # 如果失败，尝试提取代码块 ```json ... ``` 或 { ... }
                            json_match = re.search(r'\{.*\}', ai_content, re.DOTALL)
                            if json_match:
                                return self._parse_json(json_match.group(0))
                            else:
                                logger.warning(f"无法从响应中提取JSON: {ai_content[:100]}...")
                                continue
                    except Exception as e:
                        logger.error(f"处理AI响应时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                        
                elif response.status_code == 429:
                    wait_time = self.request_delay * (2 ** attempt)
                    logger.warning(f"请求频率过高，等待{wait_time}秒后重试")
                    time.sleep(wait_time)
                    continue
                elif response.status_code in [401, 403]:
                    logger.error(f"API密钥无效或权限不足，状态码: {response.status_code}")
                    logger.error(f"错误响应: {response.text[:200]}...")
                    return None
                elif response.status_code >= 500:
                    logger.error(f"API服务器错误，状态码: {response.status_code}")
                    logger.error(f"错误响应: {response.text[:200]}...")
                    # 服务器错误，继续重试
                    continue
                else:
                    logger.error(f"API请求失败，状态码: {response.status_code}")
                    logger.error(f"错误响应: {response.text[:200]}...")
                    continue
                    
            except Exception as e:
                logger.error(f"提取过程错误: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.request_delay)
                continue
        
        return None
    
    def _parse_json(self, json_str: str) -> Dict[str, str]:
        """内部JSON解析辅助函数"""
        data = json.loads(json_str)
        return self.validate_extracted_data(data)

    def validate_extracted_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """验证和清理提取的数据"""
        validated = {}
        
        # 定义字段映射，处理AI可能返回的异形Key
        key_mapping = {
            "翻译标题": ["翻译标题", "中文标题", "Translated Title", "title_cn"],
            "研究对象": ["研究对象", "Subjects", "Participants"],
            "样本量": ["样本量", "Sample Size"],
            "推荐补充剂量/用法": ["推荐补充剂量/用法", "Dosage", "补充剂量"],
            "作用机理": ["作用机理", "Mechanism"],
            "摘要主要内容": ["摘要主要内容", "Summary", "Main Content"],
            "结论摘要": ["结论摘要", "Conclusion"],
            "国家": ["国家", "Country"],
            "数据收集年份": ["数据收集年份", "Year", "Data Collection Year"]
        }

        for target_key, possible_keys in key_mapping.items():
            value = "未明确说明"
            # 尝试所有可能的Key
            for k in possible_keys:
                if k in data and data[k]:
                    val = data[k]
                    if isinstance(val, str) and val.strip() and val.lower() not in ["null", "none", "n/a"]:
                        value = val.strip()
                        break
            validated[target_key] = value

        # 特殊处理：如果翻译标题失败，暂时标记，稍后在主函数用原文填充或重试
        if validated["翻译标题"] == "未明确说明":
             validated["翻译标题"] = "翻译失败"

        return validated
    
    def get_fallback_data_with_title(self, title: str = None) -> Dict[str, str]:
        """备用数据"""
        return {
            "原文标题": title if title else "无标题",
            "翻译标题": "翻译失败", # 当AI翻译失败时，使用明确的默认值
            "研究对象": "需人工确认",
            "样本量": "需人工确认", 
            "推荐补充剂量/用法": "需人工确认",
            "作用机理": "需人工确认",
            "摘要主要内容": "需人工确认",
            "结论摘要": "需人工确认",
            "国家": "需人工确认",
            "数据收集年份": "需人工确认"
        }
    
    def extract_info_with_ai(self, abstract_text: str, title: str = None, api_key_pool=None) -> Dict[str, str]:
        """主入口函数"""
        if not abstract_text or abstract_text.strip() == "":
            return self.get_fallback_data_with_title(title)
        
        # 1. 构建 Prompt
        prompt = self.build_extraction_prompt(abstract_text, title)
        
        print("  🤖 AI模型开始分析...")
        logger.debug(f"使用的提示词: {prompt[:300]}...")
        
        # 2. 遍历模型尝试提取
        for model_name, api_base_url in self.model_configs:
            logger.debug(f"尝试使用模型: {model_name}, URL: {api_base_url}")
            # 确定模型对应的API类型
            api_type = 'deepseek' if 'deepseek' in model_name else 'openai'
            
            for attempt in range(self.max_retries_per_config):
                logger.debug(f"第 {attempt + 1}/{self.max_retries_per_config} 次尝试")
                
                # 根据模型类型获取对应API密钥
                current_api_key = None
                try:
                    if api_key_pool:
                        # 从密钥池获取对应类型的密钥（假设密钥池支持按类型分配）
                        current_api_key = api_key_pool.get_available_key()
                        logger.debug(f"从密钥池获取{api_type}密钥: {current_api_key[:10]}...")
                    else:
                        # 从配置获取对应类型的密钥
                        # 优先使用模型专用密钥池，不存在则回退到通用密钥池
                        api_keys = self.config.get(f'api_keys_{api_type}', 
                                                self.config.get('api_keys_pool', ['default']))
                        current_api_key = api_keys[0] if api_keys else 'default'
                        logger.debug(f"从配置获取{api_type}密钥: {current_api_key[:10]}...")
                except Exception as e:
                    logger.error(f"获取{api_type}密钥时出错: {e}")
                    continue
                
                # 确保API密钥有效
                if not current_api_key or current_api_key == 'default':
                    logger.error("API密钥无效")
                    continue
                
                extracted_data = self.extract_with_retry(current_api_key, api_base_url, model_name, prompt)
                
                if extracted_data:
                    # === 关键修正：在此处强制合并原文标题 ===
                    # 我们不信任AI返回的"原文标题"，直接使用传入的 title
                    extracted_data["原文标题"] = title if title else "无标题"
                    
                    # 保留翻译标题为AI返回的结果，如果AI翻译失败，保持"翻译失败"的状态
                    # 不再将翻译标题替换为原文标题

                    if api_key_pool:
                        api_key_pool.report_success(current_api_key)
                    logger.info(f"成功提取信息: {model_name}")
                    return extracted_data
                else:
                    logger.debug(f"使用模型 {model_name} 提取失败")
                    if api_key_pool:
                        api_key_pool.report_failure(current_api_key, "failed")
        
        logger.warning("所有AI提取尝试均失败")
        return self.get_fallback_data_with_title(title)

# 全局实例
ai_extractor = AIExtractor()

def extract_info_with_ai(abstract_text: str, title: str = None) -> Dict[str, str]:
    return ai_extractor.extract_info_with_ai(abstract_text, title)