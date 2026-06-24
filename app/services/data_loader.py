# -*- coding: utf-8 -*-
"""
数据加载模块：从数据库读取历史数据并转换为特征矩阵。
同时提供异步和同步版本，异步供 FastAPI 使用，同步供 Celery 训练使用。
"""
import pandas as pd
import numpy as np
import pymysql
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.ssq_history import SSQHistory
from app.models.dlt_history import DLTHistory
from app.core.config import settings


# ========== 异步版本（供 FastAPI 使用） ==========
async def load_ssq_data(limit: int = None) -> pd.DataFrame:
    """异步加载双色球历史数据"""
    async with AsyncSessionLocal() as db:
        query = select(SSQHistory).order_by(SSQHistory.issue_num)
        if limit:
            query = query.limit(limit)
        result = await db.execute(query)
        rows = result.scalars().all()

    data = []
    for r in rows:
        features = [
            r.year, r.month, r.quarter,
            r.red_summation, r.red_span,
            r.red_odd_count, r.red_even_count,
            r.red_small_count, r.red_big_count,
            r.red_prime_count, r.red_composite_count,
            r.red_mod0_count, r.red_mod1_count, r.red_mod2_count,
            r.red_zone1_count, r.red_zone2_count, r.red_zone3_count,
            r.red_ac_value,
            r.total_odd_count, r.total_even_count,
            r.red_repeat_count if hasattr(r, 'red_repeat_count') else 0,
        ]
        target = [r.red_one, r.red_two, r.red_three, r.red_four, r.red_five, r.red_six, r.blue_one]
        data.append(features + target)

    columns = [
        'year','month','quarter','sum','span','odd','even','small','big',
        'prime','composite','mod0','mod1','mod2',
        'zone1','zone2','zone3','ac','total_odd','total_even','repeat',
        'r1','r2','r3','r4','r5','r6','b1'
    ]
    return pd.DataFrame(data, columns=columns)


async def load_dlt_data(limit: int = None) -> pd.DataFrame:
    """异步加载大乐透历史数据"""
    async with AsyncSessionLocal() as db:
        query = select(DLTHistory).order_by(DLTHistory.issue_num)
        if limit:
            query = query.limit(limit)
        result = await db.execute(query)
        rows = result.scalars().all()

    data = []
    for r in rows:
        features = [
            r.year, r.month, r.quarter,
            r.front_summation, r.front_span,
            r.front_odd_count, r.front_even_count,
            r.front_small_count, r.front_big_count,
            r.front_prime_count, r.front_composite_count,
            r.front_mod0_count, r.front_mod1_count, r.front_mod2_count,
            r.front_zone1_count, r.front_zone2_count, r.front_zone3_count,
            r.front_ac_value,
            r.total_odd_count, r.total_even_count,
            r.front_repeat_count if hasattr(r, 'front_repeat_count') else 0,
        ]
        target = [
            r.front_one, r.front_two, r.front_three, r.front_four, r.front_five,
            r.back_one, r.back_two
        ]
        data.append(features + target)

    columns = [
        'year','month','quarter','sum','span','odd','even','small','big',
        'prime','composite','mod0','mod1','mod2',
        'zone1','zone2','zone3','ac','total_odd','total_even','repeat',
        'f1','f2','f3','f4','f5','b1','b2'
    ]
    return pd.DataFrame(data, columns=columns)


# ========== 同步版本（供 Celery 训练使用） ==========
def _get_db_connection():
    """获取同步数据库连接"""
    return pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset='utf8mb4'
    )


def load_ssq_data_sync(limit: int = None) -> pd.DataFrame:
    """同步加载双色球历史数据（供 Celery 训练使用）"""
    conn = _get_db_connection()
    try:
        query = "SELECT * FROM ssq_history ORDER BY issue_num"
        if limit:
            query += f" LIMIT {limit}"
        df = pd.read_sql(query, conn)
        if df.empty:
            return pd.DataFrame()

        # 构建特征列
        features = df[[
            'year', 'month', 'quarter',
            'red_summation', 'red_span',
            'red_odd_count', 'red_even_count',
            'red_small_count', 'red_big_count',
            'red_prime_count', 'red_composite_count',
            'red_mod0_count', 'red_mod1_count', 'red_mod2_count',
            'red_zone1_count', 'red_zone2_count', 'red_zone3_count',
            'red_ac_value',
            'total_odd_count', 'total_even_count',
            'red_repeat_count'
        ]].fillna(0).values

        targets = df[[
            'red_one', 'red_two', 'red_three', 'red_four', 'red_five', 'red_six', 'blue_one'
        ]].values

        data = np.concatenate([features, targets], axis=1)   # 使用 np
        columns = [
            'year','month','quarter','sum','span','odd','even','small','big',
            'prime','composite','mod0','mod1','mod2',
            'zone1','zone2','zone3','ac','total_odd','total_even','repeat',
            'r1','r2','r3','r4','r5','r6','b1'
        ]
        return pd.DataFrame(data, columns=columns)
    finally:
        conn.close()


def load_dlt_data_sync(limit: int = None) -> pd.DataFrame:
    """同步加载大乐透历史数据（供 Celery 训练使用）"""
    conn = _get_db_connection()
    try:
        query = "SELECT * FROM dlt_history ORDER BY issue_num"
        if limit:
            query += f" LIMIT {limit}"
        df = pd.read_sql(query, conn)
        if df.empty:
            return pd.DataFrame()

        features = df[[
            'year', 'month', 'quarter',
            'front_summation', 'front_span',
            'front_odd_count', 'front_even_count',
            'front_small_count', 'front_big_count',
            'front_prime_count', 'front_composite_count',
            'front_mod0_count', 'front_mod1_count', 'front_mod2_count',
            'front_zone1_count', 'front_zone2_count', 'front_zone3_count',
            'front_ac_value',
            'total_odd_count', 'total_even_count',
            'front_repeat_count'
        ]].fillna(0).values

        targets = df[[
            'front_one', 'front_two', 'front_three', 'front_four', 'front_five',
            'back_one', 'back_two'
        ]].values

        data = np.concatenate([features, targets], axis=1)   # 使用 np
        columns = [
            'year','month','quarter','sum','span','odd','even','small','big',
            'prime','composite','mod0','mod1','mod2',
            'zone1','zone2','zone3','ac','total_odd','total_even','repeat',
            'f1','f2','f3','f4','f5','b1','b2'
        ]
        return pd.DataFrame(data, columns=columns)
    finally:
        conn.close()