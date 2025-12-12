"""
API密钥管理器
负责API密钥的动态管理、自动轮换和状态监控功能
"""

import time
import logging
from typing import Optional, Dict, Any

# 导入配置管理器
from src.config import config_manager

logger = logging.getLogger(__name__)

class APIKeyPoolManager:
    """
    API密钥池管理器 - 提供密钥的动态管理、自动轮换和状态监控功能
    """
    
    def __init__(self, api_keys: list, config: dict):
        """
        初始化API密钥池管理器
        
        Args:
            api_keys: API密钥列表
            config: 配置字典
        """
        self.api_keys = api_keys
        self.config = config
        self.current_key_index = 0
        self.key_states = {}
        
        # 初始化每个密钥的状态
        for i, key in enumerate(api_keys):
            key_id = f"key_{i+1}"  # 使用key_1, key_2等作为密钥标识符
            self.key_states[key_id] = {
                "key": key,
                "failure_count": 0,
                "success_count": 0,
                "is_disabled": False,
                "disabled_until": None,
                "last_used": None,
                "total_requests": 0,
                "total_successes": 0
            }
        
        logger.info(f"API密钥池管理器已初始化，共 {len(api_keys)} 个密钥")
    
    def get_available_key(self) -> Optional[str]:
        """
        获取下一个可用的API密钥
        
        Returns:
            可用的API密钥，如果所有密钥都不可用则返回None
        """
        if not self.config.get("enable_key_rotation", True):
            return self.api_keys[0] if self.api_keys else None
            
        attempts = 0
        max_attempts = len(self.api_keys)
        
        while attempts < max_attempts:
            key_id = f"key_{self.current_key_index + 1}"
            state = self.key_states[key_id]
            
            # 检查密钥是否被禁用
            if self._is_key_disabled(state):
                # 尝试下一个密钥
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                attempts += 1
                continue
                
            # 密钥可用
            return state["key"]
        
        # 所有密钥都不可用
        logger.error("所有API密钥都不可用")
        return None
    
    def _is_key_disabled(self, key_state: dict) -> bool:
        """
        检查密钥是否被禁用
        
        Args:
            key_state: 密钥状态字典
            
        Returns:
            布尔值，表示密钥是否被禁用
        """
        if not key_state["is_disabled"]:
            return False
            
        # 检查禁用时间是否已过
        if key_state["disabled_until"] and time.time() > key_state["disabled_until"]:
            # 重新启用密钥
            key_state["is_disabled"] = False
            key_state["disabled_until"] = None
            logger.info(f"密钥重新启用")
            return False
            
        return True
    
    def report_success(self, key: str):
        """
        报告API请求成功
        
        Args:
            key: 使用的API密钥
        """
        key_id = self._get_key_id(key)
        if key_id and key_id in self.key_states:
            state = self.key_states[key_id]
            state["success_count"] += 1
            state["total_successes"] += 1
            state["last_used"] = time.time()
            
            # 如果有失败记录，重置失败计数
            if state["failure_count"] > 0:
                state["failure_count"] = max(0, state["failure_count"] - 1)
            
            # 记录密钥使用情况
            if self.config.get("log_key_usage", True):
                logger.debug(f"密钥 {key_id} 请求成功，累计成功: {state['total_successes']}")
    
    def report_failure(self, key: str, error_type: str = "unknown"):
        """
        报告API请求失败
        
        Args:
            key: 使用的API密钥
            error_type: 错误类型
        """
        key_id = self._get_key_id(key)
        if key_id and key_id in self.key_states:
            state = self.key_states[key_id]
            state["failure_count"] += 1
            state["total_requests"] += 1
            state["last_used"] = time.time()
            
            # 检查是否需要禁用密钥
            max_failures = self.config.get("max_failure_count", 3)
            if state["failure_count"] >= max_failures:
                self._disable_key(key_id, error_type)
            
            # 记录密钥使用情况
            if self.config.get("log_key_usage", True):
                logger.warning(f"密钥 {key_id} 请求失败 ({error_type})，失败次数: {state['failure_count']}")
    
    def _disable_key(self, key_id: str, reason: str):
        """
        禁用密钥
        
        Args:
            key_id: 密钥标识符
            reason: 禁用原因
        """
        disable_duration = self.config.get("disable_duration", 300)
        state = self.key_states[key_id]
        
        state["is_disabled"] = True
        state["disabled_until"] = time.time() + disable_duration
        
        logger.warning(f"密钥 {key_id} 因失败次数过多被临时禁用，原因: {reason}，禁用时长: {disable_duration}秒")
    
    def _get_key_id(self, key: str) -> Optional[str]:
        """
        根据密钥获取密钥标识符
        
        Args:
            key: API密钥
            
        Returns:
            密钥标识符，如果找不到返回None
        """
        for key_id, state in self.key_states.items():
            if state["key"] == key:
                return key_id
        return None
    
    def get_key_statistics(self) -> dict:
        """
        获取所有密钥的统计信息
        
        Returns:
            包含统计信息的字典
        """
        stats = {}
        for key_id, state in self.key_states.items():
            stats[key_id] = {
                "is_disabled": state["is_disabled"],
                "failure_count": state["failure_count"],
                "success_count": state["success_count"],
                "total_requests": state["total_requests"],
                "total_successes": state["total_successes"],
                "success_rate": state["total_successes"] / max(1, state["total_requests"]),
                "last_used": state["last_used"]
            }
        return stats
    
    def rotate_key(self):
        """
        轮换到下一个密钥
        """
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.debug(f"密钥轮换到索引: {self.current_key_index}")
    
    def reset_statistics(self):
        """重置所有密钥的统计信息"""
        for key_id in self.key_states:
            self.key_states[key_id] = {
                "key": self.key_states[key_id]["key"],
                "failure_count": 0,
                "success_count": 0,
                "is_disabled": False,
                "disabled_until": None,
                "last_used": None,
                "total_requests": 0,
                "total_successes": 0
            }
        logger.info("所有密钥统计信息已重置")
    
    def get_healthy_keys(self) -> list:
        """
        获取健康的密钥列表（未被禁用的密钥）
        
        Returns:
            健康密钥的列表
        """
        healthy_keys = []
        for key_id, state in self.key_states.items():
            if not self._is_key_disabled(state):
                healthy_keys.append(state["key"])
        return healthy_keys
    
    def enable_all_keys(self):
        """重新启用所有密钥"""
        for key_id in self.key_states:
            self.key_states[key_id]["is_disabled"] = False
            self.key_states[key_id]["disabled_until"] = None
        logger.info("所有密钥已重新启用")

# 创建全局API密钥池管理器实例
def create_api_key_pool():
    """创建全局API密钥池管理器实例"""
    api_config = config_manager.get_api_config()
    return APIKeyPoolManager(
        api_config["keys_pool"],
        api_config["pool_config"]
    )

# 全局实例
api_key_pool = create_api_key_pool()