# -*- coding: utf-8 -*-
"""
预测分析服务：整合预测记录，提取最优推荐号码，提供号码频率统计。
"""
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.ssq_forecast import SSQForecast
from app.models.dlt_forecast import DLTForecast
from app.models.ssq_history import SSQHistory
from app.models.dlt_history import DLTHistory
from datetime import date, datetime, timedelta
from collections import Counter
import random

# ==================== 开奖规则配置 ====================
LOTTERY_RULES = {
    'ssq': {
        'name': '双色球',
        'draw_days': [2, 4, 7],
        'draw_count': 3,
        'red_count': 6,
        'blue_count': 1,
        'red_max': 33,
        'blue_max': 16
    },
    'dlt': {
        'name': '大乐透',
        'draw_days': [1, 3, 6],
        'draw_count': 3,
        'red_count': 5,
        'blue_count': 2,
        'red_max': 35,
        'blue_max': 12
    }
}


def get_weekday_name(weekday):
    names = ['一', '二', '三', '四', '五', '六', '日']
    return names[weekday - 1] if 1 <= weekday <= 7 else str(weekday)


def is_draw_day(lottery_type, target_date=None):
    if target_date is None:
        target_date = date.today()
    weekday = target_date.isoweekday()
    rule = LOTTERY_RULES.get(lottery_type)
    if not rule:
        return False
    return weekday in rule['draw_days']


def get_next_draw_date(lottery_type, from_date=None):
    if from_date is None:
        from_date = date.today()
    rule = LOTTERY_RULES.get(lottery_type)
    if not rule:
        return None
    if is_draw_day(lottery_type, from_date):
        return from_date
    for i in range(1, 8):
        next_date = from_date + timedelta(days=i)
        if is_draw_day(lottery_type, next_date):
            return next_date
    return None


def get_target_draw_date(lottery_type):
    """获取当前期对应的开奖日期"""
    today = date.today()
    if is_draw_day(lottery_type, today):
        return today
    return get_next_draw_date(lottery_type, today)


async def get_today_forecasts(lottery_type='ssq'):
    """获取当前开奖期的所有预测记录（基于 forecast_date 字段），按模型时间戳降序排列"""
    async with AsyncSessionLocal() as db:
        target_date = get_target_draw_date(lottery_type)
        if target_date is None:
            return []
        if lottery_type == 'ssq':
            query = select(SSQForecast).where(
                SSQForecast.forecast_date == target_date
            ).order_by(SSQForecast.create_time.desc())
        else:
            query = select(DLTForecast).where(
                DLTForecast.forecast_date == target_date
            ).order_by(DLTForecast.create_time.desc())
        result = await db.execute(query)
        records = result.scalars().all()

        # 按模型文件名中的时间戳降序排序
        def extract_timestamp(record):
            name = record.model_version
            try:
                base = name.rsplit('.', 1)[0]
                ts = int(base.split('_')[-1])
                return ts
            except:
                return 0

        records.sort(key=extract_timestamp, reverse=True)
        return records


async def analyze_best_recommendation(forecasts, lottery_type='ssq'):
    """从预测列表中提取最优号码"""
    if not forecasts:
        return None

    rule = LOTTERY_RULES.get(lottery_type)
    if not rule:
        return None

    num_red = rule['red_count']
    num_blue = rule['blue_count']
    red_upper = rule['red_max']
    blue_upper = rule['blue_max']

    red_counter = Counter()
    blue_counter = Counter()
    total_weight = 0.0

    for f in forecasts:
        weight = f.quality_score or 0.5
        if lottery_type == 'ssq':
            reds = [f.red_one, f.red_two, f.red_three, f.red_four, f.red_five, f.red_six]
            blues = [f.blue_one]
        else:
            reds = [f.red_one, f.red_two, f.red_three, f.red_four, f.red_five]
            blues = [f.blue_one, f.blue_two]
        for r in reds:
            red_counter[r] += weight
        for b in blues:
            blue_counter[b] += weight
        total_weight += weight

    red_most = red_counter.most_common(num_red)
    blue_most = blue_counter.most_common(num_blue)

    recommended_reds = [num for num, _ in red_most]
    while len(recommended_reds) < num_red:
        missing = random.choice([x for x in range(1, red_upper + 1) if x not in recommended_reds])
        recommended_reds.append(missing)
    recommended_reds.sort()

    recommended_blues = [num for num, _ in blue_most]
    while len(recommended_blues) < num_blue:
        missing = random.choice([x for x in range(1, blue_upper + 1) if x not in recommended_blues])
        recommended_blues.append(missing)
    recommended_blues.sort()

    return {
        "red": recommended_reds,
        "blue": recommended_blues if len(recommended_blues) > 1 else recommended_blues[0],
        "confidence": round(total_weight / len(forecasts), 3) if forecasts else 0
    }


# ==================== 新增：号码频率统计分析 ====================
async def analyze_number_frequency(forecasts, lottery_type='ssq'):
    """
    分析预测记录中的号码出现频率，返回红球和蓝球的 TOP 排名
    """
    if not forecasts:
        return None

    rule = LOTTERY_RULES.get(lottery_type)
    if not rule:
        return None

    red_counter = Counter()
    blue_counter = Counter()
    total_count = len(forecasts)

    for f in forecasts:
        if lottery_type == 'ssq':
            reds = [f.red_one, f.red_two, f.red_three, f.red_four, f.red_five, f.red_six]
            blues = [f.blue_one]
        else:
            reds = [f.red_one, f.red_two, f.red_three, f.red_four, f.red_five]
            blues = [f.blue_one, f.blue_two]

        for r in reds:
            red_counter[r] += 1
        for b in blues:
            blue_counter[b] += 1

    # 红球 TOP 15（按出现次数排序）
    red_top = []
    for num, count in red_counter.most_common(15):
        red_top.append({
            "number": num,
            "count": count,
            "rate": round(count / total_count * 100, 1)
        })

    # 蓝球 TOP 12（按出现次数排序）
    blue_top = []
    for num, count in blue_counter.most_common(12):
        blue_top.append({
            "number": num,
            "count": count,
            "rate": round(count / total_count * 100, 1)
        })

    # 获取最高评分的 TOP 5 模型
    top_models = sorted(forecasts, key=lambda x: x.quality_score or 0, reverse=True)[:5]
    top_models_data = []
    for f in top_models:
        if lottery_type == 'ssq':
            reds = [f.red_one, f.red_two, f.red_three, f.red_four, f.red_five, f.red_six]
            blues = [f.blue_one]
        else:
            reds = [f.red_one, f.red_two, f.red_three, f.red_four, f.red_five]
            blues = [f.blue_one, f.blue_two]
        top_models_data.append({
            "model_name": f.model_version,
            "quality_score": f.quality_score,
            "red": reds,
            "blue": blues
        })

    return {
        "total_count": total_count,
        "red_top": red_top,
        "blue_top": blue_top,
        "top_models": top_models_data
    }


async def get_today_latest_result(lottery_type='ssq'):
    """获取今天开奖结果（如果已开奖）"""
    today = date.today()
    if not is_draw_day(lottery_type, today):
        return None

    async with AsyncSessionLocal() as db:
        if lottery_type == 'ssq':
            query = select(SSQHistory).where(
                SSQHistory.draw_date == today
            ).order_by(SSQHistory.issue_num.desc()).limit(1)
        else:
            query = select(DLTHistory).where(
                DLTHistory.draw_date == today
            ).order_by(DLTHistory.issue_num.desc()).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()


async def get_upcoming_draw_info(lottery_type='ssq'):
    """获取下一期开奖信息"""
    rule = LOTTERY_RULES.get(lottery_type)
    if not rule:
        return None
    today = date.today()
    next_draw = get_next_draw_date(lottery_type, today)
    if next_draw:
        days_until = (next_draw - today).days
        weekday_name = get_weekday_name(next_draw.isoweekday())
        return {
            "next_draw_date": next_draw.strftime("%Y-%m-%d"),
            "next_draw_weekday": f"星期{weekday_name}",
            "days_until": days_until,
            "is_today": days_until == 0
        }
    return None