#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量训练脚本：从 seq_len=1 开始，每次 +1，自动提交训练任务
彩种：大乐透 (dlt)
参数：最优配置（epochs=200, batch_size=128, lr=0.00005）
特性：请求失败时自动重试（最多3次）
"""

import time
import requests
import json
import csv

BASE_URL = "http://localhost:8000"
MAX_RETRIES = 3                 # 最大重试次数
RETRY_DELAY = 2                 # 重试间隔（秒）
REQUEST_TIMEOUT = 30            # 请求超时时间（秒）

# ==================== 配置参数（最优精度） ====================
lottery_type = "dlt"                # 彩种：大乐透
epochs = 200                        # 训练轮数（最优）
batch_size = 128                    # 批次大小（最优）
learning_rate = 0.00005             # 学习率（最优）
with_fetch = False                  # 不抓取数据（数据已存在）

seq_len_start = 1
seq_len_end = 2887                  # 最大序列长度（大乐透总期数约2887）

# ==================== 提交任务函数（带重试） ====================
def submit_task(seq_len):
    """提交单个训练任务，失败时自动重试"""
    payload = {
        "lottery_type": lottery_type,
        "epochs": epochs,
        "batch_size": batch_size,
        "seq_len": seq_len,
        "learning_rate": learning_rate,
        "with_fetch": with_fetch
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{BASE_URL}/train/start",
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                data = resp.json()
                task_id = data.get("task_id")
                print(f"   ✅ 任务已提交: {task_id}")
                return task_id
            else:
                print(f"   ⚠️ 提交失败 (状态码 {resp.status_code})，尝试 {attempt}/{MAX_RETRIES}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️ 请求异常: {e}，尝试 {attempt}/{MAX_RETRIES}")

        # 最后一次重试失败则放弃
        if attempt == MAX_RETRIES:
            print(f"   ❌ 放弃 seq_len={seq_len}（已达最大重试次数）")
            return None

        time.sleep(RETRY_DELAY)

# ==================== 开始提交任务 ====================
print("=" * 60)
print("🚀 大乐透批量训练（最优配置）")
print(f"   彩种: {lottery_type}")
print(f"   训练轮数: {epochs}")
print(f"   批次大小: {batch_size}")
print(f"   学习率: {learning_rate}")
print(f"   序列长度范围: {seq_len_start} ~ {seq_len_end}")
print(f"   最大重试次数: {MAX_RETRIES}")
print("=" * 60)
print("⚠️  警告：将提交 2887 个训练任务，耗时可能长达数天！")
confirm = input("是否继续？(输入 y 继续): ")
if confirm.lower() != 'y':
    print("已取消。")
    exit(0)

tasks = []

for seq_len in range(seq_len_start, seq_len_end + 1):
    print(f"\n📤 提交训练任务: seq_len={seq_len}")
    task_id = submit_task(seq_len)
    if task_id:
        tasks.append({
            "seq_len": seq_len,
            "task_id": task_id,
            "status": "pending"
        })
    else:
        tasks.append({
            "seq_len": seq_len,
            "task_id": None,
            "status": "failed_submit"
        })

    # 每次提交后短暂延时，避免服务器过载
    time.sleep(0.5)

# ==================== 等待所有任务完成 ====================
print(f"\n📊 共提交 {len(tasks)} 个训练任务，等待完成...")

for task in tasks:
    seq_len = task["seq_len"]
    task_id = task["task_id"]
    if task_id is None:
        continue

    while True:
        try:
            resp = requests.get(f"{BASE_URL}/train/status/{task_id}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")
                if status in ["completed", "failed", "SUCCESS", "FAILURE"]:
                    task["status"] = status
                    if status in ["completed", "SUCCESS"]:
                        result = data.get("result", {})
                        final_loss = result.get("final_loss", "N/A")
                        print(f"   seq_len={seq_len:3d} ✅ 完成, loss={final_loss}")
                        task["result"] = result
                    else:
                        print(f"   seq_len={seq_len:3d} ❌ 失败: {data.get('result', '')}")
                    break
            time.sleep(5)
        except Exception as e:
            print(f"   seq_len={seq_len:3d} 查询异常: {e}")
            time.sleep(5)

# ==================== 输出汇总 ====================
print("\n" + "=" * 60)
print("📊 训练结果汇总")
print("=" * 60)
print(f"{'seq_len':>10} | {'status':>15} | {'final_loss':>12}")
print("-" * 45)
for task in tasks:
    seq_len = task["seq_len"]
    status = task["status"]
    loss = task.get("result", {}).get("final_loss", "N/A") if status in ["completed", "SUCCESS"] else "N/A"
    print(f"{seq_len:>10} | {status:>15} | {str(loss):>12}")
print("=" * 60)

# 保存结果到 CSV
with open("batch_train_results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["seq_len", "status", "final_loss"])
    for task in tasks:
        seq_len = task["seq_len"]
        status = task["status"]
        loss = task.get("result", {}).get("final_loss", "") if status in ["completed", "SUCCESS"] else ""
        writer.writerow([seq_len, status, loss])
print("📁 结果已保存到 batch_train_results.csv")