<template>
  <div class="app">
    <!-- 顶部导航 -->
    <el-header class="app-header">
      <div class="header-left">
        <el-icon class="logo-icon"><Brain /></el-icon>
        <span class="app-title">EasyBot</span>
        <span class="app-subtitle">知识创作工作台</span>
      </div>
      <el-menu
        :default-active="$route.path"
        class="header-menu"
        mode="horizontal"
        router
        :ellipsis="false"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/content">
          <el-icon><Document /></el-icon>
          <span>内容生成</span>
        </el-menu-item>
        <el-menu-item index="/materials">
          <el-icon><Collection /></el-icon>
          <span>素材管理</span>
        </el-menu-item>
        <el-menu-item index="/poster">
          <el-icon><Picture /></el-icon>
          <span>海报制作</span>
        </el-menu-item>
        <el-menu-item index="/video">
          <el-icon><VideoCamera /></el-icon>
          <span>视频创作</span>
        </el-menu-item>
      </el-menu>
      <div class="header-right">
        <el-button type="primary" text @click="showSettings">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </el-header>

    <!-- 主内容区 -->
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </main>

    <!-- 配置对话框 -->
    <el-dialog v-model="settingsVisible" title="系统配置" width="600px">
      <SettingsPanel />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useConfigStore, useContentStore } from '@/stores'
import { configApi, contentApi } from '@/api'
import SettingsPanel from '@/components/SettingsPanel.vue'

const route = useRoute()
const configStore = useConfigStore()
const contentStore = useContentStore()

const settingsVisible = ref(false)

const showSettings = () => {
  settingsVisible.value = true
}

// 初始化配置
onMounted(async () => {
  try {
    const [modelsRes, templatesRes, schemesRes] = await Promise.all([
      configApi.getModels(),
      configApi.getTemplates(),
      configApi.getColorSchemes(),
    ])
    
    if (modelsRes.code === 0) {
      configStore.setModels(modelsRes.data)
    }
    if (templatesRes.code === 0) {
      configStore.setTemplates(templatesRes.data)
    }
    if (schemesRes.code === 0) {
      configStore.setColorSchemes(schemesRes.data)
    }
    
    // 加载历史记录
    const historyRes = await contentApi.getHistory()
    if (historyRes.code === 0) {
      contentStore.setHistory(historyRes.data)
    }
  } catch (error: any) {
    ElMessage.error('初始化失败: ' + error.message)
  }
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
  color: #C41E24;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: #C41E24;
}

.app-subtitle {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.header-menu {
  flex: 1;
  justify-content: center;
  border-bottom: none;
}

.header-right {
  display: flex;
  align-items: center;
}

.app-main {
  flex: 1;
  padding: 20px;
  background: #f5f7fa;
}
</style>
