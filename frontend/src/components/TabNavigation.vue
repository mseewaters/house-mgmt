<template>
  <div class="tab-nav">
    <button 
      v-for="tab in tabs" 
      :key="tab.key"
      class="tab-button"
      :class="{ active: store.activeTab === tab.key }"
      @click="setActiveTab(tab.key)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup>
import { useHouseStore } from '../stores/house.js'

// Store
const store = useHouseStore()

// Tab configuration
const tabs = [
  { key: 'focus', label: 'Focus' },
  { key: 'daily', label: 'Daily Tasks' },
  { key: 'meals', label: 'Meals' },
  { key: 'admin', label: 'Add tasks' }
]

// Methods
function setActiveTab(tabKey) {
  store.setActiveTab(tabKey)
}
</script>

<style scoped>
.tab-nav {
  display: flex;
  background: var(--bg-tab-nav);
  flex-shrink: 0;
}

.tab-button {
  flex: 1;
  padding: 10px 16px;
  border: none;
  background: none;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-white-light);
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: var(--transition-normal);
  min-height: var(--touch-target);
}

.tab-button.active {
  color: var(--text-white);
  background: var(--bg-tab-active);
  border-bottom-color: var(--accent-red);
}

.tab-button:hover:not(.active) {
  background: rgba(255,255,255,0.1);
  color: var(--text-white);
}

.tab-button:active {
  transform: scale(0.98);
}
</style>