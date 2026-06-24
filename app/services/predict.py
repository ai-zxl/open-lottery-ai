# -*- coding: utf-8 -*-
"""
预测接口：基于已训练模型生成预测结果。
支持单模型预测和批量预测（并发控制）。
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import date
from pydantic import BaseModel
from typing import List, Optional
from app.schemas.lottery import PredictRequest, PredictResponse
from app.services.predictor import get_prediction
import asyncio

router = APIRouter(prefix="/predict", tags=["Prediction"])


# ========== 单模型预测 ==========
@router.post("/", response_model=PredictResponse)
async def predict(request: PredictRequest):
    """
    根据彩种和模型版本生成预测号码。
    自动将预测结果保存到对应的 forecast 表中。
    """
    try:
        result = await get_prediction(
            lottery_type=request.lottery_type,
            model_version=request.model_version,
            model_name=request.model_name
        )
        return PredictResponse(
            lottery_type=request.lottery_type,
            forecast_date=date.today(),
            red=result["red"],
            blue=result["blue"],
            quality_score=result.get("quality_score"),
            model_version=result.get("model_version", "Transformer")
        )
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"预测失败: {str(e)}")


# ========== 批量预测 ==========
class BatchPredictRequest(BaseModel):
    """批量预测请求"""
    lottery_type: str
    model_names: List[str]   # 模型文件名列表

class BatchPredictItem(BaseModel):
    """批量预测单项结果"""
    model_name: str
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


@router.post("/batch")
async def batch_predict(request: BatchPredictRequest):
    """
    批量预测：一次提交多个模型，后端并发执行。
    自动控制并发数（最多同时处理 10 个），避免资源耗尽。
    """
    if not request.model_names:
        raise HTTPException(400, "model_names 不能为空")

    # 限制最大并发数（可根据 GPU 显存调整）
    MAX_CONCURRENT = 10
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def predict_one(model_name: str):
        """单个模型预测（带信号量控制）"""
        async with semaphore:
            try:
                result = await get_prediction(
                    lottery_type=request.lottery_type,
                    model_name=model_name
                )
                return {
                    "model_name": model_name,
                    "success": True,
                    "data": result
                }
            except FileNotFoundError as e:
                return {
                    "model_name": model_name,
                    "success": False,
                    "error": f"模型文件不存在: {str(e)}"
                }
            except ValueError as e:
                return {
                    "model_name": model_name,
                    "success": False,
                    "error": f"数据不足: {str(e)}"
                }
            except Exception as e:
                return {
                    "model_name": model_name,
                    "success": False,
                    "error": f"预测失败: {str(e)}"
                }

    # 并发执行所有预测任务
    tasks = [predict_one(name) for name in request.model_names]
    results = await asyncio.gather(*tasks)

    # 统计
    success_count = sum(1 for r in results if r["success"])
    total = len(results)

    return {
        "results": results,
        "total": total,
        "success_count": success_count,
        "failed_count": total - success_count
    }