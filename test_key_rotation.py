#!/usr/bin/env python3
"""
测试API密钥轮询功能的验证脚本
验证三个API密钥的轮询查询、负载均衡和故障转移功能
"""

import sys
import time
from pubmed import APIKeyPoolManager, API_KEYS_POOL, API_KEY_POOL_CONFIG

def test_key_rotation():
    """测试API密钥轮询功能"""
    print("🔍 开始测试API密钥轮询功能")
    print("=" * 60)
    
    # 创建密钥池管理器实例
    pool = APIKeyPoolManager(API_KEYS_POOL, API_KEY_POOL_CONFIG)
    
    print(f"✅ 创建密钥池管理器，包含 {len(API_KEYS_POOL)} 个API密钥")
    print(f"📋 密钥配置: {API_KEY_POOL_CONFIG}")
    print()
    
    # 1. 测试密钥获取功能
    print("1️⃣ 测试密钥获取功能:")
    for i in range(6):  # 获取6次密钥，验证轮询
        key = pool.get_available_key()
        key_id = pool._get_key_id(key) if key else None
        print(f"   第{i+1}次获取: {key_id} (密钥前8位: {key[:8] if key else 'None'}...)")
        if key:
            pool.report_success(key)
        time.sleep(0.1)
    print()
    
    # 2. 测试密钥状态统计
    print("2️⃣ 测试密钥状态统计:")
    stats = pool.get_key_statistics()
    for key_id, state in stats.items():
        print(f"   {key_id}:")
        print(f"     - 总请求数: {state['total_requests']}")
        print(f"     - 成功次数: {state['total_successes']}")
        print(f"     - 成功率: {state['success_rate']:.2%}")
        print(f"     - 是否禁用: {state['is_disabled']}")
        print(f"     - 失败次数: {state['failure_count']}")
    print()
    
    # 3. 测试故障转移功能
    print("3️⃣ 测试故障转移功能:")
    key = pool.get_available_key()
    key_id = pool._get_key_id(key) if key else None
    print(f"   获取密钥: {key_id}")
    
    # 模拟多次失败，触发密钥禁用
    for i in range(3):
        print(f"   模拟第{i+1}次失败...")
        pool.report_failure(key, "test_error")
    
    # 检查密钥是否被禁用
    updated_stats = pool.get_key_statistics()
    if key_id and updated_stats[key_id]['is_disabled']:
        print(f"   ✅ {key_id} 已成功禁用 (失败次数: {updated_stats[key_id]['failure_count']})")
        
        # 验证系统自动切换到下一个可用密钥
        next_key = pool.get_available_key()
        next_key_id = pool._get_key_id(next_key) if next_key else None
        if next_key_id != key_id:
            print(f"   ✅ 故障转移成功: 切换到 {next_key_id}")
        else:
            print(f"   ❌ 故障转移失败: 仍然返回 {key_id}")
    else:
        print(f"   ❌ 密钥禁用测试失败")
    print()
    
    # 4. 测试负载均衡
    print("4️⃣ 测试负载均衡功能:")
    # 重置所有密钥状态
    pool.key_states = {}
    for i, key in enumerate(API_KEYS_POOL):
        key_id = f"key_{i+1}"
        pool.key_states[key_id] = {
            "key": key,
            "failure_count": 0,
            "success_count": 0,
            "is_disabled": False,
            "disabled_until": None,
            "last_used": None,
            "total_requests": 0,
            "total_successes": 0
        }
    
    # 模拟10次请求，观察负载分布
    key_usage = {}
    for i in range(10):
        key = pool.get_available_key()
        if key:
            key_id = pool._get_key_id(key)
            key_usage[key_id] = key_usage.get(key_id, 0) + 1
            pool.report_success(key)
    
    print("   负载分布统计:")
    for key_id, count in key_usage.items():
        print(f"     {key_id}: {count} 次使用")
    print()
    
    # 5. 测试密钥重新启用
    print("5️⃣ 测试密钥重新启用功能:")
    # 禁用一个密钥
    key = pool.get_available_key()
    key_id = pool._get_key_id(key) if key else None
    if key_id:
        print(f"   禁用密钥: {key_id}")
        # 模拟3次失败来禁用密钥
        for _ in range(3):
            pool.report_failure(key, "test_error")
        
        # 立即检查应该显示禁用
        stats_before = pool.get_key_statistics()
        print(f"   禁用后状态: {stats_before[key_id]['is_disabled']}")
        
        # 模拟时间跳跃（实际应用中需要等待disable_duration）
        print(f"   模拟时间跳跃到密钥重新启用...")
        pool.key_states[key_id]['disabled_until'] = time.time() - 1  # 设置为已过期
        
        # 再次获取密钥
        re_enabled_key = pool.get_available_key()
        re_enabled_key_id = pool._get_key_id(re_enabled_key) if re_enabled_key else None
        
        if re_enabled_key_id == key_id:
            print(f"   ✅ 密钥重新启用成功: {key_id}")
        else:
            print(f"   ❌ 密钥重新启用失败: 期望 {key_id}，得到 {re_enabled_key_id}")
    
    print("\n" + "=" * 60)
    print("🎉 API密钥轮询功能测试完成!")
    
    # 最终统计
    final_stats = pool.get_key_statistics()
    print("\n📊 最终统计:")
    total_requests = sum(stat['total_requests'] for stat in final_stats.values())
    total_successes = sum(stat['total_successes'] for stat in final_stats.values())
    print(f"   总请求数: {total_requests}")
    print(f"   总成功数: {total_successes}")
    print(f"   整体成功率: {total_successes/max(1,total_requests):.2%}")

if __name__ == "__main__":
    test_key_rotation()