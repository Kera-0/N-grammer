<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({ modelReady: Boolean })

const API = '/api'

const text = ref('')
const taEl = ref(null)
const toField = ref('')
const subject = ref('')
const sent = ref(false)
const loading = ref(false)

const suggestions = ref([])
const ghost = ref(null) // { completion, words }
const activeIdx = ref(0)
let debounceTimer = null
let reqId = 0

const wordCount = computed(() => (text.value.trim() ? text.value.trim().split(/\s+/).length : 0))

async function fetchSuggestions() {
  const id = ++reqId
  loading.value = true
  try {
    const res = await fetch(`${API}/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text.value,
        n_words: 3,
        k: 3,
      }),
    })
    const data = await res.json()
    if (id !== reqId) return // устаревший ответ — игнорируем
    suggestions.value = data.suggestions || []
    activeIdx.value = 0
    ghost.value = suggestions.value[0] || null
  } catch {
    if (id === reqId) suggestions.value = []
  } finally {
    if (id === reqId) loading.value = false
  }
}

watch(text, () => {
  ghost.value = null
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchSuggestions, 90)
})

function applySuggestion(s) {
  if (!s) return
  text.value = text.value.replace(/\s+$/, '') + s.completion + ' '
  taEl.value?.focus()
}

function onKeydown(e) {
  if (!suggestions.value.length) return
  if (e.key === 'Tab' || e.key === 'ArrowRight') {
    e.preventDefault()
    applySuggestion(suggestions.value[activeIdx.value] || ghost.value)
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIdx.value = (activeIdx.value + 1) % suggestions.value.length
    ghost.value = suggestions.value[activeIdx.value]
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIdx.value = (activeIdx.value - 1 + suggestions.value.length) % suggestions.value.length
    ghost.value = suggestions.value[activeIdx.value]
  } else if (e.key === 'Escape') {
    ghost.value = null
  }
}

function send() {
  if (!text.value.trim()) return
  sent.value = true
  setTimeout(() => (sent.value = false), 2600)
  text.value = ''
  suggestions.value = []
  ghost.value = null
}

const placeholders = ref(['Dear team,'])
const phIdx = ref(0)
let phTimer = null
onMounted(() => {
  phTimer = setInterval(() => {
    phIdx.value = (phIdx.value + 1) % placeholders.value.length
  }, 3200)
  taEl.value?.focus()
})
onBeforeUnmount(() => clearInterval(phTimer))
</script>

<template>
  <section class="composer" :class="{ ready: modelReady }">
    <div class="fields">
      <div class="field">
        <label>Кому</label>
        <input v-model="toField" type="text" placeholder="colleague@company.com" spellcheck="false" />
      </div>
      <div class="field">
        <label>Тема</label>
        <input v-model="subject" type="text" placeholder="О чём письмо" spellcheck="false" />
      </div>
    </div>

    <div class="editor-wrap">
      <textarea
        ref="taEl"
        v-model="text"
        class="editor"
        :placeholder="placeholders[phIdx]"
        spellcheck="false"
        @keydown="onKeydown"
      ></textarea>

      <div v-if="ghost" class="ghost" aria-hidden="true">
        <span class="ghost-text">{{ text.replace(/\s+$/, '') }}</span>
        <span class="ghost-completion">{{ ghost.completion }}</span>
      </div>

      <transition name="pop">
        <div v-if="suggestions.length" class="chips">
          <button
            v-for="(s, i) in suggestions"
            :key="i"
            class="chip"
            :class="{ active: i === activeIdx, next: s.type === 'next' }"
            :title="`Tab — применить · ${s.words.join(' ')}`"
            @click="applySuggestion(s)"
            @mouseenter="activeIdx = i; ghost = s"
          >
            <span class="chip-idx">{{ i + 1 }}</span>
            <span class="chip-text">{{ s.words.join(' ') }}</span>
            <kbd>Tab</kbd>
          </button>
        </div>
      </transition>

      <div class="statusbar">
        <span class="dots" :class="{ on: loading }"><i></i><i></i><i></i></span>
        <span class="counter">{{ wordCount }} слов</span>
        <span class="hint">Tab — принять · ↑↓ — выбрать</span>
        <button class="send" :disabled="!wordCount" @click="send">Отправить ↗</button>
      </div>
    </div>

    <transition name="pop">
      <div v-if="sent" class="sent-toast">Письмо отправлено ✨</div>
    </transition>
  </section>
</template>

<style scoped>
.composer {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius);
  padding: 12px 16px;
  transition: border-color 0.2s;
}

.field:focus-within {
  border-color: var(--accent);
}

.field label {
  font-size: 13px;
  color: var(--text-dim);
  font-weight: 500;
  flex-shrink: 0;
}

.field input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 14px;
  font-family: inherit;
}

.editor-wrap {
  position: relative;
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.composer.ready .editor-wrap:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-soft);
}

.editor {
  width: 100%;
  min-height: 340px;
  resize: vertical;
  background: none;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 16px;
  line-height: 1.65;
  font-family: inherit;
  padding: 20px 20px 8px;
  caret-color: var(--accent-strong);
}

.ghost {
  position: absolute;
  inset: 20px 20px auto;
  pointer-events: none;
  font-size: 16px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.ghost-text {
  visibility: hidden;
}

.ghost-completion {
  color: var(--ghost);
}

.chips {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 12px 4px;
}

.chip {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  padding: 9px 14px;
  border-radius: 10px;
  background: var(--accent-soft);
  border: 1px solid transparent;
  color: var(--accent-strong);
  font-size: 14px;
  transition: background 0.15s, border-color 0.15s, transform 0.1s;
}

.chip.active {
  background: var(--accent);
  color: #fff;
  transform: translateX(2px);
}

.chip.next:not(.active) {
  background: rgba(79, 216, 140, 0.1);
  color: var(--success);
}

.chip.active kbd {
  border-color: rgba(255, 255, 255, 0.5);
  color: #fff;
}

.chip-idx {
  font-family: var(--mono);
  font-size: 11px;
  opacity: 0.6;
}

.chip-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

kbd {
  font-family: var(--mono);
  font-size: 10px;
  padding: 2px 6px;
  border: 1px solid var(--panel-border);
  border-radius: 5px;
  color: var(--text-dim);
}

.statusbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 16px 14px;
  font-size: 12px;
  color: var(--text-dim);
}

.counter {
  font-family: var(--mono);
}

.hint {
  margin-left: auto;
}

.dots {
  display: inline-flex;
  gap: 4px;
}

.dots i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--panel-border);
  transition: background 0.2s;
}

.dots.on i {
  background: var(--accent);
  animation: blink 0.9s infinite;
}

.dots.on i:nth-child(2) {
  animation-delay: 0.15s;
}

.dots.on i:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.send {
  padding: 8px 18px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--accent), #9d6cff);
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  transition: filter 0.15s, transform 0.1s;
}

.send:hover:not(:disabled) {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.send:disabled {
  opacity: 0.4;
  cursor: default;
}

.sent-toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--success);
  color: #0a1f14;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(79, 216, 140, 0.3);
}

.pop-enter-active,
.pop-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>
