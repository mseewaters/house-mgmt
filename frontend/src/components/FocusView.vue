<template>
  <div class="focus-view">
    <!-- Header -->
    <div class="focus-header">
      <h1 class="focus-title">Items in Focus</h1>
      <p class="focus-subtitle">Due now or overdue tasks that need attention</p>
    </div>
    
    <!-- Focus Items Grid -->
    <div class="focus-items" v-if="store.focusItems.length > 0">
      <div 
        v-for="item in store.focusItems" 
        :key="item.task_id"
        class="focus-item"
        :class="{ 'overdue': item.is_overdue }"
        @click="completeTask(item.task_id)"
      >
        <div class="focus-avatar">{{ item.member_avatar }}</div>
        <div class="focus-details">
          <div class="focus-task-name">{{ item.task_name }}</div>
          <div class="focus-member-name">{{ item.member_name }}</div>
          <div class="focus-due-time">
            {{ item.is_overdue ? 'OVERDUE' : 'Due now' }}
          </div>
        </div>
        <div class="focus-radio"></div>
      </div>
    </div>
    
    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="empty-state-icon">✅</div>
      <h3>All caught up!</h3>
      <p>No tasks need immediate attention right now.</p>
      <p class="empty-subtitle">{{ store.dailyTasks.length }} total tasks for today</p>
    </div>
  </div>
</template>

<script setup>
import { useHouseStore } from '../stores/house.js'

// Store
const store = useHouseStore()

// Methods
async function completeTask(taskId) {
  try {
    await store.completeTask(taskId)
    console.log('✅ Task completed from focus view')
  } catch (error) {
    console.error('❌ Failed to complete task:', error)
    // TODO: Show error toast
  }
}
</script>

<style scoped>
.focus-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 20px;
}

/* Header */
.focus-header {
  text-align: center;
  margin-bottom: 20px;
}

.focus-title {
  font-family: var(--font-family-display);
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.focus-subtitle {
  font-size: 1.125rem;
  color: var(--text-secondary);
}

/* Focus Items Grid */
.focus-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  flex: 1;
  align-content: start;
}

.focus-item {
  background: var(--bg-container);
  border-radius: 12px;
  border: 2px solid var(--accent-warning);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  transition: var(--transition-normal);
  cursor: pointer;
  min-height: 80px;
}

.focus-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.focus-item.overdue {
  border-color: var(--accent-red);
  background: var(--task-bg-overdue);
}

.focus-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--accent-red);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--text-white);
  font-weight: 700;
  flex-shrink: 0;
}

.focus-details {
  flex: 1;
}

.focus-task-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 5px;
}

.focus-member-name {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 5px;
}

.focus-due-time {
  font-size: 0.875rem;
  color: var(--accent-warning);
  font-weight: 600;
}

.focus-item.overdue .focus-due-time {
  color: var(--accent-red);
}

.focus-radio {
  width: 40px;
  height: 40px;
  border: 3px solid var(--accent-warning);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-normal);
  flex-shrink: 0;
}

.focus-item.overdue .focus-radio {
  border-color: var(--accent-red);
}

.focus-radio:hover {
  background: var(--accent-warning);
  transform: scale(1.1);
}

.focus-item.overdue .focus-radio:hover {
  background: var(--accent-red);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  text-align: center;
}

.empty-state-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.empty-state p {
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.empty-subtitle {
  color: var(--text-muted);
  font-size: 0.875rem;
}

/* Touch interactions */
.focus-item:active {
  transform: scale(0.98);
}
</style>