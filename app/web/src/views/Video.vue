<template>
  <div class="video-page">
    <el-row :gutter="24">
      <!-- 左侧：素材与配置 -->
      <el-col :span="8">
        <el-card class="config-panel">
          <template #header>
            <span>🎬 视频配置</span>
          </template>
          
          <!-- 海报来源 -->
          <div class="config-section">
            <label>海报图片</label>
            <el-radio-group v-model="posterSource" style="width: 100%">
              <el-radio-button label="generated">使用生成的海报</el-radio-button>
              <el-radio-button label="dimension">维度素材图</el-radio-button>
              <el-radio-button label="upload">上传图片</el-radio-button>
            </el-radio-group>

            <div v-if="posterSource === 'dimension'" class="dimension-picker">
              <el-select
                v-model="selectedDimensionIndex"
                placeholder="选择一个内容维度素材"
                style="width: 100%"
                :disabled="!dimensionOptions.length"
              >
                <el-option
                  v-for="item in dimensionOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
              <p v-if="!dimensionOptions.length" class="hint">
                暂无维度素材，请先到素材页基于内容生成素材。
              </p>
            </div>
            
            <div v-if="posterSource === 'upload'" style="margin-top: 12px">
              <el-upload
                class="poster-uploader"
                action="#"
                :auto-upload="false"
                :on-change="handlePosterChange"
                :show-file-list="false"
                accept="image/*"
              >
                <img v-if="uploadedPoster" :src="uploadedPoster" class="uploaded-poster" />
                <el-icon v-else class="uploader-icon"><Plus /></el-icon>
              </el-upload>
            </div>
          </div>
          
          <!-- 音频配置 -->
          <div class="config-section">
            <label>音频来源</label>
            <el-radio-group v-model="audioSource" style="width: 100%">
              <el-radio-button label="music">背景音乐</el-radio-button>
              <el-radio-button label="upload">上传配音</el-radio-button>
            </el-radio-group>
            
            <!-- 背景音乐列表 -->
            <div v-if="audioSource === 'music'" style="margin-top: 12px">
              <el-select v-model="selectedAudio" style="width: 100%" placeholder="选择背景音乐">
                <el-option
                  v-for="audio in audioList"
                  :key="audio.path"
                  :label="audio.name"
                  :value="audio.path"
                />
              </el-select>
            </div>
            
            <!-- 上传配音 -->
            <div v-else style="margin-top: 12px">
              <el-upload
                action="#"
                :auto-upload="false"
                :on-change="handleAudioChange"
                :limit="1"
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon>
                  选择配音文件
                </el-button>
              </el-upload>
              
              <!-- 生成字幕 -->
              <el-button 
                v-if="uploadedAudio"
                type="success" 
                size="small" 
                style="margin-top: 12px; width: 100%"
                :loading="isGeneratingSubtitles"
                @click="generateSubtitles"
              >
                <el-icon><Microphone /></el-icon>
                生成字幕
              </el-button>
            </div>
          </div>
          
          <!-- 时长设置 -->
          <div class="config-section">
            <label>视频时长</label>
            <el-slider 
              v-model="videoDuration" 
              :min="5" 
              :max="60" 
              :step="5"
              show-stops
              show-input
            />
            <p class="hint" v-if="audioSource === 'upload' && uploadedAudio">
              配音时长会自动计算，当前设置仅供参考
            </p>
          </div>
          
          <!-- 分辨率 -->
          <div class="config-section">
            <label>分辨率</label>
            <el-radio-group v-model="resolution">
              <el-radio-button label="9:16">竖屏 9:16</el-radio-button>
              <el-radio-button label="16:9">横屏 16:9</el-radio-button>
              <el-radio-button label="1:1">方形 1:1</el-radio-button>
            </el-radio-group>
          </div>
          
          <!-- 生成按钮 -->
          <el-button 
            type="primary" 
            size="large" 
            style="width: 100%; margin-top: 16px"
            :loading="isGenerating"
            @click="generateVideo"
          >
            <el-icon><VideoPlay /></el-icon>
            生成视频
          </el-button>
        </el-card>
      </el-col>
      
      <!-- 中间：预览 -->
      <el-col :span="10">
        <el-card class="preview-panel">
          <template #header>
            <span>👀 预览</span>
          </template>
          
          <!-- 海报预览 -->
          <div v-if="currentPoster" class="poster-preview">
            <h4>海报预览</h4>
            <el-image :src="currentPoster" fit="contain" />
          </div>
          
          <el-empty v-else description="请先选择或上传海报" />
          
          <!-- 字幕预览 -->
          <div v-if="subtitles.length" class="subtitle-preview">
            <h4>字幕预览 ({{ subtitles.length }} 段)</h4>
            <el-timeline>
              <el-timeline-item
                v-for="(sub, idx) in subtitles.slice(0, 5)"
                :key="idx"
                :timestamp="formatTime(sub.start) + ' - ' + formatTime(sub.end)"
              >
                {{ sub.text }}
              </el-timeline-item>
            </el-timeline>
            <p v-if="subtitles.length > 5" class="more-hint">
              还有 {{ subtitles.length - 5 }} 段字幕...
            </p>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：结果 -->
      <el-col :span="6">
        <el-card class="result-panel">
          <template #header>
            <span>📥 结果</span>
          </template>
          
          <div v-if="videoUrl" class="video-result">
            <video 
              :src="videoUrl" 
              controls 
              style="width: 100%; border-radius: 4px;"
            />
            
            <el-button 
              type="primary" 
              style="width: 100%; margin-top: 12px"
              @click="downloadVideo"
            >
              <el-icon><Download /></el-icon>
              下载视频
            </el-button>
          </div>
          
          <el-empty v-else description="生成视频后显示结果" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useMaterialStore } from '@/stores'
import { videoApi } from '@/api'

const materialStore = useMaterialStore()

// 海报来源选项
const posterSource = ref<'generated' | 'dimension' | 'upload'>('generated')
const selectedDimensionIndex = ref<number | null>(null)

const audioSource = ref('music')
const selectedAudio = ref('')
const videoDuration = ref(30)
const resolution = ref('9:16')

const uploadedPoster = ref('')
const uploadedAudioFile = ref<File | null>(null)
const uploadedAudio = ref('')

const audioList = ref<any[]>([])
const subtitles = ref<any[]>([])
const isGeneratingSubtitles = ref(false)
const isGenerating = ref(false)
const videoUrl = ref('')

// 维度素材选项
const dimensionOptions = computed(() => {
  if (!materialStore.dimensionBundle) return []
  return materialStore.dimensionBundle.dimensions.map((d, idx) => ({
    label: d.title,
    value: idx,
    thumb: d.generated_image || d.images[0]?.url,
  }))
})

// 计算属性：当前使用的海报
const currentPoster = computed(() => {
  if (posterSource.value === 'generated') {
    return localStorage.getItem('poster_for_video') || ''
  }
  if (posterSource.value === 'dimension') {
    const idx = selectedDimensionIndex.value
    if (idx == null || !materialStore.dimensionBundle) return ''
    const dim = materialStore.dimensionBundle.dimensions[idx]
    return dim?.generated_image || dim?.images?.[0]?.url || ''
  }
  return uploadedPoster.value
})

// 加载音频列表
onMounted(async () => {
  try {
    const res = await videoApi.getAudioList()
    if (res.code === 0) {
      audioList.value = res.data
      if (res.data.length > 0) {
        selectedAudio.value = res.data[0].path
      }
    }
  } catch (error) {
    console.error('加载音频列表失败', error)
  }
  
  // 检查本地存储的海报
  const savedPoster = localStorage.getItem('poster_for_video')
  if (savedPoster) {
    uploadedPoster.value = savedPoster
  }
  if (dimensionOptions.value.length && selectedDimensionIndex.value === null) {
    selectedDimensionIndex.value = 0
  }
})

// 处理海报上传
const handlePosterChange = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedPoster.value = e.target?.result as string
  }
  reader.readAsDataURL(file.raw)
}

// 处理音频上传
const handleAudioChange = (file: any) => {
  uploadedAudioFile.value = file.raw
  uploadedAudio.value = file.name
}

// 生成字幕
const generateSubtitles = async () => {
  if (!uploadedAudioFile.value) {
    ElMessage.warning('请先上传配音文件')
    return
  }
  
  isGeneratingSubtitles.value = true
  
  try {
    const res = await videoApi.generateSubtitles(uploadedAudioFile.value)
    if (res.code === 0) {
      subtitles.value = res.data
      ElMessage.success(`生成成功，共 ${res.data.length} 段字幕`)
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (error: any) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    isGeneratingSubtitles.value = false
  }
}

// 生成视频
const generateVideo = async () => {
  if (!currentPoster.value) {
    ElMessage.warning('请先选择海报')
    return
  }
  
  if (audioSource.value === 'music' && !selectedAudio.value) {
    ElMessage.warning('请选择背景音乐')
    return
  }
  
  isGenerating.value = true
  
  try {
    const config = {
      audio_path: audioSource.value === 'music' ? selectedAudio.value : null,
      duration: videoDuration.value,
      resolution: resolution.value,
    }
    
    const res = await videoApi.generate(currentPoster.value, config)
    if (res.code === 0) {
      videoUrl.value = res.data.download_url
      ElMessage.success('视频生成成功')
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (error: any) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    isGenerating.value = false
  }
}

// 下载视频
const downloadVideo = () => {
  if (!videoUrl.value) return
  
  const link = document.createElement('a')
  link.href = videoUrl.value
  link.download = `video_${Date.now()}.mp4`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.video-page {
  max-width: 1600px;
  margin: 0 auto;
}

.config-panel,
.preview-panel,
.result-panel {
  height: calc(100vh - 140px);
  overflow-y: auto;
}

.config-section {
  margin-bottom: 24px;
}

.config-section label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.dimension-picker {
  margin-top: 12px;
}

.poster-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.poster-uploader:hover {
  border-color: #409eff;
}

.uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100%;
  height: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.uploaded-poster {
  width: 100%;
  height: 200px;
  object-fit: contain;
}

.poster-preview {
  text-align: center;
  margin-bottom: 24px;
}

.poster-preview h4 {
  margin-bottom: 12px;
  color: #606266;
}

.poster-preview :deep(.el-image) {
  max-height: 300px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.subtitle-preview {
  border-top: 1px solid #e4e7ed;
  padding-top: 16px;
}

.subtitle-preview h4 {
  margin-bottom: 12px;
  color: #606266;
}

.more-hint {
  text-align: center;
  color: #909399;
  font-size: 12px;
}

.video-result video {
  background: #000;
}
</style>
