<template>
  <div class="materials-page">
    <!-- 按内容生成维度素材 -->
    <el-card class="dimension-section">
      <template #header>
        <div class="dimension-header">
          <span>🎯 按内容维度生成素材</span>
          <el-tag v-if="dimensionBundle" type="success" effect="plain">
            已生成 {{ dimensionBundle.dimensions.length }} 个维度
          </el-tag>
        </div>
      </template>

      <div class="dimension-toolbar">
        <el-select
          v-model="selectedContentId"
          placeholder="选择一条内容（来自历史记录）"
          style="flex: 1; min-width: 240px"
          filterable
          clearable
        >
          <el-option
            v-for="item in contentOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <el-input-number
          v-model="imageLimit"
          :min="1"
          :max="12"
          size="default"
        />
        <span class="hint-inline">图/维度</span>

        <el-input-number
          v-model="videoLimit"
          :min="0"
          :max="6"
          size="default"
        />
        <span class="hint-inline">视频/维度</span>

        <el-checkbox v-model="generateSimpleImage">生成简单图片</el-checkbox>

        <el-button
          type="primary"
          :loading="materialStore.isGeneratingDimensions"
          @click="generateDimensionMaterials"
        >
          <el-icon><MagicStick /></el-icon>
          生成维度素材
        </el-button>
      </div>

      <el-empty
        v-if="!dimensionBundle && !materialStore.isGeneratingDimensions"
        description="选择内容后，按 Q1-Q5 维度生成关键词、提示词与图片/视频候选"
      />

      <div v-if="dimensionBundle" class="dimension-list">
        <el-card
          v-for="dim in dimensionBundle.dimensions"
          :key="dim.dimension_id"
          shadow="hover"
          class="dimension-card"
        >
          <div class="dim-header">
            <div class="dim-title">{{ dim.title }}</div>
            <div class="dim-meta">
              <el-tag
                v-for="kw in dim.keywords"
                :key="kw"
                size="small"
                effect="plain"
                class="dim-keyword"
              >
                #{{ kw }}
              </el-tag>
            </div>
          </div>

          <div v-if="dim.answer" class="dim-answer">{{ dim.answer }}</div>

          <el-collapse class="dim-detail">
            <el-collapse-item title="🖼️ 图片候选" :name="dim.dimension_id + '-img'">
              <div v-if="dim.generated_image || dim.images.length" class="dim-images">
                <div v-if="dim.generated_image" class="dim-image-item generated">
                  <el-image
                    :src="dim.generated_image"
                    :preview-src-list="[dim.generated_image]"
                    fit="cover"
                  />
                  <div class="image-caption">简单生成图</div>
                  <el-button
                    type="primary"
                    link
                    size="small"
                    @click="useImage(dim.generated_image, dim.title)"
                  >
                    用于海报
                  </el-button>
                </div>

                <div
                  v-for="(img, idx) in dim.images"
                  :key="idx"
                  class="dim-image-item"
                >
                  <el-image
                    :src="img.url"
                    :preview-src-list="[img.url]"
                    fit="cover"
                  >
                    <template #error>
                      <div class="image-error">{{ img.title || img.content }}</div>
                    </template>
                  </el-image>
                  <div class="image-caption" :title="img.title">
                    {{ img.title || img.content }}
                  </div>
                  <el-button
                    v-if="img.url"
                    type="primary"
                    link
                    size="small"
                    @click="useImage(img.url, dim.title)"
                  >
                    用于海报
                  </el-button>
                </div>
              </div>
              <el-empty v-else description="暂无图片候选" :image-size="60" />
            </el-collapse-item>

            <el-collapse-item title="🎞️ 视频搜索入口" :name="dim.dimension_id + '-video'">
              <ul class="dim-links">
                <li v-for="(v, idx) in dim.videos" :key="idx">
                  <el-link type="primary" :href="v.url" target="_blank">
                    {{ v.title }}
                  </el-link>
                </li>
                <li v-if="!dim.videos.length" class="dim-empty">暂无</li>
              </ul>
            </el-collapse-item>

            <el-collapse-item title="✨ 图片提示词" :name="dim.dimension_id + '-prompt'">
              <div class="dim-prompt">
                <pre>{{ dim.image_prompt }}</pre>
                <el-button size="small" @click="copyText(dim.image_prompt)">复制</el-button>
              </div>
            </el-collapse-item>
          </el-collapse>

          <div v-if="dim.warnings && dim.warnings.length" class="dim-warnings">
            <el-alert
              v-for="(w, idx) in dim.warnings"
              :key="idx"
              :title="w"
              type="warning"
              :closable="false"
              show-icon
            />
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 抓取区 -->
    <el-card class="fetch-section">
      <template #header>
        <span>🔗 素材抓取</span>
      </template>
      
      <div class="fetch-form">
        <el-input
          v-model="fetchUrl"
          placeholder="输入网页链接，支持自动抓取正文、图片、链接等素材"
          size="large"
        >
          <template #append>
            <el-button 
              type="primary" 
              :loading="isFetching"
              @click="fetchContent"
            >
              <el-icon><Download /></el-icon>
              抓取
            </el-button>
          </template>
        </el-input>
        
        <div class="fetch-options">
          <el-radio-group v-model="fetchMethod" size="small">
            <el-radio-button label="auto">自动选择</el-radio-button>
            <el-radio-button label="jina">Jina AI</el-radio-button>
            <el-radio-button label="firecrawl">Firecrawl</el-radio-button>
            <el-radio-button label="basic">基础爬虫</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <!-- 抓取结果 -->
      <div v-if="fetchResult" class="fetch-result">
        <el-divider />
        
        <div class="result-header">
          <h3>{{ fetchResult.title || '未命名页面' }}</h3>
          <el-button type="primary" @click="saveToLibrary">
            <el-icon><Plus /></el-icon>
            保存到素材库
          </el-button>
        </div>
        
        <p class="result-url">{{ fetchResult.url }}</p>
        
        <!-- 内容预览 -->
        <el-collapse v-model="activePanels">
          <el-collapse-item title="📄 正文内容" name="content">
            <div class="content-preview">
              {{ fetchResult.content?.slice(0, 1000) }}...
            </div>
          </el-collapse-item>
          
          <!-- 图片素材 -->
          <el-collapse-item 
            :title="`🖼️ 图片素材 (${imageMaterials.length})`" 
            name="images"
            v-if="imageMaterials.length"
          >
            <div class="materials-grid">
              <div 
                v-for="(img, idx) in imageMaterials.slice(0, 12)" 
                :key="idx"
                class="material-item"
              >
                <el-image 
                  :src="img.url" 
                  :preview-src-list="[img.url]"
                  fit="cover"
                  style="width: 100%; height: 150px; border-radius: 4px;"
                >
                  <template #error>
                    <div class="image-error">加载失败</div>
                  </template>
                </el-image>
                <p class="material-title" :title="img.title">{{ img.title || '无标题' }}</p>
              </div>
            </div>
          </el-collapse-item>
          
          <!-- 链接素材 -->
          <el-collapse-item 
            :title="`🔗 相关链接 (${linkMaterials.length})`" 
            name="links"
            v-if="linkMaterials.length"
          >
            <el-table :data="linkMaterials.slice(0, 20)" size="small">
              <el-table-column prop="title" label="标题" min-width="200">
                <template #default="{ row }">
                  <el-link type="primary" :href="row.url" target="_blank">
                    {{ row.title || row.url }}
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column prop="url" label="链接" show-overflow-tooltip />
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>

    <!-- 素材库 -->
    <el-card class="library-section">
      <template #header>
        <div class="library-header">
          <span>📚 素材库</span>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索素材..."
            size="small"
            style="width: 200px"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>
      
      <el-empty v-if="!filteredMaterials.length" description="素材库为空，请先抓取网页" />
      
      <div v-else class="library-grid">
        <el-card 
          v-for="(item, idx) in filteredMaterials" 
          :key="idx"
          class="library-item"
          shadow="hover"
        >
          <div class="item-preview">
            <!-- 图片类型 -->
            <el-image
              v-if="item.type === 'image'"
              :src="item.url"
              fit="cover"
              style="width: 100%; height: 160px;"
            />
            <!-- 文本类型 -->
            <div v-else-if="item.type === 'text'" class="text-preview">
              {{ item.content.slice(0, 200) }}...
            </div>
            <!-- 链接类型 -->
            <div v-else-if="item.type === 'link'" class="link-preview">
              <el-icon><Link /></el-icon>
              <p>{{ item.title || '链接' }}</p>
            </div>
          </div>
          
          <div class="item-info">
            <p class="item-title" :title="item.title">{{ item.title || '未命名' }}</p>
            <p class="item-meta">{{ item.type }} · {{ formatTime(item.savedAt) }}</p>
          </div>
          
          <div class="item-actions">
            <el-button 
              v-if="item.type === 'image'" 
              type="primary" 
              link 
              size="small"
              @click="useInPoster(item)"
            >
              用于海报
            </el-button>
            <el-button type="danger" link size="small" @click="removeMaterial(idx)">
              删除
            </el-button>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useMaterialStore, useContentStore } from '@/stores'
import { fetcherApi, materialApi, contentApi } from '@/api'

const materialStore = useMaterialStore()
const contentStore = useContentStore()
const router = useRouter()

// 状态
const fetchUrl = ref('')
const fetchMethod = ref('auto')
const isFetching = ref(false)
const fetchResult = ref<any>(null)
const activePanels = ref(['content'])
const searchKeyword = ref('')

// 计算属性
const imageMaterials = computed(() => {
  return fetchResult.value?.materials?.filter((m: any) => m.type === 'image') || []
})

const linkMaterials = computed(() => {
  return fetchResult.value?.materials?.filter((m: any) => m.type === 'link') || []
})

const filteredMaterials = computed(() => {
  const keyword = searchKeyword.value.toLowerCase()
  if (!keyword) return materialStore.materials
  
  return materialStore.materials.filter((m: any) => 
    m.title?.toLowerCase().includes(keyword) ||
    m.content?.toLowerCase().includes(keyword)
  )
})

// 维度素材生成
const selectedContentId = ref('')
const imageLimit = ref(5)
const videoLimit = ref(3)
const generateSimpleImage = ref(true)

const dimensionBundle = computed(() => materialStore.dimensionBundle)

const contentOptions = computed(() => {
  const options: any[] = []
  if (contentStore.currentResult) {
    options.push({
      value: '__current__',
      label: `📌 当前: ${contentStore.currentResult.title || '未命名内容'}`,
    })
  }
  contentStore.history.forEach((item: any) => {
    options.push({
      value: item.id,
      label: `${item.title} · ${formatTime(item.created_at)}`,
    })
  })
  return options
})

const resolveContent = () => {
  if (selectedContentId.value === '__current__') return contentStore.currentResult
  return contentStore.history.find((h: any) => h.id === selectedContentId.value)
}

const generateDimensionMaterials = async () => {
  const target = resolveContent()
  if (!target) {
    ElMessage.warning('请先选择内容')
    return
  }
  if (!target.qa_list?.length) {
    ElMessage.warning('该内容缺少问答，无法生成维度素材')
    return
  }
  
  materialStore.setIsGeneratingDimensions(true)
  try {
    const res = await materialApi.generateFromContent(target, {
      imageLimit: imageLimit.value,
      videoLimit: videoLimit.value,
      generateSimpleImage: generateSimpleImage.value,
    })
    if (res.code === 0) {
      materialStore.setDimensionBundle({
        contentId: target.id || '__current__',
        title: res.data.title,
        dimensions: res.data.dimensions,
        generatedAt: new Date().toISOString(),
      })
      ElMessage.success('维度素材生成成功')
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (error: any) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    materialStore.setIsGeneratingDimensions(false)
  }
}

const useImage = (url: string, label: string) => {
  if (!url) return
  localStorage.setItem('poster_background_image', url)
  localStorage.setItem('poster_background_label', label || '')
  ElMessage.success('已设置为海报背景图，前往海报页查看')
  router.push('/poster')
}

const copyText = async (text: string) => {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制提示词')
  } catch {
    ElMessage.warning('复制失败，请手动选择文本')
  }
}

onMounted(async () => {
  if (!contentStore.history.length) {
    try {
      const res = await contentApi.getHistory()
      if (res.code === 0) contentStore.setHistory(res.data)
    } catch {
      // ignore，素材页主流程不依赖历史
    }
  }
  if (contentStore.currentResult) {
    selectedContentId.value = '__current__'
  } else if (contentStore.history.length > 0) {
    selectedContentId.value = contentStore.history[0].id
  }
})

// 抓取内容
const fetchContent = async () => {
  if (!fetchUrl.value.trim()) {
    ElMessage.warning('请输入链接')
    return
  }
  
  isFetching.value = true
  materialStore.setIsFetching(true)
  
  try {
    const res = await fetcherApi.fetch(fetchUrl.value, fetchMethod.value)
    if (res.code === 0) {
      fetchResult.value = res.data
      materialStore.setCurrentFetchResult(res.data)
      ElMessage.success('抓取成功')
    } else {
      ElMessage.error(res.message || '抓取失败')
    }
  } catch (error: any) {
    ElMessage.error('抓取失败: ' + error.message)
  } finally {
    isFetching.value = false
    materialStore.setIsFetching(false)
  }
}

// 保存到素材库
const saveToLibrary = () => {
  if (!fetchResult.value) return
  
  // 保存正文
  if (fetchResult.value.content) {
    materialStore.addMaterial({
      type: 'text',
      title: fetchResult.value.title,
      content: fetchResult.value.content,
      url: fetchResult.value.url,
      savedAt: new Date().toISOString()
    })
  }
  
  // 保存图片
  imageMaterials.value.forEach((img: any) => {
    materialStore.addMaterial({
      type: 'image',
      title: img.title,
      url: img.url,
      savedAt: new Date().toISOString()
    })
  })
  
  // 保存链接
  linkMaterials.value.slice(0, 5).forEach((link: any) => {
    materialStore.addMaterial({
      type: 'link',
      title: link.title,
      url: link.url,
      savedAt: new Date().toISOString()
    })
  })
  
  ElMessage.success('已保存到素材库')
}

// 删除素材
const removeMaterial = (idx: number) => {
  materialStore.removeMaterial(idx)
  ElMessage.success('已删除')
}

// 用于海报：从素材库挑图
const useInPoster = (item: any) => {
  if (!item?.url) {
    ElMessage.warning('该素材缺少链接')
    return
  }
  useImage(item.url, item.title || '')
}

function formatTime(isoString?: string) {
  if (!isoString) return '未知'
  const date = new Date(isoString)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.materials-page {
  max-width: 1400px;
  margin: 0 auto;
}

.fetch-section {
  margin-bottom: 24px;
}

.fetch-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.fetch-options {
  display: flex;
  justify-content: center;
}

.fetch-result {
  margin-top: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-header h3 {
  margin: 0;
  font-size: 18px;
}

.result-url {
  color: #909399;
  font-size: 13px;
  margin-bottom: 16px;
}

.content-preview {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
  max-height: 300px;
  overflow-y: auto;
}

.materials-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.material-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.material-title {
  margin: 8px;
  font-size: 12px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  font-size: 12px;
}

.library-section {
  margin-bottom: 24px;
}

.library-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.library-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.library-item {
  cursor: pointer;
  transition: all 0.3s;
}

.library-item:hover {
  transform: translateY(-2px);
}

.item-preview {
  height: 160px;
  overflow: hidden;
  background: #f5f7fa;
}

.text-preview {
  padding: 16px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  overflow: hidden;
}

.link-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.link-preview .el-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.item-info {
  padding: 12px;
}

.item-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.item-actions {
  display: flex;
  justify-content: space-between;
  padding: 0 12px 12px;
}

.dimension-section {
  margin-bottom: 24px;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dimension-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.hint-inline {
  font-size: 12px;
  color: #909399;
}

.dimension-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.dimension-card {
  display: flex;
  flex-direction: column;
}

.dim-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.dim-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.dim-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.dim-keyword {
  background: #f5f7fa;
}

.dim-answer {
  font-size: 13px;
  color: #606266;
  line-height: 1.7;
  margin-bottom: 12px;
  background: #fafafa;
  padding: 10px 12px;
  border-radius: 4px;
  border-left: 3px solid #c41e24;
}

.dim-detail {
  border-top: 1px solid #ebeef5;
}

.dim-images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.dim-image-item {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.dim-image-item.generated {
  border-color: #c41e24;
}

.dim-image-item :deep(.el-image) {
  width: 100%;
  height: 140px;
}

.dim-image-item .image-caption {
  padding: 6px 8px;
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dim-image-item .image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 12px;
  color: #909399;
  padding: 8px;
  text-align: center;
}

.dim-links {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
}

.dim-links li {
  margin-bottom: 4px;
}

.dim-empty {
  list-style: none;
  color: #909399;
}

.dim-prompt {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dim-prompt pre {
  margin: 0;
  white-space: pre-wrap;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
}

.dim-warnings {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
</style>
