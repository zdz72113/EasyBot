import axios, { type AxiosResponse } from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

// ============ 配置 API ============

export const configApi = {
  get: () => api.get('/config'),
  update: (data: any) => api.post('/config', data),
  getModels: () => api.get('/config/models'),
  getTemplates: () => api.get('/config/templates'),
  getColorSchemes: () => api.get('/config/color-schemes'),
}

// ============ 内容生成 API ============

export const contentApi = {
  // 流式生成（返回 EventSource）
  generateStream: (query: string, model?: string) => {
    return new EventSource(`/api/content/generate`, {
      method: 'POST',
      body: JSON.stringify({ query, model }),
      headers: { 'Content-Type': 'application/json' },
    } as any)
  },
  
  // 同步生成
  generate: (query: string, model?: string) => 
    api.post('/content/generate-sync', { query, model }),
  
  // 重新生成
  regenerate: (recordId: string, instruction: string, model?: string) =>
    api.post('/content/regenerate', { record_id: recordId, instruction, model }),
  
  // 历史记录
  getHistory: () => api.get('/content/history'),
  getRecord: (id: string) => api.get(`/content/history/${id}`),
  updateRecord: (id: string, data: any) => api.put(`/content/history/${id}`, data),
  deleteRecord: (id: string) => api.delete(`/content/history/${id}`),
}

// ============ 素材抓取 API ============

export const fetcherApi = {
  fetch: (url: string, method: string = 'auto') => 
    api.post('/fetcher/fetch', { url, method }),
  checkUrl: (url: string) => 
    api.get('/fetcher/check-url', { params: { url } }),
}

// ============ 素材生成 API ============

export const materialApi = {
  generateFromContent: (
    content: any,
    options: { imageLimit?: number; videoLimit?: number; generateSimpleImage?: boolean } = {}
  ) =>
    api.post(
      '/materials/generate-from-content',
      {
        content,
        image_limit: options.imageLimit ?? 5,
        video_limit: options.videoLimit ?? 3,
        generate_simple_image: options.generateSimpleImage ?? true,
      },
      { timeout: 120000 }
    ),
}

// ============ 海报 API ============

export const posterApi = {
  generate: (content: any, config: any) => 
    api.post('/poster/generate', { content, config }),
  generateDownload: (content: any, config: any) => 
    api.post('/poster/generate-download', { content, config }, { responseType: 'blob' }),
}

// ============ 视频 API ============

export const videoApi = {
  getAudioList: () => api.get('/video/audio-list'),
  generate: (posterImage: string, config: any) => 
    api.post('/video/generate', { poster_image: posterImage, config }),
  download: (path: string) => `/api/video/download?path=${encodeURIComponent(path)}`,
  generateSubtitles: (audioFile: File) => {
    const formData = new FormData()
    formData.append('audio', audioFile)
    return api.post('/video/subtitles/generate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
}

export default api
