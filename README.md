# 🎰 Open-Lottery-AI

<p align="center">
  <img alt="logo" src="https://ai-zxl-1419463292.cos.ap-chengdu.myqcloud.com/open-unknown/logo.png" width="120">
</p>
<h1 align="center" style="margin: 30px 0 30px; font-weight: bold;">Open-Lottery-AI v1.0.0</h1>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/version-v1.0.0-brightgreen.svg"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.10+-blue.svg"></a>
  <a href="#"><img src="https://img.shields.io/badge/Vue-3.5+-green.svg"></a>
  <a href="#"><img src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
</p>

> 基于 **FastAPI + PyTorch + Transformer + Vue 3** 的彩票预测系统，目前支持双色球（SSQ）和大乐透（DLT）的数据管理、模型训练与预测推理。

**开源地址：** [https://github.com/ai-zxl/open-lottery-ai](https://github.com/ai-zxl/open-lottery-ai)

---

## 📖 项目简介

**Open-Lottery-AI** 是一个端到端的彩票数据预测系统，通过历史开奖数据训练深度学习模型（Transformer 架构），预测未来开奖结果。系统包含：

- 📊 **数据抓取模块**：增量抓取双色球和大乐透历史数据（`scripts/` 目录）
- 🗄️ **数据管理模块**：MySQL 存储历史数据及 20+ 分析字段（和值、跨度、奇偶比、AC 值等）
- 🧠 **模型训练模块**：基于 PyTorch + Transformer 的异步训练服务（Celery + RabbitMQ）
- 🔮 **预测推理模块**：支持多模型选择，生成预测号码并保存到数据库
- 📈 **预测分析模块**：整合今日预测记录，提取最优推荐号码，与开奖结果对比
- 🖥️ **Web 管理界面**：Vue3 可视化面板，支持数据浏览、训练控制、预测展示和结果分析

项目采用 **前后端分离** 架构，后端提供 REST API，前端独立部署，适合企业级 AI 平台集成。

---

## 🎯 核心特性

### 后端（Python）

- ✅ **异步任务队列**：基于 RabbitMQ + Celery，支持多 Worker 并发训练，任务持久化
- ✅ **深度学习框架**：PyTorch + Transformer，支持自定义超参数（轮数、批次、序列长度、学习率）
- ✅ **多模型管理**：每次训练根据参数生成唯一模型文件名（`{彩种}_epochs{N}_bs{N}_seq{N}_lr{N}_{时间戳}.pt`），永不覆盖
- ✅ **数据管理**：MySQL 存储历史数据及 20+ 分析字段（和值、跨度、奇偶比、AC 值等）
- ✅ **进度缓存**：Redis 缓存训练进度，支持高频状态轮询
- ✅ **REST API**：FastAPI 自动生成 OpenAPI 文档（Swagger UI）
- ✅ **设备支持**：自动检测 GPU（CUDA）或回退到 CPU 训练
- ✅ **水平扩展**：支持增加 Celery Worker 数量或部署多个 FastAPI 实例
- ✅ **一键训练**：支持训练前自动抓取最新数据，保持数据最新

### 前端（Vue3）

- ✅ **首页**：最新开奖数据（双色球 + 大乐透）+ 已训练模型列表
- ✅ **数据管理**：分页浏览双色球/大乐透历史数据（红球/前区、蓝球/后区、和值、跨度）
- ✅ **模型训练**：可视化配置超参数（训练轮数 1-500、批次大小 1-256、序列长度 10-3000、学习率 5位精度），实时轮询训练状态
- ✅ **预测结果**：支持**多模型同时预测**，每个模型生成独立的预测结果卡片
- ✅ **预测分析**：展示今日所有预测记录，基于质量评分加权提取最优推荐号码，与开奖结果对比显示命中情况
- ✅ **开奖规则展示**：显示双色球（二、四、日）和大乐透（一、三、六）开奖规则及下一期开奖倒计时
- ✅ **开放架构**：无需登录，开箱即用，可扩展权限模块

---

## 🛠️ 技术栈

### 后端

| 组件               | 技术选型                                     |
| ------------------ | -------------------------------------------- |
| Web 框架           | FastAPI 0.115+ (异步, OpenAPI 自动生成)      |
| 异步任务队列       | RabbitMQ 3.12 + Celery 5.6+                  |
| 数据库             | MySQL 8.0 + SQLAlchemy 2.0 (asyncmy 驱动)   |
| 缓存               | Redis 7.0                                    |
| 深度学习框架       | PyTorch 2.5 + Transformers 4.46              |
| 数据处理           | Pandas 2.2 + NumPy 1.26                      |
| 配置管理           | Pydantic Settings + python-dotenv            |
| 部署               | Docker Compose (开发/生产)                   |

### 前端

| 组件         | 技术选型                    |
| ------------ | --------------------------- |
| 框架         | Vue 3.5+ (Composition API)  |
| 构建工具     | Vite 8.0+                   |
| UI 组件库    | Element Plus 2.8+           |
| 状态管理     | Pinia 2.2+                  |
| 路由管理     | Vue Router 4.4+             |
| HTTP 客户端  | Axios 1.7+ (统一拦截器)     |

---

## 🏗️ 系统架构

~~~
┌─────────────────────────────────────────────────────────────────────────────┐
│ Vue3 前端 (lottery-ui) │
│ ├─ 首页仪表盘（最新开奖 + 模型列表） │
│ ├─ 数据管理（分页浏览历史数据） │
│ ├─ 模型训练（配置参数 + 状态监控） │
│ ├─ 预测结果（多模型并行预测） │
│ └─ 预测分析（推荐号码 + 开奖对比） │
└─────────────────────────────────────┬───────────────────────────────────────┘
│ HTTP (代理 /api → localhost:8000)
┌─────────────────────────────────────▼───────────────────────────────────────┐
│ FastAPI 后端 (app/) │
│ ├─ api/routes/ - 数据管理 / 训练 / 预测 / 模型 / 分析 API │
│ ├─ core/ - 配置 / 数据库 / Redis / Celery │
│ ├─ models/ - SQLAlchemy ORM 模型 │
│ ├─ schemas/ - Pydantic 请求/响应模型 │
│ ├─ services/ - 数据加载 / Transformer / 训练器 / 预测器 / 分析器 │
│ └─ tasks/ - Celery 异步训练任务 │
└─────────┬───────────────────────────────────────┬─────────────────────────┘
│ │
│ 数据流 │ 任务分发
▼ ▼
┌─────────────────────────────────────┐ ┌─────────────────────────────────┐
│ MySQL │ │ Celery Worker │
│ - ssq_history (双色球历史) │ │ (异步训练任务) │
│ - dlt_history (大乐透历史) │ │ ├─ 加载历史数据 │
│ - ssq_forecast (双色球预测) │ │ ├─ 标准化 + 构造序列 │
│ - dlt_forecast (大乐透预测) │ │ ├─ Transformer 模型训练 │
└─────────────────────────────────────┘ │ └─ 保存模型 & 标准化器 │
│ └─────────────────────────────────┘
│ 数据更新（手动执行脚本 或 一键训练自动触发）
▼
┌─────────────────────────────────────┐
│ 数据抓取脚本 (scripts/) │
│ - fetch_ssq_incremental.py │
│ - fetch_dlt_incremental.py │
└─────────────────────────────────────┘
~~~

**数据流说明**：

1. **数据抓取** → 增量更新到 MySQL（`scripts/fetch_*.py` 或一键训练自动触发）
2. **前端配置** → 提交训练参数（彩种、轮数、批次、序列长度、学习率）
3. **FastAPI** → 生成 `task_id`，通过 Celery 发布任务到 RabbitMQ
4. **Celery Worker** → 消费任务，加载历史数据，训练 Transformer 模型，保存到 `models_storage/`（唯一文件名）
5. **前端轮询** → 每 5 秒查询训练状态（pending/running/completed/failed）
6. **预测推理** → 用户选择模型（支持多选），加载对应模型生成预测号码，存入 `*_forecast` 表
7. **前端展示** → 每个模型独立卡片展示预测号码、质量评分、模型版本
8. **预测分析** → 整合今日所有预测，加权推荐最优号码，与开奖结果对比

---

## 📁 项目目录结构

~~~
open-lottery-ai/                                    # 项目根目录
│
├── app/                                            # 后端主应用（FastAPI）
│   ├── api/                                        # REST API 路由层
│   │   └── routes/                                 # 路由定义
│   │       ├── health.py                           # 健康检查接口
│   │       ├── data.py                             # 数据查询接口（双色球/大乐透）
│   │       ├── train.py                            # 训练任务接口（提交/状态查询）
│   │       ├── predict.py                          # 预测推理接口
│   │       ├── models.py                           # 模型管理接口（列表/下载）
│   │       └── analysis.py                         # 预测分析接口（推荐号码+开奖对比）
│   ├── core/                                       # 核心配置与基础设施
│   │   ├── config.py                               # 环境变量配置（Pydantic Settings）
│   │   ├── database.py                             # MySQL 异步引擎、会话工厂
│   │   ├── redis_client.py                         # Redis 连接池
│   │   └── celery_app.py                           # Celery 应用配置
│   ├── models/                                     # SQLAlchemy ORM 数据模型
│   │   ├── ssq_history.py                          # 双色球历史数据表
│   │   ├── dlt_history.py                          # 大乐透历史数据表
│   │   ├── ssq_forecast.py                         # 双色球预测结果表
│   │   └── dlt_forecast.py                         # 大乐透预测结果表
│   ├── schemas/                                    # Pydantic 请求/响应模型
│   │   └── lottery.py                              # 彩种、训练、预测相关 Schema
│   ├── services/                                   # 业务逻辑层
│   │   ├── data_loader.py                          # 数据加载器（特征工程）
│   │   ├── transformer_model.py                    # Transformer 模型定义
│   │   ├── trainer.py                              # 模型训练器（保存模型+标准化器）
│   │   ├── predictor.py                            # 预测服务（多模型预测）
│   │   ├── analysis_service.py                     # 预测分析服务（推荐+对比）
│   │   └── fetch_service.py                        # 数据抓取服务（调用抓取脚本）
│   ├── tasks/                                      # Celery 异步任务
│   │   └── training_jobs.py                        # 训练任务定义（含一键完整训练）
│   ├── __init__.py                                 # 包标识文件
│   └── main.py                                     # FastAPI 应用入口
│
├── lottery-ui/                                     # Vue3 前端项目
│   ├── src/
│   │   ├── api/                                    # API 接口层
│   │   │   ├── data.js                             # 数据接口
│   │   │   ├── train.js                            # 训练接口
│   │   │   ├── predict.js                          # 预测接口
│   │   │   ├── model.js                            # 模型管理接口
│   │   │   └── analysis.js                         # 分析接口
│   │   ├── router/                                 # 路由配置
│   │   │   └── index.js
│   │   ├── store/                                  # Pinia 状态管理
│   │   │   ├── index.js                            # 统一导出
│   │   │   ├── useDataStore.js                     # 数据状态
│   │   │   ├── useTrainStore.js                    # 训练状态
│   │   │   └── usePredictStore.js                  # 预测状态
│   │   ├── utils/                                  # 工具函数
│   │   │   ├── request.js                          # Axios 统一请求封装
│   │   │   └── index.js                            # 通用工具（日期/格式化）
│   │   ├── views/                                  # 页面视图
│   │   │   ├── home/                               # 首页（仪表盘）
│   │   │   ├── data/                               # 数据管理（历史数据浏览）
│   │   │   ├── train/                              # 模型训练（参数配置+状态监控）
│   │   │   ├── predict/                            # 预测结果（多模型并行预测）
│   │   │   └── analysis/                           # 预测分析（推荐号码+开奖对比）
│   │   ├── App.vue                                 # 根组件
│   │   ├── main.js                                 # 入口文件
│   │   └── permission.js                           # 路由守卫（开放系统）
│   ├── .env.development                            # 开发环境变量
│   ├── .env.production                             # 生产环境变量
│   ├── package.json                                # 依赖管理
│   └── vite.config.js                              # Vite 构建配置
│
├── models_storage/                                 # 训练生成的模型文件目录
│   ├── {彩种}_epochs{N}_bs{N}_seq{N}_lr{N}_{时间戳}.pt  # PyTorch 模型
│   ├── {彩种}_epochs{N}_bs{N}_seq{N}_lr{N}_{时间戳}_scaler.joblib  # 标准化器
│   ├── {彩种}_final.pt                             # 最新模型快照
│   └── {彩种}_scaler.joblib                        # 最新标准化器
│
├── scripts/                                        # 数据抓取脚本
│   ├── __init__.py
│   ├── fetch_ssq_incremental.py                    # 双色球增量抓取
│   ├── fetch_dlt_incremental.py                    # 大乐透增量抓取
│   ├── generate_ssq_all.py                         # 双色球全量生成
│   └── generate_dlt_all.py                         # 大乐透全量生成
│
├── sql/                                            # SQL 建表脚本
│   └── open-lottery.sql                            # 完整建表语句
│
├── .env.development                                # 开发环境变量
├── .env.production                                 # 生产环境变量
├── .gitignore                                      # Git 忽略文件
├── batch_train_seqlen.py                           # 批量训练脚本（序列长度扫描）
├── docker-compose.yml                              # 依赖服务（MySQL/Redis/RabbitMQ）
├── LICENSE                                         # MIT 许可证
├── README.md                                       # 项目文档
└── requirements.txt                                # Python 依赖清单

~~~


---

## 🔍 核心功能详解

### 1. 模型训练（一键完整训练）

- 支持双色球和大乐透两种彩种
- 可配置参数：训练轮数（1-500）、批次大小（1-256）、序列长度（10-3000）、学习率（5位精度）
- 支持训练前自动抓取最新数据（增量更新）
- 每次训练生成唯一模型文件名，永不覆盖
- 实时轮询训练状态（等待中/抓取数据/训练中/已完成/失败）

### 2. 多模型预测

- 支持同时选择多个模型进行预测
- 每个模型生成独立的预测结果卡片
- 展示预测号码（红球/前区 + 蓝球/后区）、质量评分、模型版本
- 同一天同一模型只保留一条预测记录（自动更新）

### 3. 预测分析

- 展示今日所有预测记录
- 基于质量评分加权提取最优推荐号码
- 显示双色球和大乐透的开奖规则（二、四、日 / 一、三、六）
- 下一期开奖日期倒计时
- 与开奖结果对比，显示命中个数

### 4. 模型管理

- 模型文件按 `{彩种}_epochs{N}_bs{N}_seq{N}_lr{N}_{时间戳}.pt` 格式命名
- 同时保留 `{彩种}_final.pt` 作为最新模型
- 支[services](app/services)持模型列表查看和下载

---

## 🚀 快速开始

### 前提条件

- Python 3.10+ 和 Conda（推荐）
- Node.js 16+ 和 npm/yarn
- Docker 和 Docker Compose

### 一键启动

~~~

# 1. 启动依赖服务
cd open-lottery-ai
docker-compose up -d
sleep 10
docker ps

# 2. 初始化数据库
docker exec -i lottery-mysql mysql -uroot -p123456 < sql/open-lottery.sql

# 3. 抓取历史数据
cd scripts
python fetch_ssq_incremental.py
python fetch_dlt_incremental.py
cd ..

# 4. 创建并激活 Conda 环境
conda create -n lottery python=3.10 -y
conda activate lottery

# 5. 安装后端依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 6. 配置环境变量
copy .env.development .env

# 7. 启动 FastAPI 服务（终端1）
start cmd /k "conda activate lottery && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# 8. 启动 Celery Worker（终端2）
start cmd /k "conda activate lottery && celery -A app.core.celery_app worker --loglevel=info --pool=solo -c 1 -Q celery"

# 9. 安装前端依赖
cd lottery-ui
npm install --registry=https://registry.npmmirror.com

# 10. 启动前端服务（终端3）
start cmd /k "npm run dev"

# 访问前端: http://localhost:5173
# API 文档: http://localhost:8000/docs
# RabbitMQ 管理: http://localhost:15672 (guest/guest)

~~~

### 演示图

<div align="center">
  <img src="https://ai-zxl-1419463292.cos.ap-chengdu.myqcloud.com/open-unknown/lottery01.png" width="48%" />
  <img src="https://ai-zxl-1419463292.cos.ap-chengdu.myqcloud.com/open-unknown/lottery02.png" width="48%"/>
</div>
<br/>
<div align="center">
  <img src="https://ai-zxl-1419463292.cos.ap-chengdu.myqcloud.com/open-unknown/lottery03.png" width="48%" />
  <img src="https://ai-zxl-1419463292.cos.ap-chengdu.myqcloud.com/open-unknown/lottery04.png" width="48%"/>
</div>