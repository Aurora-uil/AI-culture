import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

/**
 * 路由结构（设计系统 §70）
 *
 * URL 中 slug 同时用作 [data-chapter] 的章节色 key（设计系统 §6）：
 *   han / northern-wei / tang / yuan / qing / contemporary
 *
 * §71：页面状态通过 query 保留，刷新后能回到当前实体，比赛可直接打开演示位置。
 *   例：/chapter/yuan/scene?entity=script_tibetan&lens=scripts
 */

const chapterRoutes: RouteRecordRaw[] = [
  {
    path: '/chapter/:slug',
    name: 'chapter-guide',
    component: () => import('@/pages/chapter/C01Guide.vue'),
    meta: { chapterKey: 'dynamic' },
  },
  {
    path: '/chapter/:slug/intro',
    name: 'chapter-intro',
    component: () => import('@/pages/chapter/C00Intro.vue'),
    meta: { chapterKey: 'dynamic' },
  },
  {
    path: '/chapter/:slug/scene',
    name: 'chapter-scene',
    component: () => import('@/pages/chapter/C02Scene.vue'),
    meta: { chapterKey: 'dynamic' },
  },
  {
    path: '/chapter/:slug/chat',
    name: 'chapter-chat',
    component: () => import('@/pages/chapter/C05Chat.vue'),
    meta: { chapterKey: 'dynamic' },
  },
  {
    path: '/chapter/:slug/graph',
    name: 'chapter-graph',
    component: () => import('@/pages/chapter/C07Graph.vue'),
    meta: { chapterKey: 'dynamic' },
  },
  {
    path: '/chapter/:slug/summary',
    name: 'chapter-summary',
    component: () => import('@/pages/chapter/C08Summary.vue'),
    meta: { chapterKey: 'dynamic' },
  },
  {
    path: '/chapter/:slug/create',
    name: 'chapter-cocreation',
    component: () => import('@/pages/chapter/C09Cocreation.vue'),
    meta: { chapterKey: 'dynamic' },
  },
]

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'splash', component: () => import('@/pages/G00Splash.vue') },
  { path: '/timeline', name: 'timeline', component: () => import('@/pages/G01Timeline.vue') },
  ...chapterRoutes,
  { path: '/graph', name: 'graph', component: () => import('@/pages/G02TotalGraph.vue') },
  { path: '/journey', name: 'journey', component: () => import('@/pages/G03Journey.vue') },
  { path: '/about', name: 'about', component: () => import('@/pages/G04About.vue') },
  {
    // 文化项目文案，不写 Oops! / Something went wrong!（设计系统 §65）
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/pages/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, saved) {
    return saved ?? { top: 0 }
  },
})

/**
 * 章节色通过 slug 下发。路由 meta 里写 'dynamic' 的，
 * 在此解析为实际 slug，供 App.vue 设置 [data-chapter]。
 */
router.beforeEach((to) => {
  const slug = to.params.slug as string | undefined
  if (slug) {
    to.meta.chapterKey = slug
  }
  return true
})

export default router
