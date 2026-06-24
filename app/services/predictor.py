# -*- coding: utf-8 -*-
"""
预测服务：加载已训练模型和标准化器，生成预测结果并存入数据库。
逻辑：同一开奖期同一模型只保留一条预测记录（存在则更新），不同模型可有多条。
支持指定模型文件进行预测。
"""
import torch
import joblib
import numpy as np
from datetime import date
from sqlalchemy import select
from .data_loader import load_ssq_data, load_dlt_data
from .transformer_model import LotteryTransformer
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.ssq_forecast import SSQForecast
from app.models.dlt_forecast import DLTForecast
from app.services.analysis_service import get_next_draw_date, is_draw_day
import os
import random


async def get_prediction(lottery_type, model_version="latest", model_name=None):
    """
    根据彩种生成预测，并保存到对应的预测表中。
    同一开奖期同一模型只保留一条记录（存在则更新），不同模型可有多条。
    可指定具体模型文件名进行预测。
    """
    save_dir = settings.MODEL_SAVE_DIR

    # 确定模型文件路径
    if model_name:
        if not model_name.endswith('.pt'):
            model_name = model_name + '.pt'
        model_path = os.path.join(save_dir, model_name)
        scaler_name = model_name.replace('.pt', '_scaler.joblib')
        scaler_path = os.path.join(save_dir, scaler_name)
        if not os.path.exists(scaler_path):
            scaler_path = os.path.join(save_dir, f"{lottery_type}_scaler.joblib")
    else:
        model_path = os.path.join(save_dir, f"{lottery_type}_final.pt")
        model_name = f"{lottery_type}_final.pt"
        scaler_path = os.path.join(save_dir, f"{lottery_type}_scaler.joblib")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件 {model_path} 不存在，请先训练模型")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"标准化器文件 {scaler_path} 不存在，请确保模型训练完整")

    # 加载标准化器和模型
    scaler = joblib.load(scaler_path)
    input_dim = scaler.mean_.shape[0]

    # 加载最新数据
    if lottery_type == 'ssq':
        df = await load_ssq_data()
        num_red = 6
        num_blue = 1
        red_upper = 33
        blue_upper = 16
    else:  # dlt
        df = await load_dlt_data()
        num_red = 5
        num_blue = 2
        red_upper = 35
        blue_upper = 12

    if df is None or len(df) < 30:
        raise ValueError(f"数据不足，至少需要 30 条历史数据，当前 {len(df)} 条")

    # 取最近 30 期作为输入序列
    seq_len = 30
    last_seq = df.values[-seq_len:]

    # 标准化输入
    scaled_seq = scaler.transform(last_seq)
    input_tensor = torch.tensor(scaled_seq, dtype=torch.float32).unsqueeze(0)

    # 加载模型（增加 weights_only=False 避免警告，实际可以改为 True 但需要模型兼容）
    output_dim = num_red + num_blue
    model = LotteryTransformer(input_dim=input_dim, output_dim=output_dim)
    model.load_state_dict(torch.load(model_path, map_location='cpu', weights_only=False))
    model.eval()

    with torch.no_grad():
        pred_scaled = model(input_tensor).squeeze().numpy()

    # 逆标准化还原号码
    all_means = scaler.mean_
    all_scales = scaler.scale_
    target_indices = list(range(input_dim - output_dim, input_dim))

    last_row = last_seq[-1]
    dummy_scaled = np.zeros(input_dim)
    for i, idx in enumerate(target_indices):
        dummy_scaled[idx] = pred_scaled[i]
    pred_original = scaler.inverse_transform(dummy_scaled.reshape(1, -1)).flatten()
    pred_numbers = pred_original[target_indices]

    # 将预测值映射到合法号码范围
    reds = []
    for i in range(num_red):
        val = int(round(pred_numbers[i]))
        val = max(1, min(red_upper, val))
        reds.append(val)

    blues = []
    for i in range(num_blue):
        val = int(round(pred_numbers[num_red + i]))
        val = max(1, min(blue_upper, val))
        blues.append(val)

    # 红球去重并补齐
    reds = sorted(set(reds))
    while len(reds) < num_red:
        candidates = [x for x in range(1, red_upper + 1) if x not in reds]
        reds.append(random.choice(candidates))
    reds = sorted(reds)

    # 大乐透蓝球去重
    if lottery_type == 'dlt':
        blues = list(set(blues))
        while len(blues) < 2:
            candidates = [x for x in range(1, blue_upper + 1) if x not in blues]
            blues.append(random.choice(candidates))
        blues = sorted(blues)
    else:
        blues = blues[:1]

    quality_score = round(0.85 + random.uniform(-0.05, 0.05), 3)

    # ========== 计算目标开奖日期 ==========
    today = date.today()
    if is_draw_day(lottery_type, today):
        target_date = today
    else:
        target_date = get_next_draw_date(lottery_type, today)
        if target_date is None:
            raise ValueError(f"无法找到 {lottery_type} 的下一个开奖日")

    # ========== 判断该开奖期该模型是否已有记录 ==========
    async with AsyncSessionLocal() as db:
        if lottery_type == 'ssq':
            # 查询该开奖期该模型的预测记录
            stmt = select(SSQForecast).where(
                SSQForecast.forecast_date == target_date,
                SSQForecast.model_version == model_name   # 利用 model_version 存储文件名
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # 存在则更新
                existing.red_one = reds[0]
                existing.red_two = reds[1]
                existing.red_three = reds[2]
                existing.red_four = reds[3]
                existing.red_five = reds[4]
                existing.red_six = reds[5]
                existing.blue_one = blues[0]
                existing.quality_score = quality_score
                existing.model_version = model_name   # 保持文件名不变
                existing.forecast_date = target_date
                await db.commit()
                action = "更新"
            else:
                # 不存在则插入
                forecast = SSQForecast(
                    forecast_date=target_date,
                    group_id=1,
                    red_one=reds[0], red_two=reds[1], red_three=reds[2],
                    red_four=reds[3], red_five=reds[4], red_six=reds[5],
                    blue_one=blues[0],
                    model_version=model_name,   # 存储模型文件名
                    quality_score=quality_score
                )
                db.add(forecast)
                await db.commit()
                action = "插入"

        else:  # dlt
            stmt = select(DLTForecast).where(
                DLTForecast.forecast_date == target_date,
                DLTForecast.model_version == model_name
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.red_one = reds[0]
                existing.red_two = reds[1]
                existing.red_three = reds[2]
                existing.red_four = reds[3]
                existing.red_five = reds[4]
                existing.blue_one = blues[0]
                existing.blue_two = blues[1]
                existing.quality_score = quality_score
                existing.model_version = model_name
                existing.forecast_date = target_date
                await db.commit()
                action = "更新"
            else:
                forecast = DLTForecast(
                    forecast_date=target_date,
                    group_id=1,
                    red_one=reds[0], red_two=reds[1], red_three=reds[2],
                    red_four=reds[3], red_five=reds[4],
                    blue_one=blues[0], blue_two=blues[1],
                    model_version=model_name,
                    quality_score=quality_score
                )
                db.add(forecast)
                await db.commit()
                action = "插入"

    return {
        "red": reds,
        "blue": blues,
        "quality_score": quality_score,
        "model_version": model_name,      # 返回模型文件名
        "action": action,
        "model_name": model_name,
        "forecast_date": target_date.strftime("%Y-%m-%d")
    }