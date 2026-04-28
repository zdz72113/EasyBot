<template>
  <div class="settings-panel">
    <el-tabs v-model="activeTab">
      <!-- AI 模型配置 -->
      <el-tab-pane label="AI 模型" name="models">
        <el-form :model="modelForm" label-position="top">
          <el-alert
            title="配置说明"
            description="支持 DeepSeek、通义千问等 OpenAI 兼容接口的模型。API Key 仅在本地存储。"
            type="info"
            :closable="false"
            style="margin-bottom: 16px"
          />
          
          <div v-for="(model, key) in modelForm.models" :key="key" class="model-section">
            <el-divider content-position="left">{{ model.name }}</el-divider>
            
            <el-form-item :label="`${model.name} API Key`">
              <el-input 
                v-model="model.api_key" 
                type="password" 
                show-password
                placeholder="sk-..."
              />
            </el-form-item>
            
            <el-form-item label="Base URL">
              <el-input v-model="model.base_url" placeholder="https://api.example.com/v1" />
            </el-form-item>
            
            <el-form-item label="模型名称">
              <el-input v-model="model.model" placeholder="model-name" />
            </el-form-item>
          </div>
          
          <el-form-item>
            <el-button type="primary" @click="saveModels">保存配置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      
      <!-- 素材抓取配置 -->
      <el-tab-pane label="素材抓取" name="fetcher">
        <el-form :model="fetcherForm" label-position="top">
          <el-alert
            title="Jina AI Reader (推荐)"
            description="免费且无需 API Key，支持高质量网页内容提取。访问 https://r.jina.ai/http://example.com 即可使用。"
            type="success"
            :closable="false"
            style="margin-bottom: 16px"
          />
          
          <el-form-item label="Jina API Key (可选)">
            <el-input v-model="fetcherForm.jina_api_key" placeholder="可选，免费版无需填写" />
          </el-form-item>
          
          <el-divider />
          
          <el-alert
            title="Firecrawl"
            description="更强大的结构化数据抓取，支持提取图片、链接列表。需要 API Key。"
            type="info"
            :closable="false"
            style="margin-bottom: 16px"
          />
          
          <el-form-item label="Firecrawl API Key">
            <el-input 
              v-model="fetcherForm.firecrawl_api_key" 
              type="password"
              placeholder="从 firecrawl.dev 获取"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="saveFetcher">保存配置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      
      <!-- 关于 -->
      <el-tab-pane label="关于" name="about">
        <div class="about-section">
          <h2>EasyBot v2.0</h2>
          <p>AI 驱动的知识学习与内容创作工作台</p>
          
          <el-divider />
          
          <h4>技术栈</h4>
          <ul>
            <li>后端: FastAPI + Python</li>
            <li>前端: Vue3 + Element Plus</li>
            <li>AI: OpenAI 兼容接口</li>
            <li>视频: MoviePy + FFmpeg</li>
          </ul>
          
          <el-divider />
          
          <p class="copyright">© 2024 EasyBot · Learn. Create. Monetize.</p>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi } from '@/api'

const activeTab = ref('models')

const modelForm = ref({
  models: {} as Record<string, any>
})

const fetcherForm = ref({
  jina_api_key: '',
  firecrawl_api_key: ''
})

// 加载配置
onMounted(async () => {
  try {
    const res = await configApi.get()
    if (res.code === 0) {
      modelForm.value.models = res.data.llm_models || {}
      fetcherForm.value.jina_api_key = res.data.fetcher?.jina_api_key || ''
      fetcherForm.value.firecrawl_api_key = res.data.fetcher?.firecrawl_api_key || ''
    }
  } catch (error: any) {
    ElMessage.error('加载配置失败: ' + error.message)
  }
})

// 保存模型配置
const saveModels = async () => {
  try {
    const res = await configApi.get()
    if (res.code === 0) {
      const config = res.data
      config.llm_models = modelForm.value.models
      
      const saveRes = await configApi.update(config)
      if (saveRes.code === 0) {
        ElMessage.success('保存成功')
      }
    }
  } catch (error: any) {
    ElMessage.error('保存失败: ' + error.message)
  }
}

// 保存抓取配置
const saveFetcher = async () => {
  try {
    const res = await configApi.get()
    if (res.code === 0) {
      const config = res.data
      config.fetcher = {
        jina_api_key: fetcherForm.value.jina_api_key,
        firecrawl_api_key: fetcherForm.value.firecrawl_api_key
      }
      
      const saveRes = await configApi.update(config)
      if (saveRes.code === 0) {
        ElMessage.success('保存成功')
      }
    }
  } catch (error: any) {
    ElMessage.error('保存失败: ' + error.message)
  }
}
</script>

<style scoped>
.settings-panel {
  padding: 8px;
}

.model-section {
  margin-bottom: 16px;
}

.about-section {
  text-align: center;
  padding: 24px;
}

.about-section h2 {
  color: #C41E24;
  margin-bottom: 8px;
}

.about-section h4 {
  color: #606266;
  margin-bottom: 12px;
}

.about-section ul {
  list-style: none;
  padding: 0;
  color: #606266;
}

.about-section li {
  padding: 4px 0;
}

.copyright {
  color: #909399;
  font-size: 12px;
  margin-top: 24px;
}
</style>
