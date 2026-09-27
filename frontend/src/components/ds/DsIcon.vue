<script setup lang="ts">
/**
 * 线性图标（设计系统 §52）
 *
 * 只用一套线性图标，统一语义。不要混用卡通 / 写实 / 3D 图标。
 */
withDefaults(defineProps<{ name: IconName; size?: number }>(), { size: 18 })

export type IconName =
  | 'map'
  | 'person'
  | 'artifact'
  | 'text'
  | 'nodes'
  | 'document'
  | 'sparkle'
  | 'external-link'
  | 'compass'
  | 'close'
  | 'arrow-right'
  | 'arrow-left'
  | 'chevron-down'
  | 'chevron-right'
  | 'check'
  | 'info'
  | 'alert'
  | 'lock'
  | 'play'
  | 'search'
  | 'filter'
  | 'layers'
  | 'book'
  | 'copy'
  | 'refresh'
  | 'stop'
  | 'send'
  | 'minimize'
  | 'grid'
  | 'needle'
  | 'palette'
</script>

<template>
  <svg
    class="ds-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- 地图 -->
    <template v-if="name === 'map'">
      <path d="M9 3 3 5.5v15L9 18l6 3 6-2.5v-15L15 6 9 3Z" />
      <path d="M9 3v15M15 6v15" />
    </template>

    <!-- 人物 -->
    <template v-else-if="name === 'person'">
      <circle cx="12" cy="8" r="3.4" />
      <path d="M5 20c0-3.6 3.1-6 7-6s7 2.4 7 6" />
    </template>

    <!-- 文物 / 博物馆 -->
    <template v-else-if="name === 'artifact'">
      <path d="M3 9.5 12 4l9 5.5" />
      <path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8" />
      <path d="M3 20.5h18" />
    </template>

    <!-- 文字 -->
    <template v-else-if="name === 'text'">
      <path d="M5 6h14M5 12h9M5 18h11" />
    </template>

    <!-- 关系 -->
    <template v-else-if="name === 'nodes'">
      <circle cx="12" cy="5" r="2.2" />
      <circle cx="5" cy="18" r="2.2" />
      <circle cx="19" cy="18" r="2.2" />
      <path d="M12 7.2 6.6 15.9M12 7.2l5.4 8.7M7.2 18h9.6" />
    </template>

    <!-- 史料 -->
    <template v-else-if="name === 'document'">
      <path d="M14 3H7a1.6 1.6 0 0 0-1.6 1.6v14.8A1.6 1.6 0 0 0 7 21h10a1.6 1.6 0 0 0 1.6-1.6V7.6Z" />
      <path d="M14 3v4.6h4.6" />
      <path d="M9 12.5h6M9 16h4" />
    </template>

    <!-- AI -->
    <template v-else-if="name === 'sparkle'">
      <path d="M12 3.5 13.7 9l5.5 1.7-5.5 1.7L12 18l-1.7-5.6L4.8 10.7 10.3 9 12 3.5Z" />
      <path d="M18.5 16.5 19.3 19l2.5.8-2.5.8-.8 2.4" />
    </template>

    <template v-else-if="name === 'external-link'">
      <path d="M14 4h6v6" />
      <path d="M20 4 11 13" />
      <path d="M18 14.5V19a1.6 1.6 0 0 1-1.6 1.6H5.6A1.6 1.6 0 0 1 4 19V8.1a1.6 1.6 0 0 1 1.6-1.6H10" />
    </template>

    <template v-else-if="name === 'compass'">
      <circle cx="12" cy="12" r="9" />
      <path d="m15.5 8.5-2 5-5 2 2-5 5-2Z" />
    </template>

    <template v-else-if="name === 'close'">
      <path d="M6 6l12 12M18 6 6 18" />
    </template>

    <template v-else-if="name === 'arrow-right'">
      <path d="M4 12h15M13 6l6 6-6 6" />
    </template>

    <template v-else-if="name === 'arrow-left'">
      <path d="M20 12H5M11 6l-6 6 6 6" />
    </template>

    <template v-else-if="name === 'chevron-down'">
      <path d="m6 9 6 6 6-6" />
    </template>

    <template v-else-if="name === 'chevron-right'">
      <path d="m9 6 6 6-6 6" />
    </template>

    <template v-else-if="name === 'check'">
      <path d="m4.5 12.5 5 5 10-11" />
    </template>

    <template v-else-if="name === 'info'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 7.8v.4" />
    </template>

    <template v-else-if="name === 'alert'">
      <path d="M12 4 2.7 20h18.6L12 4Z" />
      <path d="M12 10v4M12 17.2v.3" />
    </template>

    <template v-else-if="name === 'lock'">
      <rect x="4.5" y="10.5" width="15" height="10" rx="1.6" />
      <path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" />
    </template>

    <template v-else-if="name === 'play'">
      <path d="M8 5.5 18 12 8 18.5v-13Z" />
    </template>

    <template v-else-if="name === 'search'">
      <circle cx="11" cy="11" r="6.5" />
      <path d="m20 20-3.7-3.7" />
    </template>

    <template v-else-if="name === 'filter'">
      <path d="M3.5 6h17M6.5 12h11M10 18h4" />
    </template>

    <template v-else-if="name === 'layers'">
      <path d="m12 3 8.5 4.6L12 12.2 3.5 7.6 12 3Z" />
      <path d="m3.5 12 8.5 4.6L20.5 12" />
      <path d="m3.5 16.4 8.5 4.6 8.5-4.6" />
    </template>

    <template v-else-if="name === 'book'">
      <path d="M4 5.2A1.7 1.7 0 0 1 5.7 3.5H11v16.8H5.7A1.7 1.7 0 0 1 4 18.6V5.2Z" />
      <path d="M20 5.2a1.7 1.7 0 0 0-1.7-1.7H13v16.8h5.3A1.7 1.7 0 0 0 20 18.6V5.2Z" />
    </template>

    <template v-else-if="name === 'copy'">
      <rect x="8.5" y="8.5" width="12" height="12" rx="1.8" />
      <path d="M15.5 5.5v-1a1.5 1.5 0 0 0-1.5-1.5H5a1.5 1.5 0 0 0-1.5 1.5V14A1.5 1.5 0 0 0 5 15.5h1" />
    </template>

    <template v-else-if="name === 'refresh'">
      <path d="M20 11.5A8 8 0 0 0 6.3 6.3L4 8.5" />
      <path d="M4 4v4.5h4.5" />
      <path d="M4 12.5a8 8 0 0 0 13.7 5.2L20 15.5" />
      <path d="M20 20v-4.5h-4.5" />
    </template>

    <template v-else-if="name === 'stop'">
      <rect x="6.5" y="6.5" width="11" height="11" rx="1.6" />
    </template>

    <template v-else-if="name === 'send'">
      <path d="M20.5 3.5 3.8 10.2l6.6 2.4 2.4 6.6 7.7-15.7Z" />
      <path d="m10.4 12.6 4.4-4.4" />
    </template>

    <template v-else-if="name === 'minimize'">
      <path d="M5 12h14" />
    </template>

    <template v-else-if="name === 'grid'">
      <rect x="4" y="4" width="7" height="7" rx="1.4" />
      <rect x="13" y="4" width="7" height="7" rx="1.4" />
      <rect x="4" y="13" width="7" height="7" rx="1.4" />
      <rect x="13" y="13" width="7" height="7" rx="1.4" />
    </template>

    <!-- 针法（当代章节） -->
    <template v-else-if="name === 'needle'">
      <path d="M18.5 3.5 9 13" />
      <path d="m6 10 4 4-3.5 4.5L2 22l3.5-4.5L10 14Z" />
      <circle cx="19.6" cy="4.4" r="1.4" />
    </template>

    <template v-else-if="name === 'palette'">
      <path d="M12 3a9 9 0 0 0 0 18c1.1 0 1.8-.8 1.8-1.7 0-.5-.2-.9-.5-1.2-.3-.3-.5-.7-.5-1.1 0-.9.8-1.7 1.7-1.7H16a5 5 0 0 0 5-5c0-4-4-7.3-9-7.3Z" />
      <circle cx="8" cy="11" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="12" cy="8" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="16" cy="10.5" r="1.1" fill="currentColor" stroke="none" />
    </template>
  </svg>
</template>

<style scoped>
.ds-icon {
  display: block;
  flex: none;
}
</style>
