import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '工作台' }
  },
  {
    path: '/content',
    name: 'Content',
    component: () => import('@/views/Content.vue'),
    meta: { title: '内容生成' }
  },
  {
    path: '/materials',
    name: 'Materials',
    component: () => import('@/views/Materials.vue'),
    meta: { title: '素材管理' }
  },
  {
    path: '/poster',
    name: 'Poster',
    component: () => import('@/views/Poster.vue'),
    meta: { title: '海报制作' }
  },
  {
    path: '/video',
    name: 'Video',
    component: () => import('@/views/Video.vue'),
    meta: { title: '视频创作' }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
