import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// ============ 全局配置 Store ============

export const useConfigStore = defineStore('config', () => {
  // 模型配置
  const currentModel = ref('deepseek')
  const models = ref<Record<string, any>>({})
  
  // 海报配置
  const posterConfig = ref({
    template: '知识科普',
    colorScheme: '经典红',
    headerTitle: '知识科普',
    headerSubtitle: 'KNOWLEDGE',
    headerTag: '本周热评',
    bodyTextSize: 34,
    paragraphSpacing: 50,
    lineSpacing: 15,
    backgroundImage: '',
  })
  
  // 配色方案
  const colorSchemes = ref<Record<string, any>>({})
  
  // 模板列表
  const templates = ref<Record<string, any>>({})
  
  const setModel = (model: string) => {
    currentModel.value = model
  }
  
  const setModels = (data: Record<string, any>) => {
    models.value = data
  }
  
  const setColorSchemes = (data: Record<string, any>) => {
    colorSchemes.value = data
  }
  
  const setTemplates = (data: Record<string, any>) => {
    templates.value = data
  }
  
  const updatePosterConfig = (config: Partial<typeof posterConfig.value>) => {
    posterConfig.value = { ...posterConfig.value, ...config }
  }
  
  return {
    currentModel,
    models,
    posterConfig,
    colorSchemes,
    templates,
    setModel,
    setModels,
    setColorSchemes,
    setTemplates,
    updatePosterConfig,
  }
})

// ============ 内容 Store ============

export const useContentStore = defineStore('content', () => {
  // 当前生成结果
  const currentResult = ref<any>(null)
  const currentQuery = ref('')
  const isGenerating = ref(false)
  
  // 流式输出文本
  const streamText = ref('')
  
  // 历史记录
  const history = ref<any[]>([])
  
  const setCurrentResult = (result: any) => {
    currentResult.value = result
  }
  
  const setCurrentQuery = (query: string) => {
    currentQuery.value = query
  }
  
  const setIsGenerating = (value: boolean) => {
    isGenerating.value = value
  }
  
  const appendStreamText = (text: string) => {
    streamText.value += text
  }
  
  const clearStreamText = () => {
    streamText.value = ''
  }
  
  const setHistory = (records: any[]) => {
    history.value = records
  }
  
  return {
    currentResult,
    currentQuery,
    isGenerating,
    streamText,
    history,
    setCurrentResult,
    setCurrentQuery,
    setIsGenerating,
    appendStreamText,
    clearStreamText,
    setHistory,
  }
})

// ============ 素材 Store ============

export interface DimensionMaterial {
  dimension_id: string
  title: string
  question: string
  answer: string
  keywords: string[]
  image_prompt: string
  images: any[]
  videos: any[]
  generated_image?: string | null
  warnings?: string[]
}

export interface DimensionMaterialBundle {
  contentId: string
  title: string
  dimensions: DimensionMaterial[]
  generatedAt: string
}

export const useMaterialStore = defineStore('material', () => {
  const currentFetchResult = ref<any>(null)
  const isFetching = ref(false)
  const materials = ref<any[]>([])
  
  const dimensionBundle = ref<DimensionMaterialBundle | null>(null)
  const isGeneratingDimensions = ref(false)
  
  const setCurrentFetchResult = (result: any) => {
    currentFetchResult.value = result
  }
  
  const setIsFetching = (value: boolean) => {
    isFetching.value = value
  }
  
  const addMaterial = (material: any) => {
    materials.value.unshift(material)
  }
  
  const removeMaterial = (index: number) => {
    materials.value.splice(index, 1)
  }
  
  const setDimensionBundle = (bundle: DimensionMaterialBundle | null) => {
    dimensionBundle.value = bundle
  }
  
  const setIsGeneratingDimensions = (value: boolean) => {
    isGeneratingDimensions.value = value
  }
  
  return {
    currentFetchResult,
    isFetching,
    materials,
    dimensionBundle,
    isGeneratingDimensions,
    setCurrentFetchResult,
    setIsFetching,
    addMaterial,
    removeMaterial,
    setDimensionBundle,
    setIsGeneratingDimensions,
  }
})
