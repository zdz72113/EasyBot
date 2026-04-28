<template>
  <div class="poster-page">
    <el-row :gutter="24">
      <!-- 左侧：内容选择与配置 -->
      <el-col :span="8">
        <el-card class="config-panel">
          <template #header>
            <span>⚙️ 海报配置</span>
          </template>
          
          <!-- 内容选择 -->
          <div class="config-section">
            <label>选择内容</label>
            <el-select v-model="selectedContentId" style="width: 100%" filterable>
              <el-option
                v-for="item in contentOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </div>
          
          <!-- 模板选择 -->
          <div class="config-section">
            <label>海报模板</label>
            <el-select v-model="posterConfig.template" style="width: 100%">
              <el-option
                v-for="(tpl, key) in configStore.templates"
                :key="key"
                :label="tpl.name"
                :value="key"
              />
            </el-select>
          </div>
          
          <!-- 配色方案 -->
          <div class="config-section">
            <label>配色方案</label>
            <el-select v-model="posterConfig.colorScheme" style="width: 100%">
              <el-option
                v-for="(scheme, key) in configStore.colorSchemes"
                :key="key"
                :label="scheme.name"
                :value="key"
              />
            </el-select>
            
            <!-- 颜色预览 -->
            <div v-if="currentColors" class="color-preview">
              <div 
                class="color-box" 
                :style="{ background: currentColors.primary }"
                title="主题色"
              />
              <div 
                class="color-box" 
                :style="{ background: currentColors.background }"
                title="背景色"
              />
            </div>
          </div>
          
          <!-- 头部栏目标签（专业版式：顶部标签/标题/副标题） -->
          <div class="config-section">
            <label>顶部信息</label>
            <el-input v-model="posterConfig.headerTag" placeholder="栏目标签，如：本周热评">
              <template #prepend>栏目标签</template>
            </el-input>
            <el-input v-model="posterConfig.headerSubtitle" placeholder="英文副标题，如：KNOWLEDGE" style="margin-top: 8px">
              <template #prepend>副标题</template>
            </el-input>
            <div class="hint">标题自动使用内容标题，底部品牌可配置（见全局设置）</div>
          </div>

          <!-- 背景图（来自维度素材） -->
          <div class="config-section">
            <label>背景图片（可选）</label>
            <div v-if="posterConfig.backgroundImage" class="bg-preview">
              <el-image :src="posterConfig.backgroundImage" fit="cover" style="width: 100%; height: 100px; border-radius: 4px;" />
              <div class="bg-actions">
                <el-button type="primary" link size="small" @click="clearBg">清除</el-button>
              </div>
            </div>
            <el-alert v-else type="info" :closable="false" style="margin-bottom: 8px">
              可在素材页为问答维度生成图片，点击“用于海报”自动设置为背景。
            </el-alert>
          </div>

          <!-- 排版设置（精简） -->
          <div class="config-section">
            <label>排版微调</label>
            <el-form size="small" label-width="80px">
              <el-form-item label="正文字号">
                <el-slider v-model="posterConfig.bodyTextSize" :min="22" :max="46" :marks="{28:'', 34:'', 40:''}" show-stops />
              </el-form-item>
              <el-form-item label="段落间距">
                <el-slider v-model="posterConfig.paragraphSpacing" :min="20" :max="80" :marks="{30:'', 50:''}" />
              </el-form-item>
              <el-form-item label="行间距">
                <el-slider v-model="posterConfig.lineSpacing" :min="0" :max="30" :marks="{8:'', 15:''}" />
              </el-form-item>
            </el-form>
          </div>
          
          <!-- 生成按钮 -->
          <el-button 
            type="primary" 
            size="large" 
            style="width: 100%; margin-top: 16px"
            :loading="isGenerating"
            @click="generatePoster"
          >
            <el-icon><Picture /></el-icon>
            生成海报
          </el-button>
        </el-card>
      </el-col>
      
      <!-- 中间：预览 -->
      <el-col :span="8">
        <el-card class="preview-panel">
          <template #header>
            <span>👀 预览</span>
          </template>
          
          <div v-if="!posterImage" class="empty-preview">
            <el-icon :size="64" color="#dcdfe6"><Picture /></el-icon>
            <p>点击左侧「生成海报」按钮预览</p>
          </div>
          
          <div v-else class="poster-preview">
            <el-image :src="posterImage" fit="contain" :preview-src-list="[posterImage]" />
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：操作 -->
      <el-col :span="8">
        <el-card class="action-panel">
          <template #header>
            <span>💾 操作</span>
          </template>
          
          <div v-if="posterImage" class="actions">
            <el-button type="primary" size="large" style="width: 100%" @click="downloadPoster">
              <el-icon><Download /></el-icon>
              下载海报
            </el-button>
            
            <el-divider />
            
            <el-button 
              type="success" 
              style="width: 100%" 
              @click="goToVideo"
            >
              <el-icon><VideoCamera /></el-icon>
              用于视频创作
            </el-button>
          </div>
          
          <el-empty v-else description="生成海报后可进行操作" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useConfigStore, useContentStore } from '@/stores'
import { posterApi, contentApi } from '@/api'

const router = useRouter()
const configStore = useConfigStore()
const contentStore = useContentStore()

// 状态
const selectedContentId = ref('')
const isGenerating = ref(false)
const posterImage = ref('')

// 海报配置（从 store 初始化，并尝试读取背景图）
const posterConfig = ref({
  ...configStore.posterConfig,
  backgroundImage: '',
})

// 加载来自素材页的预设背景图
const loadBackgroundFromStore = () => {
  const saved = localStorage.getItem('poster_background_image')
  if (saved) {
    posterConfig.value.backgroundImage = saved
  }
}

onMounted(() => {
  loadBackgroundFromStore()
})

// 计算属性
const currentColors = computed(() => {
  return configStore.colorSchemes[posterConfig.value.colorScheme]
})

const contentOptions = computed(() => {
  const options: any[] = []
  
  // 当前内容
  if (contentStore.currentResult) {
    options.push({
      value: '__current__',
      label: `📌 当前: ${contentStore.currentResult.title}`
    })
  }
  
  // 历史记录
  contentStore.history.forEach((item: any) => {
    options.push({
      value: item.id,
      label: `${item.title} · ${formatDate(item.created_at)}`
    })
  })
  
  return options
})

const currentContent = computed(() => {
  if (selectedContentId.value === '__current__') {
    return contentStore.currentResult
  }
  return contentStore.history.find((h: any) => h.id === selectedContentId.value)
})

// 监听配置变化，自动保存
watch(posterConfig, (val) => {
  configStore.updatePosterConfig(val)
}, { deep: true })

// 初始化选中内容
if (contentStore.currentResult) {
  selectedContentId.value = '__current__'
} else if (contentStore.history.length > 0) {
  selectedContentId.value = contentStore.history[0].id
}

// 生成海报
const generatePoster = async () => {
  if (!currentContent.value) {
    ElMessage.warning('请先选择内容')
    return
  }
  
  isGenerating.value = true
  
  try {
    const res = await posterApi.generate(currentContent.value, posterConfig.value)
    if (res.code === 0) {
      posterImage.value = res.data.image_base64
      ElMessage.success('海报生成成功')
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (error: any) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    isGenerating.value = false
  }
}

// 下载海报
const downloadPoster = () => {
  if (!posterImage.value) return
  
  const link = document.createElement('a')
  link.href = posterImage.value
  link.download = `poster_${Date.now()}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 前往视频创作
const goToVideo = () => {
  if (posterImage.value) {
    localStorage.setItem('poster_for_video', posterImage.value)
    router.push('/video')
  }
}

// 清除背景图
const clearBg = () => {
  posterConfig.value.backgroundImage = ''
  localStorage.removeItem('poster_background_image')
  ElMessage.info('已清除背景图')
}

const formatDate = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.poster-page {
  max-width: 1600px;
  margin: 0 auto;
}

.config-panel,
.preview-panel,
.action-panel {
  height: calc(100vh - 140px);
  overflow-y: auto;
}

.config-section {
  margin-bottom: 20px;
}

.config-section label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.color-preview {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.color-box {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #909399;
}

.empty-preview p {
  margin-top: 16px;
}

.poster-preview {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
  height: calc(100vh - 200px);
  overflow: auto;
}

.poster-preview :deep(.el-image) {
  width: 100%;
  max-width: 540px;
  aspect-ratio: 9 / 16;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.poster-preview :deep(.el-image img) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.5;
}

.bg-preview {
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.bg-actions {
  padding: 8px;
  text-align: right;
  background: #f5f7fa;
}
</style>
