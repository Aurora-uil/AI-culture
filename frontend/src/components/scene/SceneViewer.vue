<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import SceneHotspot from './SceneHotspot.vue'
import AiContentBadge from '../global/AiContentBadge.vue'
import type { Hotspot, Scene } from '@/types'

/**
 * 场景查看器（设计系统 §22 / §23 / §82）
 *
 * 背景资源替换机制：
 *   1. 若 `public/assets/<chapter>/<name>.webp`（或 .jpg/.png）存在，使用真实图片；
 *   2. 否则回退到 #background 插槽里的 SVG 矢量场景。
 *   两者都保持同一套 0–1 归一化热点坐标，替换图片不需要改任何坐标代码。
 *
 * 只有 SVG / AI 示意回退显示「AI辅助历史场景示意」；历史原图显示可点击来源标签。
 */
const props = withDefaults(
  defineProps<{
    scene: Scene | null
    hotspotStatus?: Record<string, 'UNSEEN' | 'SEEN' | 'SELECTED'>
    /** 透镜开启时压暗背景（设计系统 §26：压暗 18%） */
    lensOpen?: boolean
    /** 非当前类别的热点弱化 */
    lensFilter?: (h: Hotspot) => boolean
    /** 章节 slug，用于定位资源目录 */
    chapterSlug?: string
    showBadge?: boolean
    aspect?: string
    imageFit?: 'cover' | 'contain'
    sourceLabel?: string
    sourceUrl?: string
  }>(),
  {
    hotspotStatus: () => ({}),
    lensOpen: false,
    showBadge: true,
    aspect: '16 / 9',
    imageFit: 'cover',
  },
)

const emit = defineEmits<{ (e: 'select', hotspot: Hotspot): void }>()

const imageFailed = ref(false)

/** 支持 .webp / .jpg / .png 三种扩展名 */
const candidateSrc = computed(() => {
  const asset = props.scene?.background_asset_id
  if (!asset) return null
  // 已经是完整路径
  if (asset.startsWith('/assets/')) return asset
  if (asset.startsWith('http')) return asset
  const slug = props.chapterSlug ?? props.scene?.chapter_id ?? ''
  return `/assets/${slug}/${asset}`
})

const showImage = computed(() => !!candidateSrc.value && !imageFailed.value)

const visibleHotspots = computed(() => {
  const list = props.scene?.hotspots ?? []
  if (!props.lensOpen || !props.lensFilter) return list
  return list.map((h) => ({ h, dim: !props.lensFilter!(h) }))
})

function onImageError() {
  imageFailed.value = true
}

watch(
  () => props.scene?.id,
  () => {
    imageFailed.value = false
  },
)
</script>

<template>
  <div class="scene" :style="{ aspectRatio: aspect }">
    <!-- 背景层：真图优先，缺失时回退 SVG -->
    <div class="scene__bg" :class="{ 'is-dimmed': lensOpen }">
      <img
        v-if="showImage"
        class="scene__img"
        :src="candidateSrc!"
        :alt="scene?.name || '历史场景'"
        :style="{ objectFit: imageFit }"
        :width="scene?.width || 1600"
        :height="scene?.height || 900"
        @error="onImageError"
      />
      <div v-else class="scene__svg">
        <!-- 各章专属 SVG 场景由父级注入 -->
        <slot name="background" />
      </div>
    </div>

    <!-- 热点层（未定位的热点由各章自定义渲染） -->
    <div v-if="scene?.hotspots?.length" class="scene__hotspots">
      <template v-for="item in visibleHotspots" :key="(item as any).h?.id ?? (item as any).id">
        <SceneHotspot
          :hotspot="(item as any).h ?? item"
          :status="hotspotStatus[(item as any).h?.id ?? (item as any).id] || 'UNSEEN'"
          :class="{ 'is-dimmed': (item as any).dim }"
          @select="emit('select', $event)"
        />
      </template>
    </div>

    <!-- 额外覆盖层：透镜标注、地图路线等 -->
    <slot name="overlay" />

    <AiContentBadge v-if="showBadge && !showImage" class="scene__badge" kind="scene" on-dark />

    <a
      v-if="showImage && sourceLabel && sourceUrl"
      class="scene__source"
      :href="sourceUrl"
      target="_blank"
      rel="noreferrer"
    >{{ sourceLabel }}</a>
    <span v-else-if="showImage && sourceLabel" class="scene__source">{{ sourceLabel }}</span>

    <p v-if="scene?.disclaimer" class="scene__disclaimer">{{ scene.disclaimer }}</p>
  </div>
</template>

<style scoped>
.scene {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: var(--radius-card);
  background: var(--color-paper-200);
  z-index: var(--z-scene);
}

.scene__bg {
  position: absolute;
  inset: 0;
  transition: filter var(--dur-scene) var(--ease-standard);
  animation: scene-camera-settle 1.65s cubic-bezier(.16,.78,.18,1) both;
}
/* 透镜开启：背景轻度压暗 18% */
.scene__bg.is-dimmed {
  filter: brightness(0.82) saturate(0.92);
}

.scene__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.scene__svg {
  width: 100%;
  height: 100%;
}
.scene__svg :deep(svg) {
  width: 100%;
  height: 100%;
  display: block;
}

.scene__hotspots {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.scene__hotspots > :deep(*) {
  pointer-events: auto;
}
.scene__hotspots :deep(.is-dimmed) {
  opacity: 0.25;
  transition: opacity var(--dur-normal) var(--ease-standard);
}

.scene__badge {
  position: absolute;
  right: var(--sp-3);
  bottom: var(--sp-3);
  z-index: var(--z-hud);
}

.scene__source {
  position: absolute;
  right: var(--sp-3);
  bottom: var(--sp-3);
  z-index: var(--z-hud);
  max-width: min(76%, 520px);
  padding: 4px 10px;
  border: 1px solid rgba(246, 241, 225, 0.48);
  border-radius: var(--radius-pill);
  background: rgba(27, 45, 46, 0.72);
  color: #f7f2e5;
  font-size: var(--fs-caption);
  line-height: 1.4;
  backdrop-filter: blur(8px);
}
.scene__source:hover {
  color: #fff;
  border-color: rgba(236, 203, 126, 0.8);
}

.scene__disclaimer {
  position: absolute;
  left: var(--sp-3);
  bottom: var(--sp-3);
  z-index: var(--z-hud);
  font-size: var(--fs-caption);
  color: var(--color-ink-700);
  background: rgba(250, 248, 242, 0.85);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  padding: 3px 10px;
  backdrop-filter: blur(6px);
}
@keyframes scene-camera-settle {
  from { opacity: .25; transform: scale(1.055); }
  to { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) { .scene__bg { animation: none; } }
</style>
