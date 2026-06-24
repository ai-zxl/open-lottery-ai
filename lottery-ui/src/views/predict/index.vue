<template>
  <div class="predict-container">
    <el-card>
      <template #header>🔮 生成预测</template>
      <el-form label-width="120px" label-position="top" class="predict-form">
        <!-- 彩种选择 -->
        <el-form-item label="彩种">
          <el-radio-group v-model="lotteryType" @change="onLotteryChange">
            <el-radio label="ssq">双色球</el-radio>
            <el-radio label="dlt">大乐透</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 模型多选 + 搜索（filterable 已支持搜索） -->
        <el-form-item label="选择模型">
          <el-select
            v-model="selectedModels"
            multiple
            placeholder="输入模型名搜索，支持多选"
            style="width:100%;"
            filterable
            collapse-tags
            :disabled="modelOptions.length === 0"
            @change="onModelChange"
          >
            <el-option
              v-for="item in modelOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <div style="color:#909399;font-size:12px;margin-top:4px;">
            共 {{ modelOptions.length }} 个模型，输入关键词可快速筛选
          </div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="btn-group">
            <el-button
              type="primary"
              @click="handlePredict"
              :loading="loading"
              :disabled="!selectedModels.length"
            >
              预测
            </el-button>
            <el-button @click="handleClear">清空结果</el-button>
            <el-button @click="loadModels" :loading="loadingModels">刷新模型列表</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 预测结果列表 -->
    <div v-if="results.length > 0" style="margin-top:20px;">
      <el-row :gutter="20">
        <el-col
          v-for="(item, index) in results"
          :key="index"
          :xs="24"
          :sm="12"
          :md="12"
          :lg="8"
        >
          <el-card class="result-card" shadow="hover">
            <template #header>
              <div class="result-header">
                <span class="model-name">{{ item.modelName }}</span>
                <el-tag :type="item.success ? 'success' : 'danger'" size="small">
                  {{ item.success ? '成功' : '失败' }}
                </el-tag>
              </div>
            </template>
            <div v-if="item.success" class="result-content">
              <p><strong>彩种：</strong>{{ item.data.lottery_type === 'ssq' ? '双色球' : '大乐透' }}</p>
              <p><strong>预测日期：</strong>{{ item.data.forecast_date }}</p>
              <p class="ball-row">
                <strong>红球（前区）：</strong>
                <el-tag
                  v-for="r in item.data.red"
                  :key="r"
                  size="default"
                  class="result-tag"
                >{{ r }}</el-tag>
              </p>
              <p class="ball-row">
                <strong>蓝球（后区）：</strong>
                <el-tag
                  v-for="b in item.data.blue"
                  :key="b"
                  size="default"
                  type="danger"
                  class="result-tag"
                >{{ b }}</el-tag>
              </p>
              <p><strong>质量评分：</strong>{{ item.data.quality_score }}</p>
              <p><strong>模型版本：</strong>{{ item.data.model_version }}</p>
            </div>
            <div v-else class="error-msg">
              <el-alert type="error" :title="item.error" show-icon />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 全局错误 -->
    <el-alert
      v-if="globalError"
      type="error"
      :title="globalError"
      show-icon
      closable
      @close="globalError = null"
      style="margin-top:20px;"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listModels } from '@/api/model'
import { getPrediction } from '@/api/predict'
import { ElMessage } from 'element-plus'

// ----- 状态 -----
const lotteryType = ref('ssq')
const selectedModels = ref([])
const modelOptions = ref([])
const results = ref([])
const loading = ref(false)
const loadingModels = ref(false)
const globalError = ref(null)

// ----- 加载模型列表 -----
const loadModels = async () => {
  loadingModels.value = true
  try {
    const res = await listModels()
    const allModels = res.models || []
    const prefix = lotteryType.value
    const filtered = allModels
      .filter(name => name.endsWith('.pt') && name.startsWith(prefix))
      .filter(name => !name.includes('_final'))   // 可选
      .map(name => {
        // 美化显示：提取参数信息
        const base = name.replace('.pt', '')
        const parts = base.split('_')
        // 例如 ssq_epochs200_bs128_seq100_lr0_0001_1234567890
        let label = base
        if (parts.length >= 5) {
          // 尝试提取关键参数
          const epochPart = parts.find(p => p.startsWith('epochs')) || ''
          const bsPart = parts.find(p => p.startsWith('bs')) || ''
          const seqPart = parts.find(p => p.startsWith('seq')) || ''
          const lrPart = parts.find(p => p.startsWith('lr')) || ''
          const timePart = parts[parts.length - 1] || ''
          label = `E${epochPart.replace('epochs','')} B${bsPart.replace('bs','')} S${seqPart.replace('seq','')} L${lrPart.replace('lr','').replace('_','.')} (${timePart})`
        }
        return {
          value: name,
          label: label
        }
      })
    // 按时间戳降序排列（最新在前）
    filtered.sort((a, b) => {
      const timeA = parseInt(a.value.split('_').pop().replace('.pt','')) || 0
      const timeB = parseInt(b.value.split('_').pop().replace('.pt','')) || 0
      return timeB - timeA
    })
    modelOptions.value = filtered
    // 清除已选但不再存在的模型
    selectedModels.value = selectedModels.value.filter(m =>
      filtered.some(item => item.value === m)
    )
    if (filtered.length === 0) {
      ElMessage.warning(`当前彩种 ${lotteryType.value === 'ssq' ? '双色球' : '大乐透'} 暂无可用模型，请先训练`)
    }
  } catch (e) {
    console.error('加载模型列表失败:', e)
    ElMessage.error('加载模型列表失败')
  } finally {
    loadingModels.value = false
  }
}

// 彩种切换
const onLotteryChange = () => {
  selectedModels.value = []
  results.value = []
  globalError.value = null
  loadModels()
}

// 模型选择变化（可在此处添加额外逻辑）
const onModelChange = (val) => {
  // 不做特殊处理
}

// 预测
const handlePredict = async () => {
  if (selectedModels.value.length === 0) {
    ElMessage.warning('请至少选择一个模型')
    return
  }

  loading.value = true
  globalError.value = null
  results.value = []

  const promises = selectedModels.value.map(async (modelName) => {
    try {
      const data = await getPrediction({
        lottery_type: lotteryType.value,
        model_name: modelName
      })
      return {
        modelName,
        success: true,
        data
      }
    } catch (error) {
      return {
        modelName,
        success: false,
        error: error.message || '预测失败'
      }
    }
  })

  const settledResults = await Promise.allSettled(promises)
  const finalResults = settledResults.map((item, index) => {
    if (item.status === 'fulfilled') {
      return item.value
    } else {
      return {
        modelName: selectedModels.value[index] || '未知模型',
        success: false,
        error: item.reason?.message || '请求异常'
      }
    }
  })

  results.value = finalResults

  const successCount = finalResults.filter(r => r.success).length
  if (successCount === finalResults.length) {
    ElMessage.success(`全部 ${successCount} 个模型预测成功`)
  } else if (successCount > 0) {
    ElMessage.warning(`${successCount}/${finalResults.length} 个模型预测成功，请查看详情`)
  } else {
    ElMessage.error('所有模型预测均失败')
  }

  loading.value = false
}

// 清空
const handleClear = () => {
  results.value = []
  globalError.value = null
}

// 生命周期
onMounted(() => {
  loadModels()
})
</script>

<style scoped>
/* 样式保持不变 */
.predict-container {
  padding: 0;
}
.predict-form .el-form-item {
  margin-bottom: 18px;
}
.btn-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.btn-group .el-button {
  flex: 1 0 auto;
  min-width: 80px;
}
.result-card {
  margin-bottom: 20px;
  height: 100%;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.model-name {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
}
.result-content {
  font-size: 14px;
  line-height: 1.8;
}
.ball-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.result-tag {
  margin: 2px 0;
}
.error-msg {
  padding: 10px 0;
}
@media (max-width: 768px) {
  .predict-form .el-form-item {
    margin-bottom: 14px;
  }
  .result-content {
    font-size: 13px;
  }
  .result-tag {
    font-size: 13px;
    padding: 0 10px;
    height: 28px;
  }
}
</style>