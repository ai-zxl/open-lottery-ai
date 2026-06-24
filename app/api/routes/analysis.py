# -*- coding: utf-8 -*-
"""
预测分析 API 路由。
"""
from fastapi import APIRouter, HTTPException, Query
from app.services.analysis_service import (
    get_today_forecasts,
    analyze_best_recommendation,
    analyze_number_frequency,
    get_today_latest_result,
    get_upcoming_draw_info,
    LOTTERY_RULES,
    get_target_draw_date
)

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/today")
async def get_today_analysis(lottery_type: str = Query('ssq', description="彩种：ssq或dlt")):
    """
    获取当前开奖期的预测分析结果，包含：
    - 所有预测记录
    - 最优推荐号码
    - 今日开奖结果（若有）
    - 号码频率统计
    """
    try:
        target_date = get_target_draw_date(lottery_type)
        if target_date is None:
            return {
                "forecasts": [],
                "recommendation": None,
                "result": None,
                "message": f"未找到 {lottery_type} 的下一个开奖日",
                "lottery_info": None,
                "upcoming": None,
                "target_draw_date": None,
                "frequency": None
            }

        forecasts = await get_today_forecasts(lottery_type)
        rule = LOTTERY_RULES.get(lottery_type)

        if not forecasts:
            return {
                "forecasts": [],
                "recommendation": None,
                "result": None,
                "message": f"当前开奖期（{target_date.strftime('%Y-%m-%d')}）暂无预测数据",
                "lottery_info": {
                    "name": rule['name'] if rule else lottery_type,
                    "draw_days": rule['draw_days'] if rule else [],
                    "draw_count": rule['draw_count'] if rule else 0
                },
                "upcoming": await get_upcoming_draw_info(lottery_type),
                "target_draw_date": target_date.strftime("%Y-%m-%d"),
                "frequency": None
            }

        # 最优推荐
        recommendation = await analyze_best_recommendation(forecasts, lottery_type)
        # 号码频率统计
        frequency = await analyze_number_frequency(forecasts, lottery_type)
        # 今日开奖结果
        latest_result = await get_today_latest_result(lottery_type)

        # 格式化预测数据
        formatted_forecasts = []
        for f in forecasts:
            if lottery_type == 'ssq':
                reds = [f.red_one, f.red_two, f.red_three, f.red_four, f.red_five, f.red_six]
                blue = f.blue_one
            else:  # dlt
                reds = [f.red_one, f.red_two, f.red_three, f.red_four, f.red_five]
                blue = [f.blue_one, f.blue_two]

            formatted_forecasts.append({
                "red": reds,
                "blue": blue,
                "quality_score": f.quality_score,
                "create_time": f.create_time.strftime("%Y-%m-%d %H:%M:%S") if f.create_time else None,
                "model_version": f.model_version
            })

        # 格式化开奖结果
        result_data = None
        if latest_result:
            if lottery_type == 'ssq':
                result_data = {
                    "red": [latest_result.red_one, latest_result.red_two, latest_result.red_three,
                            latest_result.red_four, latest_result.red_five, latest_result.red_six],
                    "blue": latest_result.blue_one,
                    "issue_num": latest_result.issue_num,
                    "draw_date": latest_result.draw_date.strftime("%Y-%m-%d") if latest_result.draw_date else None
                }
            else:  # dlt
                result_data = {
                    "red": [latest_result.front_one, latest_result.front_two, latest_result.front_three,
                            latest_result.front_four, latest_result.front_five],
                    "blue": [latest_result.back_one, latest_result.back_two],
                    "issue_num": latest_result.issue_num,
                    "draw_date": latest_result.draw_date.strftime("%Y-%m-%d") if latest_result.draw_date else None
                }

        return {
            "forecasts": formatted_forecasts,
            "recommendation": recommendation,
            "result": result_data,
            "total": len(forecasts),
            "lottery_info": {
                "name": rule['name'] if rule else lottery_type,
                "draw_days": rule['draw_days'] if rule else [],
                "draw_count": rule['draw_count'] if rule else 0
            },
            "upcoming": await get_upcoming_draw_info(lottery_type),
            "target_draw_date": target_date.strftime("%Y-%m-%d"),
            "frequency": frequency
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")