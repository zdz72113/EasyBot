<template>
  <div class="content-page">
    <!-- 输入区 -->
    <div class="input-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>📝 内容生成</span>
            <el-select v-model="currentModel" size="small" style="width: 150px">
              <el-option
                v-for="(cfg, key) in configStore.models"
                :key="key"
                :label="cfg.name"
                :value="key"
              />
            </el-select>
          </div>
        </template>
        
        <el-input
          v-model="inputQuery"
          type="textarea"
          :rows="4"
          placeholder="输入主题、一段文字或文章链接...\n例如：为什么手机要涨价了？"
          resize="none"
        />
        
        <div class="input-actions">
          <el-button 
            type="primary" 
            size="large" 
            :loading="isGenerating"
            @click="generate"
          >
            <el-icon><MagicStick /></el-icon>
            {{ isGenerating ? '生成中...' : '生成内容' }}
          </el-button>
          <el-button v-if="isGenerating" @click="stopGenerate">停止</el-button>
        </div>
        
        <!-- 流式输出显示 -->
        <div v-if="streamText" class="stream-output">
          <el-divider />
          <pre>{{ streamText }}</pre>
        </div>
      </el-card>
    </div>

    <!-- 结果展示区 -->
    <div v-if="currentResult" class="result-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>✨ 生成结果</span>
            <div class="header-actions">
              <el-button text @click="editMode = true">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button text @click="showRegenerate = true">
                <el-icon><Refresh /></el-icon> 重新生成
              </el-button>
            </div>
          </div>
        </template>
        
        <!-- 编辑模式 -->
        <div v-if="editMode" class="edit-form">
          <el-form label-position="top">
            <el-form-item label="标题">
              <el-input v-model="editForm.title" />
            </el-form-item>
            
            <el-form-item 
              v-for="(qa, idx) in editForm.qa_list" 
              :key="idx"
              :label="`Q${idx + 1} & A${idx + 1}`"
            >
              <el-input v-model="qa.q" placeholder="问题" style="margin-bottom: 8px" />
              <el-input 
                v-model="qa.a" 
                type="textarea" 
                :rows="2" 
                placeholder="回答"
              />
            </el-form-item>
            
            <el-form-item label="简介">
              <el-input v-model="editForm.summary" type="textarea" :rows="2" />
            </el-form-item>
            
            <el-form-item label="标签（空格分隔）">
              <el-input v-model="editForm.tagsText" />
            </el-form-item>
          </el-form>
          
          <div class="edit-actions">
            <el-button type="primary" @click="saveEdit">保存</el-button>
            <el-button @click="editMode = false">取消</el-button>
          </div>
        </div>
        
        <!-- 展示模式 -->
        <div v-else class="result-display">
          <h2 class="result-title">{{ currentResult.title }}</h2>
          <p v-if="currentResult.summary" class="result-summary">
            {{ currentResult.summary }}
          </p>
          
          <div class="qa-list">
            <div 
              v-for="(qa, idx) in currentResult.qa_list" 
              :key="idx" 
              class="qa-item"
            >
              <div class="question">
                <span class="q-badge">Q{{ idx + 1 }}</span>
                {{ qa.q }}
              </div>
              <div class="answer">{{ qa.a }}</div>
            </div>
          </div>
          
          <div class="result-tags">
            <el-tag v-for="tag in currentResult.tags" :key="tag" effect="plain">
              {{ tag }}
            </el-tag>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 历史记录 -->
    <div class="history-section">
      <el-card>
        <template #header>
          <span>📚 历史记录</span>
        </template>
        
        <el-empty v-if="!history.length" description="暂无历史记录" />
        
        <el-timeline v-else>
          <el-timeline-item
            v-for="item in history"
            :key="item.id"
            :timestamp="formatTime(item.created_at)"
            placement="top"
          >
            <el-card shadow="hover" @click="loadRecord(item)">
              <h4>{{ item.title }}</h4>
              <p class="timeline-summary">{{ item.summary }}</p>
              <div class="timeline-actions">
                <el-tag 
                  v-for="tag in item.tags.slice(0, 2)" 
                  :key="tag" 
                  size="small"
                  effect="plain"
                >
                  {{ tag }}
                </el-tag>
                <el-button 
                  type="danger" 
                  link 
                  size="small"
                  @click.stop="deleteRecord(item.id)"
                >
                  删除
                </el-button>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>

    <!-- 重新生成对话框 -->
    <el-dialog v-model="showRegenerate" title="重新生成" width="500px">
      <el-input
        v-model="regenerateInstruction"
        type="textarea"
        :rows="4"
        placeholder="描述如何调整内容，例如：把第二点写得更简洁；增加一段关于XX的说明..."
      />
      <template #footer>
        <el-button @click="showRegenerate = false">取消</el-button>
        <el-button type="primary" @click="regenerate" :loading="isRegenerating">
          重新生成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useConfigStore, useContentStore } from '@/stores'
import { contentApi } from '@/api'

const configStore = useConfigStore()
const contentStore = useContentStore()

// 状态
const inputQuery = ref('')
const isGenerating = ref(false)
const abortController = ref<AbortController | null>(null)
const editMode = ref(false)
const showRegenerate = ref(false)
const regenerateInstruction = ref('')
const isRegenerating = ref(false)

// 编辑表单
const editForm = ref<any>({
  title: '',
  qa_list: [],
  summary: '',
  tagsText: ''
})

// 计算属性
const currentModel = computed({
  get: () => configStore.currentModel,
  set: (val) => configStore.setModel(val)
})

const currentResult = computed(() => contentStore.currentResult)
const streamText = computed(() => contentStore.streamText)
const history = computed(() => contentStore.history)

// 监听当前结果，初始化编辑表单
watch(currentResult, (val) => {
  if (val) {
    editForm.value = {
      title: val.title,
      qa_list: JSON.parse(JSON.stringify(val.qa_list)),
      summary: val.summary,
      tagsText: val.tags?.join(' ') || ''
    }
  }
}, { immediate: true })

// 生成内容
const generate = async () => {
  if (!inputQuery.value.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  
  isGenerating.value = true
  contentStore.clearStreamText()
  contentStore.setIsGenerating(true)
  
  try {
    const response = await fetch('/api/content/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: inputQuery.value,
        model: currentModel.value
      })
    })
    
    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应')
    
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const text = line.slice(6)
          contentStore.appendStreamText(text)
        } else if (line.startsWith('event: complete')) {
          // 完成，刷新历史
          const res = await contentApi.getHistory()
          if (res.code === 0) {
            contentStore.setHistory(res.data)
            // 加载最新记录
            if (res.data.length > 0) {
              contentStore.setCurrentResult(res.data[0])
            }
          }
        }
      }
    }
    
    ElMessage.success('生成完成')
  } catch (error: any) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    isGenerating.value = false
    contentStore.setIsGenerating(false)
  }
}

const stopGenerate = () => {
  abortController.value?.abort()
  isGenerating.value = false
  contentStore.setIsGenerating(false)
}

// 保存编辑
const saveEdit = async () => {
  if (!currentResult.value?.id) return
  
  const tags = editForm.value.tagsText
    .split(/\s+/)
    .filter((t: string) => t.trim())
  
  const updated = {
    ...currentResult.value,
    title: editForm.value.title,
    qa_list: editForm.value.qa_list,
    summary: editForm.value.summary,
    tags,
  }
  
  try {
    const res = await contentApi.updateRecord(currentResult.value.id, updated)
    if (res.code === 0) {
      contentStore.setCurrentResult(updated)
      editMode.value = false
      ElMessage.success('保存成功')
      
      // 刷新历史
      const historyRes = await contentApi.getHistory()
      if (historyRes.code === 0) {
        contentStore.setHistory(historyRes.data)
      }
    }
  } catch (error: any) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

// 加载历史记录
const loadRecord = (item: any) => {
  contentStore.setCurrentResult(item)
}

// 删除记录
const deleteRecord = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除这条记录吗？', '提示', {
      type: 'warning'
    })
    
    const res = await contentApi.deleteRecord(id)
    if (res.code === 0) {
      ElMessage.success('删除成功')
      const historyRes = await contentApi.getHistory()
      if (historyRes.code === 0) {
        contentStore.setHistory(historyRes.data)
      }
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 重新生成
const regenerate = async () => {
  if (!currentResult.value?.id) return
  
  isRegenerating.value = true
  contentStore.clearStreamText()
  showRegenerate.value = false
  
  try {
    const response = await fetch('/api/content/regenerate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        record_id: currentResult.value.id,
        instruction: regenerateInstruction.value || '请润色内容',
        model: currentModel.value
      })
    })
    
    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应')
    
    const decoder = new TextDecoder()
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          contentStore.appendStreamText(line.slice(6))
        } else if (line.startsWith('event: complete')) {
          const res = await contentApi.getHistory()
          if (res.code === 0) {
            contentStore.setHistory(res.data)
            const updated = res.data.find((r: any) => r.id === currentResult.value.id)
            if (updated) {
              contentStore.setCurrentResult(updated)
            }
          }
        }
      }
    }
    
    ElMessage.success('重新生成完成')
  } catch (error: any) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    isRegenerating.value = false
  }
}

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.content-page {
  max-width: 1200px;
  margin: 0 auto;
}

.input-section,
.result-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.input-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.stream-output {
  margin-top: 16px;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
}

.stream-output pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
}

.result-title {
  color: #C41E24;
  margin: 0 0 16px;
  font-size: 24px;
}

.result-summary {
  color: #606266;
  font-style: italic;
  margin-bottom: 24px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.qa-list {
  margin-bottom: 24px;
}

.qa-item {
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-left: 4px solid #C41E24;
  border-radius: 0 8px 8px 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.question {
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.q-badge {
  background: #C41E24;
  color: white;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 14px;
}

.answer {
  color: #606266;
  line-height: 1.8;
  padding-left: 8px;
}

.result-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.edit-form {
  padding: 16px 0;
}

.edit-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.timeline-summary {
  font-size: 13px;
  color: #606266;
  margin: 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.timeline-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
</style>
