<script setup>
import { ref, computed } from 'vue'
import Composer from './components/Composer.vue'

const stats = ref(null)

fetch('/api/health')
  .then((r) => r.json())
  .then(stats)
  .catch(() => {})

const subtitle = computed(() =>
  stats.value
    ? `${stats.value.vocab_size.toLocaleString('ru-RU')} слов · ${stats.value.n_contexts.toLocaleString('ru-RU')} биграммных контекстов`
    : 'загружаю статистику корпуса…'
)
</script>

<template>
  <div class="shell">
    <header class="header">
      <div class="logo">
        <span class="logo-mark">N</span>
        <div>
          <h1>N-grammer</h1>
          <p class="subtitle">{{ subtitle }}</p>
        </div>
      </div>
      <span class="badge">n-gram · HW1 · ФКН ВШЭ</span>
    </header>

    <main class="main">
      <Composer :model-ready="!!stats" />
    </main>
  </div>
</template>

<style scoped>
.shell {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 24px 48px;
  display: flex;
  flex-direction: column;
  gap: 28px;
  min-height: 100%;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-mark {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--accent), #9d6cff);
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 24px;
  color: #fff;
  box-shadow: 0 6px 24px rgba(108, 140, 255, 0.35);
}

h1 {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 13px;
  color: var(--text-dim);
  margin-top: 2px;
}

.badge {
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text-dim);
  border: 1px solid var(--panel-border);
  padding: 6px 12px;
  border-radius: 999px;
}
</style>
