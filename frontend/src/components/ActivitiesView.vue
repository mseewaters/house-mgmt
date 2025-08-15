<template>
  <div class="activities-layout">
    <!-- CENTER ZONE: Tasks (flex-grow to fill available space) -->
    <div class="center-zone">
      <!-- Overdue Section -->
      <div v-if="overdueTasks.length > 0" class="task-section overdue">
        <h3 class="section-header overdue">OVERDUE</h3>
        <div class="task-list">
          <div 
            v-for="task in overdueTasks" 
            :key="task.id"
            class="task-item overdue"
            @click="toggleTaskCompletion(task)"
          >
            <div class="task-checkbox overdue" :class="{ completed: task.completed }"></div>
            <div class="task-content">
              <div class="task-name">{{ task.name }}</div>
              <div class="task-person">
                <div class="person-initial" :class="getPersonClass(task.assignedTo)">
                  {{ getPersonInitial(task.assignedTo) }}
                </div>
                {{ getPersonName(task.assignedTo) }}
              </div>
            </div>
            <div class="task-meta">{{ formatOverdueTime(task.dueTime) }}</div>
          </div>
        </div>
      </div>

      <!-- Current Period Section -->
      <div v-if="currentPeriodTasks.length > 0" class="task-section current">
        <h3 class="section-header">{{ currentPeriodHeader }}</h3>
        <div class="task-list">
          <div 
            v-for="task in currentPeriodTasks" 
            :key="task.id"
            class="task-item"
            @click="toggleTaskCompletion(task)"
          >
            <div class="task-checkbox" :class="{ completed: task.completed }"></div>
            <div class="task-content">
              <div class="task-name">{{ task.name }}</div>
              <div class="task-person">
                <div class="person-initial" :class="getPersonClass(task.assignedTo)">
                  {{ getPersonInitial(task.assignedTo) }}
                </div>
                {{ getPersonName(task.assignedTo) }}
              </div>
            </div>
            <div class="task-meta">{{ formatTaskTime(task.dueTime) }}</div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="overdueTasks.length === 0 && currentPeriodTasks.length === 0" class="empty-state">
        <div class="empty-state-icon">✨</div>
        <h3>All caught up!</h3>
        <p>No tasks due right now.</p>
      </div>
    </div>

    <!-- RIGHT ZONE: Completed + Coming Up -->
    <div class="right-zone">
      <!-- Completed Today Section -->
      <div class="completed-section">
        <h4 class="right-section-header">Completed Today</h4>
        <div class="completed-list">
          <div 
            v-for="task in completedTasks" 
            :key="task.id"
            class="completed-item"
          >
            <div class="person-initial" :class="getPersonClass(task.assignedTo)">
              {{ getPersonInitial(task.assignedTo) }}
            </div>
            <div class="completed-content">
              <div class="completed-task">{{ task.name }}</div>
              <div class="completed-time">{{ formatCompletedTime(task.completedAt) }}</div>
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
        <div v-if="completedTasks.length === 0" class="empty-message">
          No tasks completed yet today
        </div>
      </div>

      <!-- Coming Up Section -->
      <div class="coming-up-section">
        <h4 class="right-section-header">Coming Up - {{ nextPeriodName }}</h4>
        <div class="coming-up-list">
          <div 
            v-for="task in upcomingTasks" 
            :key="task.id"
            class="coming-up-item"
          >
            <div class="person-initial" :class="getPersonClass(task.assignedTo)">
              {{ getPersonInitial(task.assignedTo) }}
            </div>
            <div class="coming-up-task">{{ task.name }}</div>
            <div class="coming-up-time">{{ formatUpcomingTime(task.dueTime) }}</div>
          </div>
        </div>
        <div v-if="upcomingTasks.length === 0" class="empty-message">
          No {{ nextPeriodName.toLowerCase() }} tasks scheduled
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useHouseStore } from '../stores/house.js'

// Store
const store = useHouseStore()

// Mock data for development - replace with actual API calls
const mockTasks = ref([
  {
    id: '1',
    name: 'Evening pills',
    assignedTo: 'bob',
    dueTime: '2024-08-12T21:00:00Z',
    completed: false,
    isOverdue: true
  },
  {
    id: '2', 
    name: 'Lunch vitamins',
    assignedTo: 'marjorie',
    dueTime: '2024-08-13T12:00:00Z',
    completed: false,
    isOverdue: true
  },
  {
    id: '3',
    name: 'Walk Layla',
    assignedTo: 'bob',
    dueTime: '2024-08-13T10:00:00Z',
    completed: false,
    isOverdue: false
  },
  {
    id: '4',
    name: 'Morning vitamins',
    assignedTo: 'marjorie',
    dueTime: '2024-08-13T09:00:00Z',
    completed: false,
    isOverdue: false
  },
  {
    id: '5',
    name: 'Feed Sadie',
    assignedTo: 'marjorie',
    dueTime: '2024-08-13T08:00:00Z',
    completed: false,
    isOverdue: false
  }
])

const mockCompletedTasks = ref([
  {
    id: 'c1',
    name: 'Morning pills',
    assignedTo: 'bob',
    completedAt: '2024-08-13T08:45:00Z'
  },
  {
    id: 'c2',
    name: 'Breakfast',
    assignedTo: 'lucy',
    completedAt: '2024-08-13T08:30:00Z'
  },
  {
    id: 'c3',
    name: 'Morning walk',
    assignedTo: 'layla',
    completedAt: '2024-08-13T07:45:00Z'
  }
])

const mockUpcomingTasks = ref([
  {
    id: 'u1',
    name: 'Afternoon vitamins',
    assignedTo: 'marjorie',
    dueTime: '2024-08-13T14:00:00Z'
  },
  {
    id: 'u2',
    name: 'Afternoon walk',
    assignedTo: 'layla',
    dueTime: '2024-08-13T15:00:00Z'
  },
  {
    id: 'u3',
    name: 'Treat time',
    assignedTo: 'lucy',
    dueTime: '2024-08-13T16:00:00Z'
  },
  {
    id: 'u4',
    name: 'Dinner prep',
    assignedTo: 'sadie',
    dueTime: '2024-08-13T17:00:00Z'
  }
])

// Family member data
const familyMembers = {
  bob: { name: 'Bob', type: 'person', initial: 'B' },
  marjorie: { name: 'Marjorie', type: 'person', initial: 'M' },
  layla: { name: 'Layla', type: 'pet', initial: 'La' },
  lucy: { name: 'Lucy', type: 'pet', initial: 'Lu' },
  sadie: { name: 'Sadie', type: 'pet', initial: 'S' }
}

// Computed properties for filtering tasks
const overdueTasks = computed(() => {
  return mockTasks.value.filter(task => task.isOverdue && !task.completed)
})

const currentPeriodTasks = computed(() => {
  return mockTasks.value.filter(task => !task.isOverdue && !task.completed)
})

const completedTasks = computed(() => {
  return mockCompletedTasks.value
})

const upcomingTasks = computed(() => {
  return mockUpcomingTasks.value
})

// Dynamic period headers based on current time
const currentPeriodHeader = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'MORNING (until 12pm)'
  if (hour < 18) return 'AFTERNOON (until 6pm)'
  return 'EVENING (until 10pm)'
})

const nextPeriodName = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Afternoon'
  if (hour < 18) return 'Evening'
  return 'Tomorrow Morning'
})

// Helper methods
function getPersonInitial(personKey) {
  return familyMembers[personKey]?.initial || '?'
}

function getPersonName(personKey) {
  return familyMembers[personKey]?.name || 'Unknown'
}

function getPersonClass(personKey) {
  const member = familyMembers[personKey]
  if (!member) return ''
  
  if (member.type === 'pet') {
    return `pet-${personKey}`
  }
  return ''
}

function formatOverdueTime(dueTime) {
  const date = new Date(dueTime)
  const now = new Date()
  const diffHours = Math.floor((now - date) / (1000 * 60 * 60))
  
  if (diffHours < 24) {
    return `${diffHours}h ago`
  } else {
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  }
}

function formatTaskTime(dueTime) {
  return new Date(dueTime).toLocaleTimeString([], { 
    hour: 'numeric', 
    minute: '2-digit' 
  })
}

function formatCompletedTime(completedAt) {
  return new Date(completedAt).toLocaleTimeString([], { 
    hour: 'numeric', 
    minute: '2-digit' 
  })
}

function formatUpcomingTime(dueTime) {
  return new Date(dueTime).toLocaleTimeString([], { 
    hour: 'numeric', 
    minute: '2-digit' 
  })
}

// Task interaction methods
function toggleTaskCompletion(task) {
  // Optimistic UI update
  task.completed = !task.completed
  
  if (task.completed) {
    // Move to completed list
    mockCompletedTasks.value.unshift({
      id: `c${Date.now()}`,
      name: task.name,
      assignedTo: task.assignedTo,
      completedAt: new Date().toISOString()
    })
    
    // Remove from main task list
    const index = mockTasks.value.findIndex(t => t.id === task.id)
    if (index > -1) {
      mockTasks.value.splice(index, 1)
    }
  }
  
  // TODO: Call actual API endpoint
  // await store.updateTaskCompletion(task.id, task.completed)
}

function undoTaskCompletion(completedTask) {
  // Remove from completed list
  const index = mockCompletedTasks.value.findIndex(t => t.id === completedTask.id)
  if (index > -1) {
    mockCompletedTasks.value.splice(index, 1)
  }
  
  // Add back to main task list
  mockTasks.value.push({
    id: completedTask.id.replace('c', ''),
    name: completedTask.name,
    assignedTo: completedTask.assignedTo,
    dueTime: new Date().toISOString(), // TODO: Use original due time
    completed: false,
    isOverdue: false // TODO: Calculate if actually overdue
  })
  
  // TODO: Call actual API endpoint
  // await store.undoTaskCompletion(completedTask.id)
}

// Load data on mount
onMounted(() => {
  // TODO: Load actual tasks from API
  // await store.loadDailyTasks()
})
</script>

<style scoped>
/* THREE ZONE LAYOUT */
.activities-layout {
  display: flex;
  height: 100%;
  gap: var(--spacing-lg);
}

/* CENTER ZONE: Tasks */
.center-zone {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  min-width: 400px;
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
}

/* TASK SECTIONS - Compact List Design */
.task-section {
  margin-bottom: var(--spacing-lg);
}

.task-section.overdue {
  border-left: 4px solid var(--accent-red);
  padding-left: var(--spacing-md);
}

.task-section.current {
  border-left: 4px solid var(--border-light);
  padding-left: var(--spacing-md);
}

.section-header {
  background: linear-gradient(90deg, #B85450, #95A985, #9CAAB6);
  color: var(--text-white);
  padding: var(--spacing-sm) var(--spacing-md);
  font-weight: 700;
  font-size: var(--font-size-base);
  margin: 0 0 var(--spacing-sm) 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-radius: 4px;
}

.section-header.overdue {
  background: var(--accent-red);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
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
  background: var(--task-bg-overdue);
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

.task-checkbox.overdue {
  border-color: var(--accent-red);
}

.task-checkbox.completed {
  background: var(--accent-success);
  border-color: var(--accent-success);
}

.task-checkbox.completed::after {
  content: '✓';
  color: white;
  font-size: 14px;
  font-weight: bold;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.task-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-name {
  font-weight: 500;
  color: var(--text-primary);
}

.task-person {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.person-initial {
  width: 20px;
  height: 20px;
  background: var(--accent-success);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: bold;
}

.task-meta {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

/* RIGHT ZONE STYLES */
.right-section-header {
  background: linear-gradient(90deg, #B85450, #95A985, #9CAAB6);
  color: var(--text-white);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-sm);
  font-weight: 700;
  margin: 0 0 var(--spacing-sm) 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-radius: 4px;
}

.completed-section {
  border-left: 4px solid var(--border-light);
  padding-left: var(--spacing-md);
}

.completed-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.completed-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-container);
  border-radius: 4px;
  font-size: var(--font-size-sm);
  opacity: 0.8;
  min-height: var(--touch-target);
  transition: background-color 0.15s ease;
}

.completed-item:hover {
  background: #f8f9fa;
}

.completed-item:nth-child(even) {
  background: #fcfcfc;
}

.completed-item:nth-child(even):hover {
  background: #f0f1f2;
}

.completed-content {
  flex: 1;
}

.completed-task {
  font-weight: 500;
  color: var(--text-primary);
}

.completed-time {
  font-size: 12px;
  color: var(--text-muted);
}

.undo-btn {
  background: none;
  border: 1px solid var(--border-light);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 12px;
  transition: all 0.2s ease;
}

.undo-btn:hover {
  background: var(--accent-red);
  color: white;
  border-color: var(--accent-red);
}

.coming-up-section {
  border-left: 4px solid var(--border-light);
  padding-left: var(--spacing-md);
}

.coming-up-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.coming-up-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-container);
  border-radius: 4px;
  font-size: var(--font-size-sm);
  min-height: var(--touch-target);
  transition: background-color 0.15s ease;
}

.coming-up-item:hover {
  background: #f8f9fa;
}

.coming-up-item:nth-child(even) {
  background: #fcfcfc;
}

.coming-up-item:nth-child(even):hover {
  background: #f0f1f2;
}

.coming-up-time {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  margin-left: auto;
  min-width: 40px;
  text-align: right;
}

.coming-up-task {
  flex: 1;
  color: var(--text-primary);
}

.empty-message {
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  padding: var(--spacing-lg);
  opacity: 0.7;
}

/* Pet-specific colors for two-letter codes */
.pet-layla .person-initial { background: #8B5CF6; }
.pet-lucy .person-initial { background: #06B6D4; }
.pet-sadie .person-initial { background: #F59E0B; }

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-secondary);
  text-align: center;
}

.empty-state-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.empty-state p {
  font-size: 1rem;
}

/* Touch interactions */
.task-item:active {
  transform: scale(0.98);
}

/* Responsive adjustments */
@media (max-width: 1024px) {
  .activities-layout {
    flex-direction: column;
  }
  
  .right-zone {
    width: 100%;
    max-height: 400px;
  }
}
</style>