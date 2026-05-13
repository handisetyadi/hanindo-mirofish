<template>
  <router-view />
</template>

<script setup>
// 使用 Vue Router 来管理页面
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--mf-warm-ink);
  background-color: var(--mf-bg);
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--mf-beige);
}

::-webkit-scrollbar-thumb {
  background: var(--mf-blue);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--mf-blue-deep);
}

/* 全局按钮样式 */
button {
  font-family: inherit;
}
</style>
