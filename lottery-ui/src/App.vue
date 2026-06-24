<template>
  <el-container>
    <el-header>
      <div class="logo">🎰 Open-Lottery-AI</div>
      <!-- PC 端水平菜单 -->
      <el-menu
        mode="horizontal"
        router
        background-color="#409EFF"
        text-color="#fff"
        active-text-color="#fff"
        class="pc-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/data">
          <el-icon><DataBoard /></el-icon>
          <span>数据管理</span>
        </el-menu-item>
        <el-menu-item index="/train">
          <el-icon><Cpu /></el-icon>
          <span>模型训练</span>
        </el-menu-item>
        <el-menu-item index="/predict">
          <el-icon><TrendCharts /></el-icon>
          <span>预测结果</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><DataAnalysis /></el-icon>
          <span>预测分析</span>
        </el-menu-item>
      </el-menu>

      <!-- 移动端汉堡菜单按钮 -->
      <div class="mobile-menu-btn" @click="drawer = true">
        <el-icon size="24"><Menu /></el-icon>
      </div>

      <!-- 移动端抽屉菜单 -->
      <el-drawer v-model="drawer" direction="rtl" size="200px" :with-header="false">
        <el-menu
          router
          background-color="#fff"
          text-color="#303133"
          active-text-color="#409EFF"
          @select="drawer = false"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/data">
            <el-icon><DataBoard /></el-icon>
            <span>数据管理</span>
          </el-menu-item>
          <el-menu-item index="/train">
            <el-icon><Cpu /></el-icon>
            <span>模型训练</span>
          </el-menu-item>
          <el-menu-item index="/predict">
            <el-icon><TrendCharts /></el-icon>
            <span>预测结果</span>
          </el-menu-item>
          <el-menu-item index="/analysis">
            <el-icon><DataAnalysis /></el-icon>
            <span>预测分析</span>
          </el-menu-item>
        </el-menu>
      </el-drawer>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import {
  Menu,
  House,
  DataBoard,
  Cpu,
  TrendCharts,
  DataAnalysis
} from '@element-plus/icons-vue'

const drawer = ref(false)
</script>

<style scoped>
.el-header {
  display: flex;
  align-items: center;
  background: #409EFF;
  color: white;
  padding: 0 20px;
  height: 60px;
}
.logo {
  font-size: 24px;
  font-weight: bold;
  margin-right: 40px;
  white-space: nowrap;
}
.pc-menu {
  flex: 1;
  background: transparent !important;
  border-bottom: none !important;
}
.pc-menu .el-menu-item {
  color: white !important;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.pc-menu .el-menu-item.is-active {
  background: rgba(255, 255, 255, 0.2) !important;
  border-bottom: 2px solid white !important;
}
.mobile-menu-btn {
  display: none;
  margin-left: auto;
  cursor: pointer;
  color: white;
}
.el-main {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}
/* 移动端菜单项样式 */
.el-drawer .el-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 响应式：小屏隐藏水平菜单，显示汉堡按钮 */
@media (max-width: 768px) {
  .pc-menu {
    display: none;
  }
  .mobile-menu-btn {
    display: block;
  }
  .logo {
    font-size: 20px;
  }
  .el-main {
    padding: 10px;
  }
}
</style>