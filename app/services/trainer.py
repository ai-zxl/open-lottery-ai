# -*- coding: utf-8 -*-
"""
训练器模块：使用历史数据训练 Transformer 模型，并保存模型和标准化参数。
支持双色球 (ssq) 和大乐透 (dlt) 两种彩种。
"""
import os
import joblib
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler

from .data_loader import load_ssq_data_sync, load_dlt_data_sync
from .transformer_model import LotteryTransformer
from app.core.config import settings


def train_lottery_model(lottery_type, epochs=50, batch_size=32, seq_len=30, lr=1e-4):
    """
    训练指定彩种的预测模型。

    Args:
        lottery_type (str): 彩种标识，'ssq' 或 'dlt'
        epochs (int): 训练轮数
        batch_size (int): 批次大小
        seq_len (int): 序列长度（使用多少期历史数据预测下一期）
        lr (float): 学习率

    Returns:
        dict: 包含模型路径、最终损失等信息
    """
    # ---------- 1. 加载数据（同步） ----------
    print(f"📊 开始加载 {lottery_type} 历史数据...")
    if lottery_type == 'ssq':
        df = load_ssq_data_sync()
    else:  # lottery_type == 'dlt'
        df = load_dlt_data_sync()

    if df is None or len(df) < seq_len + 1:
        raise ValueError(
            f"数据量不足，需要至少 {seq_len + 1} 条记录，"
            f"当前仅有 {len(df) if df is not None else 0} 条"
        )
    print(f"✅ 数据加载完成，共 {len(df)} 条记录")

    # ---------- 2. 标准化特征和目标 ----------
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df.values)

    # ---------- 3. 构造序列样本 ----------
    X, y = [], []
    for i in range(len(scaled) - seq_len):
        X.append(scaled[i:i + seq_len])
        y.append(scaled[i + seq_len])
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)

    output_dim = 7
    y_target = y[:, -output_dim:]

    dataset = TensorDataset(torch.tensor(X), torch.tensor(y_target))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # ---------- 4. 初始化模型 ----------
    input_dim = df.shape[1]
    model = LotteryTransformer(
        input_dim=input_dim,
        d_model=128,
        nhead=4,
        num_layers=3,
        output_dim=output_dim
    )

    device = torch.device(settings.DEVICE if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"💻 训练设备: {device}")

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    # ---------- 5. 训练循环 ----------
    print(f"🚀 开始训练 {lottery_type} 模型，共 {epochs} 轮...")
    for epoch in range(epochs):
        total_loss = 0.0
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)

            optimizer.zero_grad()
            pred = model(batch_x)
            loss = criterion(pred, batch_y)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"  Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")

    print("✅ 训练完成！")

    # ---------- 6. 保存模型和标准化器 ----------
    save_dir = settings.MODEL_SAVE_DIR
    os.makedirs(save_dir, exist_ok=True)

    import time
    param_str = f"epochs{epochs}_bs{batch_size}_seq{seq_len}_lr{str(lr).replace('.', '_')}"
    timestamp = int(time.time())
    run_id = f"{lottery_type}_{param_str}_{timestamp}"

    # 1. 保存带参数的模型（历史保留）
    model_filename = f"{run_id}.pt"
    scaler_filename = f"{run_id}_scaler.joblib"
    model_path = os.path.join(save_dir, model_filename)
    scaler_path = os.path.join(save_dir, scaler_filename)

    torch.save(model.state_dict(), model_path)
    joblib.dump(scaler, scaler_path)

    # 2. 同时覆盖 final 版本（供预测使用）
    final_model_path = os.path.join(save_dir, f"{lottery_type}_final.pt")
    final_scaler_path = os.path.join(save_dir, f"{lottery_type}_scaler.joblib")
    torch.save(model.state_dict(), final_model_path)
    joblib.dump(scaler, final_scaler_path)

    print(f"💾 模型已保存至: {model_path}")
    print(f"💾 标准化器已保存至: {scaler_path}")
    print(f"💾 同时覆盖了 final 版本: {final_model_path}")

    # ---------- 7. 返回训练结果 ----------
    result = {
        "model_path": model_path,
        "scaler_path": scaler_path,
        "final_model_path": final_model_path,
        "epochs": epochs,
        "final_loss": avg_loss,
        "lottery_type": lottery_type,
        "device": str(device),
        "run_id": run_id
    }
    print(f"📊 训练结果: {result}")
    return result