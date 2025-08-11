<template>
  <div class="daily-tasks-view">
    <div class="placeholder-content">
      <h2>Daily Tasks View</h2>
      <p>Coming next: Full daily tasks by family member</p>
      <div class="stats">
        <div class="stat">
          <span class="stat-number">{{ store.dailyTasks.length }}</span>
          <span class="stat-label">Total Tasks</span>
        </div>
        <div class="stat">
          <span class="stat-number">{{ store.familyMembers.length }}</span>
          <span class="stat-label">Family Members</span>
        </div>
        <div class="stat">
          <span class="stat-number">{{ store.focusItems.length }}</span>
          <span class="stat-label">Need Attention</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useHouseStore } from '../stores/house.js'
const store = useHouseStore()
</script>

<style scoped>
.daily-tasks-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.placeholder-content {
  text-align: center;
  max-width: 500px;
}

.placeholder-content h2 {
  font-family: var(--font-family-display);
  font-size: 2rem;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.placeholder-content p {
  font-size: 1.125rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 2rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  background: var(--bg-container);
  border-radius: 8px;
  border: 1px solid var(--border-light);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent-red);
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}
</style>