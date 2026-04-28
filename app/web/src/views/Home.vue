<template>
  <div class="home">
    <!-- 欢迎区 -->
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">🧠 EasyBot</h1>
        <p class="hero-desc">
          AI 驱动的知识学习与内容创作工作台<br>
          <span class="highlight">Learn</span> · 
          <span class="highlight">Create</span> · 
          <span class="highlight">Monetize</span>
        </p>
      </div>
    </div>

    <!-- 快速入口 -->
    <div class="quick-actions">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="action-card" shadow="hover" @click="$router.push('/content')">
            <el-icon class="action-icon"><Document /></el-icon>
            <h3>内容生成</h3>
            <p>输入主题，AI 自动生成「5个问题看懂」科普内容</p>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="action-card" shadow="hover" @click="$router.push('/materials')">
            <el-icon class="action-icon"><Collection /></el-icon>
            <h3>素材抓取</h3>
            <p>抓取网页内容，收集图片、链接等丰富素材</p>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="action-card" shadow="hover" @click="$router.push('/poster')">
            <el-icon class="action-icon"><Picture /></el-icon>
            <h3>海报制作</h3>
            <p>选择模板，一键生成精美知识海报</p>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="action-card" shadow="hover" @click="$router.push('/video')">
            <el-icon class="action-icon"><VideoCamera /></el-icon>
            <h3>视频创作</h3>
            <p>合成海报与音频，生成短视频</p>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 最近历史 -->
    <div class="recent-section">
      <div class="section-header">
        <h3>最近生成</h3>
        <el-button text @click="$router.push('/content')">
          查看全部 <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
      
      <el-empty v-if="!recentHistory.length" description="暂无历史记录" />
      
      <el-row v-else :gutter="16">
        <el-col :span="8" v-for="item in recentHistory" :key="item.id">
          <el-card class="history-card" shadow="hover" @click="viewContent(item)">
            <h4 class="history-title">{{ item.title }}</h4>
            <p class="history-summary">{{ item.summary || '暂无简介' }}</p>
            <div class="history-meta">
              <el-tag v-for="tag in item.tags.slice(0, 3)" :key="tag" size="small">
                {{ tag }}
              </el-tag>
              <span class="history-time">{{ formatTime(item.created_at) }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useContentStore } from '@/stores'

const router = useRouter()
const contentStore = useContentStore()

const recentHistory = computed(() => {
  return contentStore.history.slice(0, 6)
})

const viewContent = (item: any) => {
  contentStore.setCurrentResult(item)
  router.push('/content')
}

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.home {
  max-width: 1400px;
  margin: 0 auto;
}

.hero-section {
  text-align: center;
  padding: 40px 0;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  color: #C41E24;
  margin-bottom: 16px;
}

.hero-desc {
  font-size: 18px;
  color: #606266;
  line-height: 1.6;
}

.highlight {
  color: #C41E24;
  font-weight: 600;
}

.quick-actions {
  margin-bottom: 40px;
}

.action-card {
  cursor: pointer;
  text-align: center;
  padding: 20px;
  transition: all 0.3s;
}

.action-card:hover {
  transform: translateY(-4px);
}

.action-icon {
  font-size: 48px;
  color: #C41E24;
  margin-bottom: 16px;
}

.action-card h3 {
  font-size: 18px;
  margin-bottom: 8px;
  color: #303133;
}

.action-card p {
  font-size: 14px;
  color: #909399;
  line-height: 1.5;
}

.recent-section {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 18px;
  margin: 0;
}

.history-card {
  cursor: pointer;
  margin-bottom: 16px;
}

.history-title {
  font-size: 16px;
  margin: 0 0 8px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-summary {
  font-size: 13px;
  color: #606266;
  margin: 0 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  height: 40px;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.history-time {
  margin-left: auto;
  font-size: 12px;
  color: #909399;
}
</style>
