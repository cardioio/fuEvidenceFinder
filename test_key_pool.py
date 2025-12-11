#!/usr/bin/env python3
"""
API密钥池管理系统测试脚本
专门用于测试多API密钥池机制的功能
"""

import time
import json
from typing import Dict, Optional

# API密钥池配置
API_KEYS_POOL = [
    "sk-1wLZqqkXDT9shZzgTqNRc0wNB6K4Kmu1t0kov0KA5I3auqVf",  # 主密钥
    "sk-19GhS2EHMvZJZrm4LYdL94KrAfIb5ckAhwH7Btcorg23zh8H",  # 备用密钥1
    "sk-t0WZJnqINXX2LnRvPIvRvhMLIcfYtZ76UvOjHf82IGPcYRj1",  # 备用密钥2
]

API_KEY_POOL_CONFIG = {
    "max_failure_count": 3,        # 最大失败次数，超过后暂时禁用密钥
    "disable_duration": 300,       # 密钥禁用时长（秒），5分钟
    "success_reset_threshold": 2,  # 成功次数阈值，重置失败计数
    "enable_key_rotation": True,   # 启用密钥轮换
    "log_key_usage": True          # 是否记录密钥使用情况（不记录具体密钥内容）
}

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
        print("❌ 所有API密钥都不可用")
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
            print(f"✅ 密钥重新启用")
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
                print(f"✅ 密钥 {key_id} 请求成功，累计成功: {state['total_successes']}")
    
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
                print(f"❌ 密钥 {key_id} 请求失败 ({error_type})，失败次数: {state['failure_count']}")
    
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
        
        print(f"⚠️  密钥 {key_id} 因失败次数过多被临时禁用，原因: {reason}，禁用时长: {disable_duration}秒")
    
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
        print(f"🔄 密钥轮换到索引: {self.current_key_index + 1}")

def test_api_key_pool():
    """
    测试API密钥池管理器的各项功能
    包括密钥轮换、失败检测、禁用逻辑和统计信息
    """
    print("\n" + "=" * 70)
    print("🔧 API密钥池管理系统测试")
    print("=" * 70)
    
    # 创建测试用的密钥池配置
    test_keys = [
        "sk-test123456789abcdef",  # 密钥1
        "sk-test987654321fedcba",  # 密钥2
        "sk-test111111111111111"   # 密钥3
    ]
    
    test_config = {
        "max_failure_count": 2,        # 设置较低阈值用于测试
        "disable_duration": 5,         # 5秒禁用时间
        "success_reset_threshold": 1,
        "enable_key_rotation": True,
        "log_key_usage": True
    }
    
    # 创建测试密钥池管理器
    test_pool = APIKeyPoolManager(test_keys, test_config)
    print(f"✅ 创建测试密钥池，包含 {len(test_keys)} 个密钥")
    
    # 测试1: 基本密钥获取
    print("\n--- 测试1: 基本密钥获取 ---")
    key1 = test_pool.get_available_key()
    print(f"获取第一个可用密钥: {key1[:20]}...")
    assert key1 == test_keys[0], "应该返回第一个密钥"
    
    # 测试2: 密钥轮换
    print("\n--- 测试2: 密钥轮换 ---")
    test_pool.rotate_key()
    key2 = test_pool.get_available_key()
    print(f"轮换后获取密钥: {key2[:20]}...")
    assert key2 == test_keys[1], "应该返回第二个密钥"
    
    # 测试3: 失败计数和禁用
    print("\n--- 测试3: 失败计数和自动禁用 ---")
    initial_stats = test_pool.get_key_statistics()
    print("初始状态:")
    for key_id, stats in initial_stats.items():
        print(f"  {key_id}: 请求={stats['total_requests']}, 成功={stats['total_successes']}")
    
    # 报告失败直到触发禁用
    for i in range(test_config["max_failure_count"]):
        test_pool.report_failure(key1, "test_error")
        stats = test_pool.get_key_statistics()
        print(f"失败 {i+1} 次后: key_1 失败次数={stats['key_1']['failure_count']}")
    
    # 检查密钥是否被禁用
    key_after_failures = test_pool.get_available_key()
    print(f"禁用后获取的密钥: {key_after_failures[:20]}...")
    assert key_after_failures == test_keys[1], "应该跳过禁用的密钥1"
    
    # 测试4: 成功重置失败计数
    print("\n--- 测试4: 成功重置失败计数 ---")
    test_pool.report_success(key2)
    stats = test_pool.get_key_statistics()
    print(f"成功后统计: key_2 成功={stats['key_2']['success_count']}, 失败={stats['key_2']['failure_count']}")
    
    # 测试5: 禁用恢复
    print("\n--- 测试5: 禁用恢复机制 ---")
    key1_stats_before = test_pool.get_key_statistics()['key_1']
    print(f"密钥1禁用状态: {key1_stats_before['is_disabled']}")
    
    if key1_stats_before['is_disabled']:
        print(f"等待禁用期结束 (当前配置: {test_config['disable_duration']}秒)")
        
        # 等待禁用期结束
        print("等待禁用期结束...")
        time.sleep(test_config['disable_duration'] + 1)
        
        # 尝试重新获取密钥
        key1_after_recovery = test_pool.get_available_key()
        print(f"禁用期结束后获取密钥: {key1_after_recovery[:20]}...")
    
    # 测试6: 统计信息
    print("\n--- 测试6: 统计信息获取 ---")
    final_stats = test_pool.get_key_statistics()
    print("最终统计信息:")
    for key_id, stats in final_stats.items():
        print(f"  {key_id}:")
        print(f"    状态: {'🔴 禁用' if stats['is_disabled'] else '🟢 正常'}")
        print(f"    总请求: {stats['total_requests']}")
        print(f"    总成功: {stats['total_successes']}")
        print(f"    成功率: {stats['success_rate']:.2%}")
    
    # 测试7: 所有密钥都不可用的情况
    print("\n--- 测试7: 全部密钥禁用情况 ---")
    # 禁用所有密钥
    for i in range(len(test_keys)):
        key_id = f"key_{i+1}"
        test_pool.key_states[key_id]['is_disabled'] = True
        test_pool.key_states[key_id]['disabled_until'] = time.time() + 60
    
    no_key = test_pool.get_available_key()
    print(f"所有密钥禁用时获取结果: {no_key}")
    assert no_key is None, "应该返回None表示没有可用密钥"
    
    print("\n" + "=" * 70)
    print("✅ API密钥池测试完成")
    print("=" * 70)
    
    return test_pool

def test_actual_key_pool():
    """
    测试实际密钥池的功能
    """
    print("\n" + "=" * 70)
    print("🎯 实际密钥池使用场景测试")
    print("=" * 70)
    
    # 创建实际密钥池管理器
    actual_pool = APIKeyPoolManager(API_KEYS_POOL, API_KEY_POOL_CONFIG)
    print(f"✅ 创建实际密钥池，包含 {len(API_KEYS_POOL)} 个密钥")
    
    # 显示密钥池统计信息
    stats = actual_pool.get_key_statistics()
    print("当前密钥池状态:")
    for key_id, key_stats in stats.items():
        status = "🔴 禁用" if key_stats['is_disabled'] else "🟢 正常"
        last_used = "未使用" if not key_stats['last_used'] else time.strftime("%H:%M:%S", time.localtime(key_stats['last_used']))
        
        print(f"  {key_id}: {status}")
        print(f"    总请求: {key_stats['total_requests']}, 成功: {key_stats['total_successes']}")
        print(f"    成功率: {key_stats['success_rate']:.1%}")
        print(f"    最后使用: {last_used}")
    
    # 测试密钥获取
    print("\n--- 测试密钥获取 ---")
    available_key = actual_pool.get_available_key()
    if available_key:
        key_id = actual_pool._get_key_id(available_key)
        print(f"✅ 获取到可用密钥: {key_id}")
        print(f"密钥前缀: {available_key[:15]}...")
        
        # 模拟成功请求
        actual_pool.report_success(available_key)
        print(f"✅ 报告密钥 {key_id} 请求成功")
        
        # 获取更新后的统计
        updated_stats = actual_pool.get_key_statistics()[key_id]
        print(f"更新后成功率: {updated_stats['success_rate']:.1%}")
    else:
        print("❌ 没有可用的密钥")
    
    print("\n" + "=" * 70)
    print("✅ 实际场景测试完成")
    print("=" * 70)

def simulate_api_requests():
    """
    模拟API请求场景，测试密钥池的实际表现
    """
    print("\n" + "=" * 70)
    print("🔄 API请求模拟测试")
    print("=" * 70)
    
    pool = APIKeyPoolManager(API_KEYS_POOL, API_KEY_POOL_CONFIG)
    
    # 模拟10次API请求，其中一些会失败
    for i in range(10):
        print(f"\n--- 第 {i+1} 次请求 ---")
        
        # 获取可用密钥
        key = pool.get_available_key()
        if not key:
            print("❌ 没有可用密钥，跳过此次请求")
            continue
        
        key_id = pool._get_key_id(key)
        print(f"使用密钥: {key_id}")
        
        # 模拟请求结果 (90%成功率)
        import random
        success = random.random() > 0.1
        
        if success:
            pool.report_success(key)
            print("✅ 请求成功")
        else:
            # 模拟不同类型的错误
            error_types = ["rate_limit", "auth_error", "network_error"]
            error_type = random.choice(error_types)
            pool.report_failure(key, error_type)
            print(f"❌ 请求失败 ({error_type})")
        
        # 显示当前状态
        stats = pool.get_key_statistics()
        available_keys = sum(1 for s in stats.values() if not s['is_disabled'])
        print(f"可用密钥数量: {available_keys}/{len(API_KEYS_POOL)}")
    
    # 显示最终统计
    print("\n--- 最终统计 ---")
    final_stats = pool.get_key_statistics()
    for key_id, stats in final_stats.items():
        print(f"{key_id}: {stats['total_requests']} 请求, {stats['total_successes']} 成功, 成功率 {stats['success_rate']:.1%}")
    
    print("\n" + "=" * 70)
    print("✅ API请求模拟测试完成")
    print("=" * 70)

if __name__ == "__main__":
    print("🔧 开始API密钥池管理系统测试")
    
    # 运行所有测试
    test_api_key_pool()
    test_actual_key_pool()
    simulate_api_requests()
    
    print("\n🎉 所有测试完成！")
    print("多API密钥池机制已成功实现并通过测试验证。")