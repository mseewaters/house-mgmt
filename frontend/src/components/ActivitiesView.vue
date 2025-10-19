<template>
  <div class="activities-person-layout">
    <!-- Left Column: People (2 cards, 50% height each) -->
    <div class="people-column">
      <div 
        v-for="person in store.tasksByPersonGrouped.people" 
        :key="person.member_id"
        class="person-card"
      >
        <div class="gradient-bar"></div>
        <div class="card-header">
          <div class="member-info">
            <div class="member-avatar" :class="getPersonClass(person.member_id)">
              {{ person.avatar }}
            </div>
            <div class="member-name">{{ person.name }}</div>
          </div>
          <div class="progress-count">[{{ person.progress.completed }}/{{ person.progress.total }}]</div>
        </div>
        
        <div class="task-list">
          <div 
            v-for="task in person.tasks" 
            :key="task.task_id"
            class="task-item"
            :class="{ 
              'overdue': task.is_overdue && !task.is_completed, 
              'completed': task.is_completed 
            }"
            @click="toggleTaskCompletion(task)"
          >
            <div class="task-radio" :class="{ checked: task.is_completed }"></div>
            <div class="task-content">
              <div class="task-name">{{ task.task_name }}</div>
            </div>
            <div class="task-status">
              <span v-if="task.is_completed">Completed</span>
              <span v-else-if="task.is_overdue">Overdue</span>
              <span v-else>{{ task.display_time }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="person.tasks.length === 0" class="empty-card">
          No tasks today
        </div>
      </div>
    </div>

    <!-- Right Column: Pets (3 cards, 33% height each) -->
    <div class="pets-column">
      <div 
        v-for="pet in store.tasksByPersonGrouped.pets" 
        :key="pet.member_id"
        class="pet-card"
      >
        <div class="gradient-bar"></div>
        <div class="card-header">
          <div class="member-info">
            <div class="member-avatar" :class="getPersonClass(pet.member_id)">
              {{ pet.avatar }}
            </div>
            <div class="member-name">{{ pet.name }}</div>
          </div>
          <div class="progress-count">[{{ pet.progress.completed }}/{{ pet.progress.total }}]</div>
        </div>
        
        <div class="task-list">
          <div 
            v-for="task in pet.tasks" 
            :key="task.task_id"
            class="task-item"
            :class="{ 
              'overdue': task.is_overdue && !task.is_completed, 
              'completed': task.is_completed 
            }"
            @click="toggleTaskCompletion(task)"
          >
            <div class="task-radio" :class="{ checked: task.is_completed }"></div>
            <div class="task-content">
              <div class="task-name">{{ task.task_name }}</div>
            </div>
            <div class="task-status">
              <span v-if="task.is_completed">Completed</span>
              <span v-else-if="task.is_overdue">Overdue</span>
              <span v-else>{{ task.display_time }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="pet.tasks.length === 0" class="empty-card">
          No tasks today
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useHouseStore } from '../stores/house.js'

const store = useHouseStore()

// Helper: Get person color class
function getPersonClass(memberId) {
  const member = store.familyMembers.find(m => m.member_id === memberId)
  if (!member) return 'person-unknown'
  
  const colors = ['person-blue', 'person-green', 'person-purple', 'person-orange', 'person-pink']
  const index = store.familyMembers.indexOf(member)
  return colors[index % colors.length]
}

// Task actions
async function toggleTaskCompletion(task) {
  try {
    if (task.status === 'Completed') {
      console.log('⚠️ Task already completed:', task.task_name)
      return
    }
    
    console.log('🔄 Completing task:', task.task_name)
    await store.completeTask(task.task_id)
    console.log('✅ Task completed successfully')
  } catch (error) {
    console.error('❌ Failed to complete task:', error)
  }
}

// Load data on mount
onMounted(async () => {
  console.log('📱 ActivitiesView (Person-Oriented) mounted')
  if (store.dailyTasks.length === 0) {
    console.log('🔄 No tasks found, refreshing...')
    await store.loadDailyTasks()
  }
  console.log(`📋 Activities ready - ${store.dailyTasks.length} tasks loaded`)
})
</script>

<style scoped>
/* TWO COLUMN LAYOUT */
.activities-person-layout {
  display: grid;
  grid-template-columns: 50% 50%;
  gap: 16px;
  height: 100%;
  padding: 8px;
  overflow: hidden;
}

/* PEOPLE COLUMN (Left) */
.people-column {
  display: grid;
  grid-template-rows: 50% 50%;
  gap: 16px;
  overflow: hidden;
}

.person-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* PETS COLUMN (Right) */
.pets-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.pet-card {
  flex: 1;
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* CARD HEADER */
.gradient-bar {
  height: 6px;
  background: linear-gradient(90deg, #B85450, #95A985, #9CAAB6);
  border-radius: 2px 2px 0 0;
  margin: -16px -16px 12px -16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  flex-shrink: 0;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.member-avatar {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: bold;
  color: white;
  flex-shrink: 0;
}

.person-blue { background: var(--accent-red); }
.person-green { background: var(--bg-tab-nav); }
.person-purple { background: var(--accent-blue); }
.person-orange { background: var(--bg-tab-active); }
.person-pink { background: var(--accent-success); }
.person-unknown { background: #6b7280; }

.member-name {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.progress-count {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-secondary);
}

/* TASK LIST */
.task-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-height: 0;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  min-height: 40px;
}

.task-item:hover {
  background: #f9fafb;
}

/* TASK STATES */
.task-item.overdue {
  background: var(--task-bg-overdue);
}

.task-item.completed {
  background: var(--task-bg-completed);
}

/* RADIO BUTTON */
.task-radio {
  width: 24px;
  height: 24px;
  border: 2px solid #d1d5db;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.task-item.overdue .task-radio {
  border-color: var(--accent-red);
}

.task-radio.checked {
  background: var(--accent-success);
  border-color: var(--accent-success);
}

.task-radio.checked::after {
  content: '✓';
  color: white;
  font-size: 18px;
  font-weight: bold;
}

/* TASK CONTENT */
.task-content {
  flex: 1;
  min-width: 0;
}

.task-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.task-status {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
  flex-shrink: 0;
  white-space: nowrap;
}

.task-item.overdue .task-status {
  color: var(--accent-red);
  font-weight: 600;
}

.task-item.completed .task-status {
  color: var(--accent-success);
}

/* EMPTY STATE */
.empty-card {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-style: italic;
  font-size: 16px;
}
</style>