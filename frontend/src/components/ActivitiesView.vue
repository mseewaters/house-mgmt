<template>
  <div class="activities-layout">
    <!-- CENTER ZONE: Tasks (flex-grow to fill available space) -->
    <div class="center-zone">
      <!-- Overdue Section -->
      <div v-if="store.overdueTasks.length > 0" class="task-section overdue">
        <h3 class="section-header overdue">OVERDUE</h3>
        <div class="task-list">
          <div 
            v-for="task in store.overdueTasks" 
            :key="task.task_id"
            class="task-item overdue"
            @click="toggleTaskCompletion(task)"
          >
            <div class="task-checkbox overdue" :class="{ completed: task.status === 'Completed' }"></div>
            <div class="task-name">{{ task.task_name }}</div>
            <div class="person-initial" :class="getPersonClass(task.assigned_to)">
              {{ task.member_avatar }}
            </div>
            <div class="task-person-name">{{ task.member_name }}</div>
            <div class="task-meta">{{ task.overdue_message }}</div>
          </div>
        </div>
      </div>

      <!-- Current Period Section -->
      <div v-if="store.currentPeriodTasks.length > 0" class="task-section current">
        <h3 class="section-header">{{ store.currentPeriodName }}</h3>
        <div class="task-list">
          <div 
            v-for="task in store.currentPeriodTasks" 
            :key="task.task_id"
            class="task-item"
            @click="toggleTaskCompletion(task)"
          >
            <div class="task-checkbox" :class="{ completed: task.status === 'Completed' }"></div>
            <div class="task-name">{{ task.task_name }}</div>
            <div class="person-initial" :class="getPersonClass(task.assigned_to)">
              {{ task.member_avatar }}
            </div>
            <div class="task-person-name">{{ task.member_name }}</div>
            <div class="task-meta">{{ task.display_time }}</div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="store.overdueTasks.length === 0 && store.currentPeriodTasks.length === 0" class="empty-state">
        <div class="empty-state-icon">✨</div>
        <h3>All caught up!</h3>
        <p>No tasks due right now.</p>
      </div>
    </div>

    <!-- RIGHT ZONE: Completed + Coming Up -->
    <div class="right-zone">
      <!-- Completed Today Section -->
      <div class="completed-section">
        <div class="gradient-bar"></div>
        <h4 class="right-section-header">Completed Today</h4>
        <div class="completed-list">
          <div 
            v-for="task in store.completedTasks" 
            :key="task.task_id"
            class="completed-item"
          >
            <div class="person-initial" :class="getPersonClass(task.assigned_to)">
              {{ task.member_avatar }}
            </div>
            <div class="completed-content">
              <div class="completed-task">{{ task.task_name }}</div>
              <div class="completed-time">{{ task.completed_display_time }}</div>
            </div>
            <button 
              class="undo-btn" 
              @click="undoTaskCompletion(task)"
              title="Undo completion"
            >
              ↶
            </button>
          </div>
        </div>
        <div v-if="store.completedTasks.length === 0" class="empty-message">
          No tasks completed yet today
        </div>
      </div>

      <!-- Coming Up Section -->
      <div class="coming-up-section">
        <div class="gradient-bar"></div>
        <h4 class="right-section-header">Coming Up - {{ store.nextPeriodName }}</h4>
        <div class="coming-up-list">
          <div 
            v-for="task in store.upcomingTasks" 
            :key="task.task_id"
            class="coming-up-item"
          >
            <div class="person-initial" :class="getPersonClass(task.assigned_to)">
              {{ task.member_avatar }}
            </div>
            <div class="coming-up-task">{{ task.task_name }}</div>
            <div class="coming-up-time">{{ task.display_time }}</div>
          </div>
        </div>
        <div v-if="store.upcomingTasks.length === 0" class="empty-message">
          No {{ store.nextPeriodName.toLowerCase() }} tasks scheduled
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useHouseStore } from '../stores/house.js'

// Store
const store = useHouseStore()

// Helper functions
function getPersonClass(memberId) {
  const member = store.familyMembers.find(m => m.member_id === memberId)
  if (!member) return 'person-unknown'
  
  // Generate unique color class based on member's position in familyMembers array
  const colors = ['person-blue', 'person-green', 'person-purple', 'person-orange', 'person-pink']
  
  // Find the index of this member in the familyMembers array
  const memberIndex = store.familyMembers.findIndex(m => m.member_id === memberId)
  
  // Use the member's position to assign a unique color (cycling through if more members than colors)
  const colorIndex = memberIndex % colors.length
  return colors[colorIndex]
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
    // TODO: Show user-friendly error message
  }
}

async function undoTaskCompletion(completedTask) {
  try {
    console.log('🔄 Undoing task completion:', completedTask.task_name)
    await store.undoTaskCompletion(completedTask.task_id)
    console.log('✅ Task completion undone successfully')
  } catch (error) {
    console.error('❌ Failed to undo task completion:', error)
    // TODO: Show user-friendly error message
  }
}

// Load data on mount
onMounted(async () => {
  console.log('📱 ActivitiesView mounted')
  // Data is already loaded by HomePage, but refresh if needed
  if (store.dailyTasks.length === 0) {
    console.log('🔄 No tasks found, refreshing...')
    await store.loadDailyTasks()
  }
  console.log(`📋 Activities ready - ${store.dailyTasks.length} tasks loaded`)
})
</script>

<style scoped>
/* THREE ZONE LAYOUT */
.activities-layout {
  display: flex;
  height: 100%;
  gap: var(--spacing-lg);
  min-width: 0; /* Critical for flex shrinking */
}

/* CENTER ZONE: Tasks - Dynamic flex layout */
.center-zone {
  flex: 1;
  padding: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  min-width: var(--center-zone-min);
  max-width: calc(100vw - var(--sidebar-width) - var(--right-zone-width) - 60px);
  overflow: hidden;
}

/* RIGHT ZONE: Completed + Coming Up */
.right-zone {
  width: 400px;
  padding: var(--spacing-lg);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
  border-left: 1px solid var(--border-light);
  flex-shrink: 0; /* Prevent shrinking below min width */
}

/* TASK SECTIONS - Dynamic heights */
.task-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-bottom: var(--spacing-lg);
  overflow: hidden; /* Prevent section overflow */
}

.task-section.overdue {
  border-left: 4px solid var(--accent-red);
  padding-left: var(--spacing-md);
  flex: 0 1 auto; /* Don't grow much, but can shrink */
}

.task-section.current {
  border-left: 4px solid var(--border-light);
  padding-left: var(--spacing-md);
  flex: 1; /* Take remaining space */
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  flex: 1; /* Fill available section space */
  max-height: calc(50vh - 100px); /* Prevent excessive growth */
}

.section-header {
  background: linear-gradient(90deg, var(--accent-red), var(--accent-success), var(--text-muted));
  color: var(--text-white);
  padding: var(--spacing-sm) var(--spacing-md);
  font-weight: 700;
  font-size: var(--font-size-base);
  margin: 0 0 var(--spacing-sm) 0;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-radius: 6px;
}

.section-header.overdue {
  background: var(--accent-red);
}

.task-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-container);
  border-radius: 4px;
  min-height: var(--touch-target);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.task-item:hover {
  background: #f8f9fa;
}

.task-item:nth-child(even) {
  background: #fcfcfc;
}

.task-item:nth-child(even):hover {
  background: #f0f1f2;
}

.task-item.overdue {
  background: var(--task-bg-overdue, #fef2f2);
}

.task-item.overdue:hover {
  background: #fde8e8;
}

.task-checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border-light);
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.task-checkbox.completed {
  background: var(--accent-green, #10b981);
  border-color: var(--accent-green, #10b981);
}

.task-checkbox.completed::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 14px;
  font-weight: bold;
}

.task-checkbox.overdue {
  border-color: var(--accent-red, #ef4444);
}

.task-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: var(--font-size-base);
  flex: 1;
  min-width: 0;
}

.task-person-name {
  font-size: 14px;
  color: #6b7280;
  margin-left: 8px;
  white-space: nowrap;
}

.task-person {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.person-initial {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
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

.task-meta {
  font-size: 12px;
  color: #9ca3af;
  flex-shrink: 0;
  white-space: nowrap;
  margin-left: 12px;
}

/* EMPTY STATE */
.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-md);
}

/* RIGHT ZONE SECTIONS */
.gradient-bar {
  height: 4px;
  background: linear-gradient(90deg, #B85450, #95A985, #9CAAB6);
  border-radius: 2px;
  margin-bottom: 8px;
}

.right-section-header {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
  padding: 0 12px 4px 12px;
  border-bottom: 1px solid #e5e7eb;
}

.completed-section, .coming-up-section {
  flex: 1;
  min-height: 200px;
  padding: 0;
}

.completed-list, .coming-up-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.completed-item, .coming-up-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: transparent;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
  transition: all 0.15s ease;
  min-height: 32px;
}

.completed-item:last-child, .coming-up-item:last-child {
  border-bottom: none;
}

.completed-item:hover, .coming-up-item:hover {
  background: #f8f9fa;
}

.completed-content {
  flex: 1;
  min-width: 0;
}

.coming-up-task {
  flex: 1;
  min-width: 0;
  font-weight: 500;
  color: #374151;
  line-height: 1.2;
}

.completed-task {
  font-weight: 500;
  color: #374151;
  margin-bottom: 1px;
  line-height: 1.2;
}

.completed-time, .coming-up-time {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 400;
  line-height: 1.2;
}

.undo-btn {
  background: none;
  border: none;
  font-size: 14px;
  cursor: pointer;
  color: #9ca3af;
  padding: 2px 4px;
  border-radius: 3px;
  transition: all 0.15s ease;
  min-width: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.undo-btn:hover {
  background: #f3f4f6;
  color: #6b7280;
}

.empty-message {
  text-align: center;
  padding: 16px 12px;
  color: #9ca3af;
  font-style: italic;
  font-size: 12px;
  background: transparent;
  border: 1px dashed #d1d5db;
  border-radius: 4px;
  margin: 8px 12px;
}

/* Responsive adjustments */
@media screen and (min-width: 1200px) and (max-width: 1300px) {
  /* Likely Fire 10 HD dimensions */
  .right-zone {
    width: 350px; /* Smaller right zone for Fire tablets */
  }
  
  .center-zone {
    min-width: 350px; /* Reduce min width for center */
  }
  
  /* Adjust sidebar for Fire tablets */
  .sidebar {
    width: 250px;
  }
}

@media screen and (min-width: 1400px) {
  .container {
    max-width: 1400px;
    margin: 0 auto;
  }
  
  .right-zone {
    width: 420px;
  }
}

/* Tablet-Specific Touch Optimizations */
@media (pointer: coarse) {
  /* Larger touch targets for tablets */
  .task-item {
    min-height: 50px; /* Slightly larger than 44px minimum */
    padding: var(--spacing-md);
  }
  
  .nav-tab {
    min-height: 50px;
    padding: var(--spacing-lg) var(--spacing-xl);
  }
  
  .task-checkbox {
    width: 24px;
    height: 24px; /* Larger checkboxes for easier tapping */
  }
}

</style>