<template>
  <!-- 训练配置主容器 -->
  <div class="train-container">
    <!-- 训练配置卡片 -->
    <el-card>
      <!-- 卡片头部：标题 + 帮助按钮 -->
      <template #header>
        <div class="card-header">
          <span>⚙️ 训练配置</span>
          <!-- 点击切换参数说明表格的显示/隐藏 -->
          <el-button type="text" @click="showHelp = !showHelp" style="font-size:14px;">
            {{ showHelp ? '收起参数说明 ▲' : '展开参数说明 ▼' }}
          </el-button>
        </div>
      </template>

      <!-- 参数说明表格（可展开/收起，使用过渡动画） -->
      <el-collapse-transition>
        <div v-show="showHelp" class="help-table">
          <el-table :data="helpData" border size="small" style="width:100%;">
            <el-table-column prop="param" label="参数" width="120" />
            <el-table-column prop="desc" label="说明" />
            <el-table-column prop="range" label="取值范围" width="160" />
            <el-table-column prop="recommend" label="推荐值" width="140" />
          </el-table>
        </div>
      </el-collapse-transition>

      <!-- 训练参数表单 -->
      <el-form label-width="120px" label-position="top" class="train-form">
        <!-- 彩种选择 -->
        <el-form-item label="彩种">
          <el-radio-group v-model="lotteryType">
            <el-radio label="ssq">双色球</el-radio>
            <el-radio label="dlt">大乐透</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 训练轮数：1-500，默认200（最优精度） -->
        <el-form-item label="训练轮数">
          <el-input-number v-model="epochs" :min="1" :max="500" style="width: 100%" />
        </el-form-item>

        <!-- 批次大小：1-256，默认128（最优精度） -->
        <el-form-item label="批次大小">
          <el-input-number v-model="batchSize" :min="1" :max="256" style="width: 100%" />
        </el-form-item>

        <!-- 序列长度：10-3000，默认30（推荐值） -->
        <el-form-item label="序列长度">
          <el-input-number v-model="seqLen" :min="10" :max="3000" style="width: 100%" />
        </el-form-item>

        <!-- 学习率：步长0.00001，精度5位，默认0.00005（最优精度） -->
        <el-form-item label="学习率">
          <el-input-number v-model="learningRate" :step="0.00001" :precision="5" style="width: 100%" />
        </el-form-item>

        <!-- 训练前是否抓取最新数据（开关） -->
        <el-form-item label="训练前更新数据">
          <el-switch v-model="withFetch" active-text="开启" inactive-text="关闭" />
          <span style="margin-left:10px;color:#909399;font-size:12px;">开启后将先抓取最新开奖数据</span>
        </el-form-item>

        <!-- 操作按钮组 -->
        <el-form-item>
          <div class="btn-group">
            <!-- 提交训练任务按钮，显示文字随 withFetch 变化 -->
            <el-button type="primary" @click="handleStart" :loading="trainStore.loading">
              {{ withFetch ? '一键完整训练' : '开始训练' }}
            </el-button>
            <!-- 查询当前任务状态（任务提交后可用） -->
            <el-button @click="handleCheckStatus" :disabled="!trainStore.taskId">查询状态</el-button>
            <!-- 重置所有参数为默认最优值 -->
            <el-button @click="handleReset">重置</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 训练状态展示卡片（仅当有任务ID时显示） -->
    <el-card v-if="trainStore.taskId" style="margin-top:20px">
      <template #header>📊 训练状态</template>
      <div class="status-content">
        <p><strong>任务 ID：</strong>{{ trainStore.taskId }}</p>
        <p><strong>状态：</strong>
          <el-tag :type="statusTagType">{{ statusText }}</el-tag>
        </p>
        <!-- 如果任务处于抓取或训练阶段，显示具体阶段名称 -->
        <p v-if="trainStore.status?.meta?.stage">
          <strong>当前阶段：</strong>
          <el-tag size="small" :type="stageTagType">{{ stageText }}</el-tag>
        </p>
        <!-- 训练完成时，以 JSON 格式显示结果摘要 -->
        <pre v-if="trainStore.status?.result" class="result-pre">{{ JSON.stringify(trainStore.status.result, null, 2) }}</pre>
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 导入 Vue 响应式 API
import { ref, computed, onUnmounted } from 'vue'
// 导入 Pinia store（训练状态管理）
import { useTrainStore } from '@/store'
// Element Plus 消息提示
import { ElMessage } from 'element-plus'

// ----- 获取训练 store 实例 -----
const trainStore = useTrainStore()

// ----- 训练参数（采用最高精度最优配置） -----
const lotteryType = ref('ssq')          // 彩种：ssq 或 dlt
const epochs = ref(200)                // 训练轮数：200（推荐）
const batchSize = ref(128)             // 批次大小：128（推荐）
const seqLen = ref(30)                 // 序列长度：30（推荐）
const learningRate = ref(0.00005)      // 学习率：5e-5（最优）
const withFetch = ref(true)            // 训练前是否更新数据
const showHelp = ref(false)            // 参数说明表格是否展开

// ----- 参数说明表格数据（用于展示给用户） -----
const helpData = [
  {
    param: '彩种',
    desc: '选择要训练的彩票类型',
    range: '双色球 / 大乐透',
    recommend: '按需选择'
  },
  {
    param: '训练轮数',
    desc: '训练迭代轮数，越大模型越收敛',
    range: '1 - 500',
    recommend: '200 - 300（追求精度）'
  },
  {
    param: '批次大小',
    desc: '每次迭代使用的样本数',
    range: '1 - 256',
    recommend: '64 - 128'
  },
  {
    param: '序列长度',
    desc: '使用多少期历史数据预测下一期',
    range: '10 - 3000',
    recommend: '30 - 50'
  },
  {
    param: '学习率',
    desc: '模型参数更新步长，越小收敛越精细',
    range: '0.00001 - 0.01',
    recommend: '0.00005 - 0.0001'
  },
  {
    param: '更新数据',
    desc: '训练前是否先抓取最新开奖数据',
    range: '开启 / 关闭',
    recommend: '开启'
  }
]

// ----- 计算属性：状态文本映射 -----
const statusText = computed(() => {
  const s = trainStore.status?.status
  const map = {
    pending: '等待中',
    running: '训练中...',
    completed: '已完成 ✅',
    failed: '失败 ❌',
    fetching: '数据更新中...'
  }
  return map[s] || '未知'
})

// 状态标签类型（用于 Element Plus Tag 颜色）
const statusTagType = computed(() => {
  const s = trainStore.status?.status
  const map = {
    completed: 'success',
    failed: 'danger',
    running: 'warning',
    fetching: 'warning'
  }
  return map[s] || 'info'
})

// 当前阶段文本（抓取/训练/完成）
const stageText = computed(() => {
  const stage = trainStore.status?.meta?.stage
  const map = { fetch: '抓取数据', train: '训练模型', done: '已完成' }
  return map[stage] || '未知'
})

// 阶段标签类型
const stageTagType = computed(() => {
  const stage = trainStore.status?.meta?.stage
  const map = { fetch: 'warning', train: 'primary', done: 'success' }
  return map[stage] || 'info'
})

// ----- 轮询定时器（用于自动刷新训练状态） -----
let pollTimer = null

/**
 * 轮询训练状态（每5秒请求一次）
 * 当任务完成或失败时自动停止轮询并提示
 */
const pollStatus = async () => {
  if (!trainStore.taskId) return
  try {
    const res = await trainStore.fetchStatus(trainStore.taskId)
    const status = res.status
    // 如果任务结束（成功或失败），停止轮询并提示
    if (status === 'completed' || status === 'failed' || status === 'SUCCESS' || status === 'FAILURE') {
      ElMessage.info(`训练${status === 'completed' || status === 'SUCCESS' ? '完成' : '失败'}`)
      return
    }
    // 继续轮询
    pollTimer = setTimeout(pollStatus, 5000)
  } catch {
    // 出错时继续轮询（防止中断）
    pollTimer = setTimeout(pollStatus, 5000)
  }
}

/**
 * 提交训练任务
 * 从表单收集参数，调用 store 的 start 方法
 */
const handleStart = async () => {
  try {
    const params = {
      lottery_type: lotteryType.value,
      epochs: epochs.value,
      batch_size: batchSize.value,
      seq_len: seqLen.value,
      learning_rate: learningRate.value,
      with_fetch: withFetch.value
    }
    await trainStore.start(params)
    ElMessage.success(`任务已提交，ID: ${trainStore.taskId}`)
    // 开始轮询状态
    pollStatus()
  } catch (e) {
    ElMessage.error('提交失败：' + e.message)
  }
}

/**
 * 手动查询当前训练任务状态
 */
const handleCheckStatus = async () => {
  if (!trainStore.taskId) return
  await trainStore.fetchStatus(trainStore.taskId)
  ElMessage.info(`当前状态: ${trainStore.status?.status}`)
}

/**
 * 重置所有参数为默认最优值，并清空任务状态和轮询
 */
const handleReset = () => {
  trainStore.reset()
  if (pollTimer) clearTimeout(pollTimer)
  lotteryType.value = 'ssq'
  epochs.value = 200
  batchSize.value = 128
  seqLen.value = 30
  learningRate.value = 0.00005
  withFetch.value = true
}

// ----- 组件卸载时清除定时器，防止内存泄漏 -----
onUnmounted(() => {
  if (pollTimer) clearTimeout(pollTimer)
})
</script>

<style scoped>
/* 训练容器内边距 */
.train-container {
  padding: 0;
}
/* 表单项底部间距 */
.train-form .el-form-item {
  margin-bottom: 18px;
}

/* 卡片头部 flex 布局 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 帮助表格上边距和边框 */
.help-table {
  margin-bottom: 20px;
  padding: 12px 0;
  border-top: 1px solid #ebeef5;
}

/* 按钮组使用 flex 布局，支持换行 */
.btn-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.btn-group .el-button {
  flex: 1 0 auto;
  min-width: 80px;
}

/* 状态内容样式 */
.status-content {
  font-size: 14px;
  line-height: 1.8;
}
/* 训练结果 JSON 展示区 */
.result-pre {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .train-form .el-form-item {
    margin-bottom: 14px;
  }
  .train-form .el-form-item__label {
    padding-bottom: 4px;
  }
  .help-table {
    font-size: 12px;
  }
}
</style>