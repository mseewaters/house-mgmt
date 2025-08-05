# Technical Design: house-mgmt

## System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Lambda        │
│   (Vue.js)      │◄──►│   (AWS)         │◄──►│   (FastAPI)     │
│                 │    │                 │    │                 │
│ • Vue Router    │    │ • CORS          │    │ • Business Logic│
│ • Pinia Store   │    │ • IP Filtering  │    │ • Data Access   │
│ • Touch UI      │    │ • Rate Limiting │    │ • Weather API   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   CloudFront    │    │   DynamoDB      │
                       │   (Amplify CDN) │    │   (Database)    │
                       │                 │    │                 │
                       │ • Static Assets │    │ • Family Data   │
                       │ • Global Cache  │    │ • Task Data     │
                       └─────────────────┘    │ • Completions   │
                                              └─────────────────┘
                      
┌─────────────────┐    ┌─────────────────┐
│   GitHub        │    │   External APIs │  
│   Actions       │    │                 │
│                 │    │ • Weather API   │
│ • Backend CI/CD │    │ • Time/Date API │
│ • SAM Deploy    │    │                 │
└─────────────────┘    └─────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Main API Lambda │    │ Weather Lambda  │
│                 │────▶│                  │    │ (Cron Job)      │
│ GET /api/weather│    │ Reads from S3    │    │ Updates S3      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                         ┌─────────────────┐    ┌─────────────────┐
                         │   S3 Bucket     │    │ OpenWeather API │
                         │ (Weather Cache) │    │                 │
                         └─────────────────┘    └─────────────────┘
                         
```

### Technology Stack
- **Frontend**: Vue.js 3 with Composition API, Pinia state management
- **Deployment**: AWS Amplify (hosting + CI/CD for frontend)
- **API**: AWS API Gateway + Lambda (Python FastAPI)
- **Database**: DynamoDB with single-table design
- **CDN**: CloudFront (managed by Amplify)
- **IaC**: AWS SAM for backend infrastructure
- **CI/CD**: GitHub Actions for backend deployment
- **Security**: IP address allowlisting (kitchen tablet only)

### Key Design Decisions
- **No Authentication**: Application secured by network-level IP restrictions
- **Touch-First UI**: Optimized for tablet interface (44px touch targets)
- **Offline Resilience**: Local state with background sync and retry logic
- **Real-time Updates**: Optimistic UI updates with server reconciliation
## Data Models & Database Design

### DynamoDB Table Structure

**Primary Table: `house-mgmt_main`**
```python
# Partition Key: PK, Sort Key: SK
# GSI1: GSI1PK, GSI1SK (for alternate access patterns)

# Family Member Entity
{
    'PK': 'FAMILY',
    'SK': 'MEMBER#uuid-1234',
    'GSI1PK': 'MEMBER#uuid-1234',
    'GSI1SK': 'FAMILY',
    'entity_type': 'family_member',
    'name': 'Bob',  # max 15 characters
    'type': 'Person',  # Person, Pet
    'pet_type': null,  # dog, cat, other (only if type=Pet)
    'status': 'Active',  # Active, Inactive
    'created_at': '2024-08-02T09:39:00Z',
    'updated_at': '2024-08-02T09:39:00Z'
}

# Recurring Task Template Entity
{
    'PK': 'RECURRING',
    'SK': 'TASK#uuid-5678',
    'GSI1PK': 'MEMBER#uuid-1234',  # assigned family member
    'GSI1SK': 'RECURRING#uuid-5678',
    'entity_type': 'recurring_task',
    'task_name': 'Morning pills',  # max 30 characters
    'assigned_to': 'uuid-1234',  # family member UUID
    'frequency': 'Daily',  # Daily, Weekly, Monthly
    'due': 'Morning',  # Morning/Evening (Daily), Mon-Sun (Weekly), 1-31 (Monthly)
    'overdue_when': '1 hour',  # Immediate, 1 hour, 6 hours, 1 day
    'category': 'Medication',  # Medication, Feeding, Other
    'status': 'Active',  # Active, Inactive
    'created_at': '2024-08-02T09:30:00Z',
    'updated_at': '2024-08-02T09:30:00Z'
}

# Daily Task Instance Entity (Generated from Recurring Tasks)
{
    'PK': 'DAILY#2024-08-02',
    'SK': 'TASK#uuid-9999',
    'GSI1PK': 'MEMBER#uuid-1234',  # assigned family member
    'GSI1SK': 'DAILY#2024-08-02',
    'entity_type': 'daily_task',
    'task_name': 'Morning pills',
    'assigned_to': 'uuid-1234',  # family member UUID
    'recurring_task_id': 'uuid-5678',  # source recurring task template
    'date': '2024-08-02',  # local date (YYYY-MM-DD)
    'due_time': 'Morning',  # Morning, Evening, or specific time (local)
    'due_timestamp': '2024-08-02T13:00:00Z',  # UTC timestamp for due time
    'status': 'Pending',  # Pending, Completed, Overdue, Cleared, Skipped
    'category': 'Medication',
    'completed_at': null,  # UTC timestamp when marked complete, null if pending
    'generated_at': '2024-08-02T05:00:00Z',  # UTC timestamp when generated (local midnight)
    'overdue_at': '2024-08-02T14:00:00Z',  # UTC timestamp when becomes overdue
    'clear_at': '2024-08-03T05:00:00Z',  # UTC timestamp when cleared (frequency-dependent)
    'frequency': 'Daily',  # copied from recurring task (Daily, Weekly, Monthly)
    'overdue_behavior': '1 hour'  # copied from recurring task for reference
}

# Task Completion Entity
{
    'PK': 'COMPLETION',
    'SK': 'TASK#uuid-9999#2024-08-02T10:15:00Z',
    'GSI1PK': 'MEMBER#uuid-1234',
    'GSI1SK': 'COMPLETION#2024-08-02',
    'entity_type': 'task_completion',
    'task_id': 'uuid-9999',  # daily task UUID
    'recurring_task_id': 'uuid-5678',  # source recurring task
    'family_member_id': 'uuid-1234',
    'completed_at': '2024-08-02T10:15:00Z',
    'date': '2024-08-02',
    'task_name': 'Morning pills',
    'category': 'Medication'
}

```

### Access Patterns & Queries
```python
# 1. Get all family members
PK = "FAMILY", SK begins_with "MEMBER#"

# 2. Get specific family member
PK = "FAMILY", SK = "MEMBER#uuid-1234"

# 3. Get all recurring tasks
PK = "RECURRING", SK begins_with "TASK#"

# 4. Get recurring tasks for a family member
GSI1PK = "MEMBER#uuid-1234", SK begins_with "RECURRING#"

# 5. Get all daily tasks for a specific date
PK = "DAILY#2024-08-02", SK begins_with "TASK#"

# 6. Get daily tasks for a family member on a date
GSI1PK = "MEMBER#uuid-1234", GSI1SK = "DAILY#2024-08-02"

# 7. Get all completions for a date
PK = "COMPLETION", SK begins_with "TASK#", filter on date

# 8. Get family member's completion history
GSI1PK = "MEMBER#uuid-1234", SK begins_with "COMPLETION#"

# 9. Get active family members (scan with filter)
PK = "FAMILY", SK begins_with "MEMBER#", filter: status = "Active"

# 10. Get active recurring tasks (scan with filter)  
PK = "RECURRING", SK begins_with "TASK#", filter: status = "Active"
```

### Weather Data Storage
```python
# Weather data stored in S3, not DynamoDB
# S3 Bucket: house-mgmt-weather-data
# Key: current-weather.json
# Updated hourly via Lambda + OpenWeather API
# Structure:
{
    "current": {
        "temperature": 77,
        "humidity": 56,
        "wind_speed": 7
    },
    "today": {
        "high": 77,
        "low": 60,
        "condition": "Few Clouds",
        "icon": "02d"
    },
    "forecast": [
        {"day": "Sunday", "high": 82, "low": 60, "icon": "01d"},
        {"day": "Monday", "high": 86, "low": 61, "icon": "02d"},
        {"day": "Tuesday", "high": 84, "low": 64, "icon": "02d"},
        {"day": "Wednesday", "high": 85, "low": 65, "icon": "02d"},
        {"day": "Thursday", "high": 82, "low": 66, "icon": "11d"}
    ],
    "updated_at": "2024-08-02T09:39:00Z"  # UTC timestamp
}
```

### Data Generation & Task Management
```python
# Daily Task Generation Process (runs at local midnight via EventBridge)
def generate_daily_tasks():
    """
    1. Query all active recurring tasks
    2. For each recurring task, check if it should generate for tomorrow
    3. Generate daily instance with proper UTC timestamps
    4. Handle frequency logic (Daily=every day, Weekly=specific day, Monthly=specific date)
    """
    
    # Daily Tasks: Generate every day
    # Weekly Tasks: Generate only on specified day (e.g., Sunday)  
    # Monthly Tasks: Generate only on specified date (e.g., 15th)

# Task Status Management Process (runs hourly)
def update_task_statuses():
    """
    1. Query pending daily tasks where overdue_at < now()
    2. Update status from 'Pending' to 'Overdue'
    3. Query overdue tasks where clear_at < now()
    4. Update status from 'Overdue' to 'Cleared' (frequency-based thresholds)
    """

def calculate_clear_timestamp(due_timestamp, frequency, local_date):
    """
    Calculate when overdue task should be cleared based on frequency:
    - Daily: Next local midnight after due date
    - Weekly: 7 days after overdue_at 
    - Monthly: 30 days after overdue_at
    """
    if frequency == 'Daily':
        # Clear at next local midnight (start of next day)
        next_day = datetime.strptime(local_date, '%Y-%m-%d') + timedelta(days=1)
        return next_day.replace(hour=5, minute=0, second=0)  # 5 AM UTC = midnight EST
    elif frequency == 'Weekly':
        return due_timestamp + timedelta(days=7)
    elif frequency == 'Monthly':
        return due_timestamp + timedelta(days=30)

# Task Clearing Rules (frequency-based thresholds):
# - Daily tasks: Clear at next local midnight (didn't do it today → gone tomorrow)
# - Weekly tasks: Clear after 7 days overdue  
# - Monthly tasks: Clear after 30 days overdue
# - Cleared tasks don't appear in daily UI but remain for audit
# - Manual "Skip" action → status = 'Skipped' (doesn't count toward progress)
# - Can "Unsnooze" cleared tasks back to 'Overdue' if needed

# Time Zone Conversion:
# Kitchen timezone: America/New_York (EST/EDT) - hardcoded
# Storage: All timestamps in UTC
# Display: Frontend converts UTC → local for user interface
# Generation: Local midnight (00:00 EST/EDT) triggers task generation

# Weekly/Monthly Examples:
# Weekly: "Bath Layla every Sunday" → generates only on Sundays
# Monthly: "Vet checkup on 15th" → generates only on 15th of each month
```

## API Design & Endpoints

### Security Model
```python
# No authentication required - secured by IP allowlisting at API Gateway level
# All endpoints are public within trusted network
# Rate limiting applied per IP address
# CORS configured for Amplify frontend domain only
```

### Core API Endpoints
```python
# Family Members
GET    /api/family                        # Get all family members
POST   /api/family                        # Create family member
GET    /api/family/{member_id}            # Get family member details
PUT    /api/family/{member_id}            # Update family member
DELETE /api/family/{member_id}            # Delete family member

# Recurring Task Templates
GET    /api/recurring-tasks               # Get all recurring tasks
POST   /api/recurring-tasks               # Create recurring task
GET    /api/recurring-tasks/{task_id}     # Get recurring task details  
PUT    /api/recurring-tasks/{task_id}     # Update recurring task
DELETE /api/recurring-tasks/{task_id}     # Delete recurring task
GET    /api/recurring-tasks/member/{member_id}  # Get tasks for family member

# Daily Task Instances
GET    /api/daily-tasks                   # Get today's tasks (default)
GET    /api/daily-tasks?date=2024-08-02   # Get tasks for specific date
GET    /api/daily-tasks/member/{member_id} # Get today's tasks for family member
PUT    /api/daily-tasks/{task_id}/complete # Mark task as completed
PUT    /api/daily-tasks/{task_id}/skip    # Mark task as skipped
PUT    /api/daily-tasks/{task_id}/unsnooze # Reactivate cleared task

# Task Completions & History
GET    /api/completions                   # Get recent completions
GET    /api/completions/member/{member_id} # Get completion history for member
GET    /api/completions?date=2024-08-02   # Get completions for specific date

# Weather Data
GET    /api/weather                       # Get current weather and forecast

# System Health
GET    /api/health                        # Health check endpoint
GET    /api/stats                         # Dashboard statistics
```

### API Request/Response Examples

#### Daily Tasks Dashboard (Primary UI)
```python
# GET /api/daily-tasks
# Returns all tasks for today with family member details
Response: {
    "date": "2024-08-02",
    "tasks_by_member": {
        "Bob": {
            "member_id": "uuid-1234",
            "name": "Bob",
            "type": "Person", 
            "tasks": [
                {
                    "id": "uuid-9999",
                    "task_name": "Morning pills",
                    "category": "Medication",
                    "due_time": "Morning",
                    "status": "Completed",
                    "completed_at": "2024-08-02T10:15:00Z"
                },
                {
                    "id": "uuid-8888", 
                    "task_name": "Evening pills",
                    "category": "Medication",
                    "due_time": "Evening",
                    "status": "Pending", 
                    "completed_at": null
                }
            ],
            "progress": {"completed": 1, "total": 2}
        }
    }
}
```

#### Complete Task (Touch Interaction)
```python
# PUT /api/daily-tasks/{task_id}/complete
Request: {}  # No body needed
Response: {
    "success": true,
    "task": {
        "id": "uuid-9999",
        "status": "Completed", 
        "completed_at": "2024-08-02T10:15:00Z"
    },
    "member_progress": {"completed": 2, "total": 2}
}
```

#### Create Family Member
```python
# POST /api/family
Request: {
    "name": "Sadie",
    "type": "Pet",
    "pet_type": "cat",
    "status": "Active"
}
Response: {
    "id": "uuid-5555",
    "name": "Sadie", 
    "type": "Pet",
    "pet_type": "cat",
    "status": "Active",
    "created_at": "2024-08-02T09:39:00Z"
}
```

#### Create Recurring Task  
```python
# POST /api/recurring-tasks
Request: {
    "task_name": "Feed Sadie",
    "assigned_to": "uuid-5555",
    "frequency": "Daily",
    "due": "Evening", 
    "overdue_when": "6 hours",
    "category": "Feeding",
    "status": "Active"
}
Response: {
    "id": "uuid-7777",
    "task_name": "Feed Sadie",
    "assigned_to": "uuid-5555",
    "frequency": "Daily",
    "due": "Evening",
    "overdue_when": "6 hours", 
    "category": "Feeding",
    "status": "Active",
    "created_at": "2024-08-02T09:30:00Z"
}
```

#### Weather Data
```python
# GET /api/weather
Response: {
    "current": {
        "temperature": 77,
        "humidity": 56,
        "wind_speed": 7
    },
    "today": {
        "high": 77,
        "low": 60, 
        "condition": "Few Clouds",
        "icon": "02d"
    },
    "forecast": [
        {"day": "Sunday", "high": 82, "low": 60, "icon": "01d"},
        {"day": "Monday", "high": 86, "low": 61, "icon": "02d"}
    ],
    "updated_at": "2024-08-02T09:39:00Z"
}
```

### Error Handling
```python
# Standard error response format
{
    "error": true,
    "message": "Family member not found",
    "code": "MEMBER_NOT_FOUND",
    "details": {
        "member_id": "invalid-uuid"
    }
}

# HTTP status codes:
# 200 - Success
# 400 - Bad Request (validation errors)
# 404 - Not Found  
# 429 - Rate Limited
# 500 - Internal Server Error
```

## Frontend Architecture

### Vue.js Structure
```
src/
├── components/           # Reusable UI components
│   ├── common/          # Generic components (Button, Modal, LoadingSpinner)
│   ├── family/          # Family member components (MemberCard, MemberForm)
│   ├── tasks/           # Task components (TaskItem, TaskList, ProgressDial)
│   ├── weather/         # Weather components (WeatherWidget, Forecast)
│   └── admin/           # Admin components (DataTable, ConfirmDialog)
├── views/               # Page-level components (tablet screens)
│   ├── DailyTracking.vue    # Main dashboard (Activities tab)
│   ├── AdminPanel.vue       # Family & recurring task management
│   └── MealsView.vue        # Future meals functionality
├── stores/              # Pinia state management
│   ├── dailyTasks.ts    # Daily task instances & completion state
│   ├── family.ts        # Family member management
│   ├── recurringTasks.ts # Recurring task templates
│   ├── weather.ts       # Weather data caching
│   └── ui.ts            # UI state (loading, errors, modals)
├── services/            # API communication & utilities
│   ├── api.ts           # Base API client with retry logic
│   ├── timeUtils.ts     # UTC ↔ local time conversion
│   └── offline.ts       # Offline state management
├── composables/         # Vue 3 composition functions
│   ├── useTouch.ts      # Touch interaction handling
│   ├── useRetry.ts      # API retry with exponential backoff
│   └── useLocalTime.ts  # Time zone conversion utilities
└── router/              # Vue Router configuration
    └── index.ts         # Route definitions for tablet navigation
```

### State Management (Pinia)
```typescript
// stores/dailyTasks.ts - Main dashboard state
export const useDailyTasksStore = defineStore('dailyTasks', {
  state: () => ({
    tasksByMember: {} as Record<string, FamilyMemberTasks>,
    currentDate: new Date().toISOString().split('T')[0], // YYYY-MM-DD
    loading: false,
    error: null as string | null,
    lastUpdated: null as Date | null
  }),

  getters: {
    // Calculate total progress across all family members
    overallProgress: (state) => {
      const totals = Object.values(state.tasksByMember).reduce(
        (acc, member) => ({
          completed: acc.completed + member.progress.completed,
          total: acc.total + member.progress.total
        }),
        { completed: 0, total: 0 }
      )
      return totals
    }
  },

  actions: {
    async fetchTodaysTasks() {
      this.loading = true
      try {
        const response = await api.get(`/api/daily-tasks?date=${this.currentDate}`)
        this.tasksByMember = response.data.tasks_by_member
        this.lastUpdated = new Date()
      } catch (error) {
        this.error = 'Failed to fetch daily tasks'
        // Use cached data if available
      } finally {
        this.loading = false
      }
    },

    async completeTask(taskId: string, memberId: string) {
      // Optimistic update for immediate UI feedback
      const member = this.tasksByMember[memberId]
      const task = member?.tasks.find(t => t.id === taskId)
      
      if (task && member) {
        const oldStatus = task.status
        const oldCompleted = member.progress.completed
        
        // Update UI immediately
        task.status = 'Completed'
        task.completed_at = new Date().toISOString()
        member.progress.completed = oldCompleted + 1
        
        try {
          const response = await api.put(`/api/daily-tasks/${taskId}/complete`)
          // Update with server response for consistency
          member.progress = response.data.member_progress
        } catch (error) {
          // Revert optimistic changes on failure
          task.status = oldStatus
          task.completed_at = null
          member.progress.completed = oldCompleted
          this.error = 'Failed to complete task'
          
          // Retry logic handled by composable
          useRetry().scheduleRetry(() => this.completeTask(taskId, memberId))
        }
      }
    },

    async skipTask(taskId: string, memberId: string) {
      const member = this.tasksByMember[memberId]
      const task = member?.tasks.find(t => t.id === taskId)
      
      if (task) {
        const oldStatus = task.status
        task.status = 'Skipped'
        
        try {
          await api.put(`/api/daily-tasks/${taskId}/skip`)
        } catch (error) {
          task.status = oldStatus
          this.error = 'Failed to skip task'
        }
      }
    }
  }
})

// stores/family.ts - Family member management
export const useFamilyStore = defineStore('family', {
  state: () => ({
    members: [] as FamilyMember[],
    loading: false,
    error: null as string | null
  }),

  getters: {
    activeMembers: (state) => state.members.filter(m => m.status === 'Active'),
    people: (state) => state.members.filter(m => m.type === 'Person'),
    pets: (state) => state.members.filter(m => m.type === 'Pet')
  },

  actions: {
    async fetchMembers() {
      this.loading = true
      try {
        const response = await api.get('/api/family')
        this.members = response.data
      } catch (error) {
        this.error = 'Failed to fetch family members'
      } finally {
        this.loading = false
      }
    },

    async createMember(memberData: CreateFamilyMemberRequest) {
      try {
        const response = await api.post('/api/family', memberData)
        this.members.push(response.data)
        return response.data
      } catch (error) {
        this.error = 'Failed to create family member'
        throw error
      }
    }
  }
})

// stores/weather.ts - Weather data caching
export const useWeatherStore = defineStore('weather', {
  state: () => ({
    current: null as CurrentWeather | null,
    today: null as TodayWeather | null,
    forecast: [] as ForecastDay[],
    lastUpdated: null as Date | null,
    loading: false
  }),

  getters: {
    isStale: (state) => {
      if (!state.lastUpdated) return true
      return Date.now() - state.lastUpdated.getTime() > 30 * 60 * 1000 // 30 minutes
    }
  },

  actions: {
    async fetchWeather() {
      // Only fetch if data is stale
      if (!this.isStale && this.current) return
      
      this.loading = true
      try {
        const response = await api.get('/api/weather')
        this.current = response.data.current
        this.today = response.data.today
        this.forecast = response.data.forecast
        this.lastUpdated = new Date()
      } catch (error) {
        // Keep existing cached data on error
        console.warn('Weather update failed, using cached data')
      } finally {
        this.loading = false
      }
    }
  }
})
```

### Touch Interaction & Offline Handling
```typescript
// composables/useTouch.ts - Touch-optimized interactions
export function useTouch() {
  const handleTaskComplete = async (taskId: string, memberId: string) => {
    // Immediate visual feedback
    const element = document.querySelector(`[data-task-id="${taskId}"]`)
    element?.classList.add('completing')
    
    // Haptic feedback if available
    if ('vibrate' in navigator) {
      navigator.vibrate(50)
    }
    
    // Complete task with optimistic UI
    const dailyTasksStore = useDailyTasksStore()
    await dailyTasksStore.completeTask(taskId, memberId)
    
    element?.classList.remove('completing')
  }
  
  const handleTaskSkip = async (taskId: string, memberId: string) => {
    // Show confirmation for skip actions
    const confirmed = await showConfirmDialog('Skip this task?')
    if (confirmed) {
      const dailyTasksStore = useDailyTasksStore()
      await dailyTasksStore.skipTask(taskId, memberId)
    }
  }
  
  return { handleTaskComplete, handleTaskSkip }
}

// composables/useRetry.ts - Network retry logic
export function useRetry() {
  const retryQueue = ref<Array<{ fn: Function, attempts: number }>>([])
  
  const scheduleRetry = (fn: Function, maxAttempts = 3) => {
    const item = { fn, attempts: 0 }
    retryQueue.value.push(item)
    executeRetry(item, maxAttempts)
  }
  
  const executeRetry = async (item: any, maxAttempts: number) => {
    const delays = [1000, 2000, 5000] // Exponential backoff
    
    while (item.attempts < maxAttempts) {
      try {
        await item.fn()
        // Success - remove from queue
        const index = retryQueue.value.indexOf(item)
        if (index > -1) retryQueue.value.splice(index, 1)
        return
      } catch (error) {
        item.attempts++
        if (item.attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, delays[item.attempts - 1]))
        }
      }
    }
    
    // Max attempts reached - show user error
    const uiStore = useUIStore()
    uiStore.showError('Action failed after multiple attempts. Please try again.')
  }
  
  return { scheduleRetry, retryQueue: readonly(retryQueue) }
}

// composables/useLocalTime.ts - Time zone handling
export function useLocalTime() {
  const KITCHEN_TIMEZONE = 'America/New_York' // Hardcoded kitchen timezone
  
  const utcToLocal = (utcTimestamp: string): Date => {
    return new Date(utcTimestamp + 'Z') // Ensure UTC parsing
  }
  
  const localToUTC = (localDate: Date): string => {
    return localDate.toISOString()
  }
  
  const formatLocalTime = (utcTimestamp: string): string => {
    const local = utcToLocal(utcTimestamp)
    return local.toLocaleTimeString('en-US', {
      timeZone: KITCHEN_TIMEZONE,
      hour: 'numeric',
      minute: '2-digit'
    })
  }
  
  const isOverdue = (dueTimestamp: string): boolean => {
    const due = utcToLocal(dueTimestamp)
    return Date.now() > due.getTime()
  }
  
  return { utcToLocal, localToUTC, formatLocalTime, isOverdue }
}
```

### Offline & Performance Strategy
```typescript
// services/offline.ts - Offline state management
export class OfflineManager {
  private isOnline = ref(navigator.onLine)
  private pendingActions = ref<Array<any>>([])
  
  constructor() {
    window.addEventListener('online', this.handleOnline.bind(this))
    window.addEventListener('offline', this.handleOffline.bind(this))
  }
  
  private handleOnline() {
    this.isOnline.value = true
    this.processPendingActions()
  }
  
  private handleOffline() {
    this.isOnline.value = false
  }
  
  private async processPendingActions() {
    // Process queued actions when back online
    const actions = [...this.pendingActions.value]
    this.pendingActions.value = []
    
    for (const action of actions) {
      try {
        await action.execute()
      } catch (error) {
        // Re-queue failed actions
        this.pendingActions.value.push(action)
      }
    }
  }
  
  queueAction(action: any) {
    if (this.isOnline.value) {
      return action.execute()
    } else {
      this.pendingActions.value.push(action)
      return Promise.resolve() // Optimistic success for UI
    }
  }
}

// Performance optimizations:
// 1. Virtual scrolling for task lists (if >50 tasks)
// 2. Image lazy loading for family member avatars
// 3. Component lazy loading for admin panels
// 4. Local storage caching for frequently accessed data
// 5. Service worker for offline functionality (future enhancement)
```

## Data Synchronization

### Background Sync Strategy
```typescript
// services/backgroundSync.ts - Polling-based sync for single tablet
export class BackgroundSyncManager {
  private syncInterval: number | null = null
  private readonly SYNC_FREQUENCY = 5 * 60 * 1000 // 5 minutes
  
  startSync() {
    // Periodic sync every 5 minutes to catch background task updates
    this.syncInterval = window.setInterval(() => {
      this.performSync()
    }, this.SYNC_FREQUENCY)
    
    // Also sync on visibility change (when tablet screen turns on)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.performSync()
      }
    })
  }
  
  private async performSync() {
    try {
      // Refresh daily tasks (in case status changed via backend processes)
      const dailyTasksStore = useDailyTasksStore()
      await dailyTasksStore.fetchTodaysTasks()
      
      // Refresh weather data if stale
      const weatherStore = useWeatherStore()
      await weatherStore.fetchWeather()
      
      // Process any pending offline actions
      const offlineManager = useOfflineManager()
      await offlineManager.processPendingActions()
      
    } catch (error) {
      console.warn('Background sync failed:', error)
      // Fail silently - user can manually refresh
    }
  }
  
  stopSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval)
      this.syncInterval = null
    }
  }
}

// App.vue - Initialize background sync
export default defineComponent({
  name: 'App',
  setup() {
    const syncManager = new BackgroundSyncManager()
    
    onMounted(() => {
      syncManager.startSync()
    })
    
    onUnmounted(() => {
      syncManager.stopSync()
    })
    
    return {}
  }
})

// Manual refresh capability for user-triggered updates
export function useManualRefresh() {
  const isRefreshing = ref(false)
  
  const refresh = async () => {
    if (isRefreshing.value) return
    
    isRefreshing.value = true
    try {
      const dailyTasksStore = useDailyTasksStore()
      const weatherStore = useWeatherStore()
      
      await Promise.all([
        dailyTasksStore.fetchTodaysTasks(),
        weatherStore.fetchWeather()
      ])
      
      // Show success feedback
      const uiStore = useUIStore()
      uiStore.showSuccess('Data refreshed')
      
    } catch (error) {
      const uiStore = useUIStore()
      uiStore.showError('Refresh failed')
    } finally {
      isRefreshing.value = false
    }
  }
  
  return { refresh, isRefreshing: readonly(isRefreshing) }
}
```

## Security Implementation

### IP Allowlisting & Network Security
```python
# AWS API Gateway Resource Policy - IP Allowlisting
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "execute-api:Invoke",
            "Resource": "arn:aws:execute-api:*:*:*",
            "Condition": {
                "IpAddress": {
                    "aws:SourceIp": [
                        "192.168.1.100/32",  # Kitchen tablet IP
                        "192.168.1.0/24"     # Local network range (for development)
                    ]
                }
            }
        }
    ]
}

# CORS Configuration - Restrict to Amplify domain
CORS_ORIGINS = [
    "https://main.d1234567890.amplifyapp.com",  # Production Amplify URL
    "http://localhost:3000"  # Development only
]
```

### Input Validation
```python
# Pydantic models for request validation
from pydantic import BaseModel, validator, Field
from typing import Optional, Literal
from enum import Enum
import uuid
import re

class FamilyMemberType(str, Enum):
    PERSON = "Person"
    PET = "Pet"

class PetType(str, Enum):
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"

class Status(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class TaskFrequency(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"

class TaskCategory(str, Enum):
    MEDICATION = "Medication"
    FEEDING = "Feeding"
    OTHER = "Other"

class OverdueBehavior(str, Enum):
    IMMEDIATE = "Immediate"
    ONE_HOUR = "1 hour"
    SIX_HOURS = "6 hours"
    ONE_DAY = "1 day"

# Family Member Validation
class CreateFamilyMemberRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=15)
    type: FamilyMemberType
    pet_type: Optional[PetType] = None
    status: Status = Status.ACTIVE

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        # Only alphanumeric and spaces allowed
        if not re.match(r'^[a-zA-Z0-9\s]+$', v.strip()):
            raise ValueError('Name contains invalid characters')
        return v.strip()

    @validator('pet_type')
    def validate_pet_type(cls, v, values):
        if values.get('type') == FamilyMemberType.PET and not v:
            raise ValueError('Pet type is required for pets')
        if values.get('type') == FamilyMemberType.PERSON and v:
            raise ValueError('Pet type not allowed for people')
        return v

# Recurring Task Validation
class CreateRecurringTaskRequest(BaseModel):
    task_name: str = Field(..., min_length=1, max_length=30)
    assigned_to: str  # UUID of family member
    frequency: TaskFrequency
    due: str  # Morning/Evening for Daily, Mon-Sun for Weekly, 1-31 for Monthly
    overdue_when: OverdueBehavior
    category: TaskCategory
    status: Status = Status.ACTIVE

    @validator('task_name')
    def validate_task_name(cls, v):
        if not v.strip():
            raise ValueError('Task name cannot be empty')
        return v.strip()

    @validator('assigned_to')
    def validate_assigned_to(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid family member ID')
        return v

    @validator('due')
    def validate_due(cls, v, values):
        frequency = values.get('frequency')
        
        if frequency == TaskFrequency.DAILY:
            if v not in ['Morning', 'Evening']:
                raise ValueError('Daily tasks must be due Morning or Evening')
        elif frequency == TaskFrequency.WEEKLY:
            if v not in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                raise ValueError('Weekly tasks must specify a day of the week')
        elif frequency == TaskFrequency.MONTHLY:
            try:
                day = int(v)
                if day < 1 or day > 31:
                    raise ValueError('Monthly tasks must specify day 1-31')
            except ValueError:
                raise ValueError('Monthly tasks must specify a numeric day')
        
        return v

# Request sanitization and security
class SecurityMiddleware:
    @staticmethod
    def sanitize_input(data: dict) -> dict:
        """Remove potentially harmful characters from string inputs"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                # Remove HTML tags, scripts, and special characters
                sanitized[key] = re.sub(r'[<>"\']', '', value.strip())
            else:
                sanitized[key] = value
        return sanitized

    @staticmethod
    def validate_uuid_params(uuid_str: str) -> str:
        """Validate UUID parameters to prevent injection"""
        try:
            uuid.UUID(uuid_str)
            return uuid_str
        except ValueError:
            raise HTTPException(400, "Invalid ID format")

# Rate limiting per IP (implemented at API Gateway level)
RATE_LIMITS = {
    "requests_per_minute": 60,
    "requests_per_hour": 1000,
    "burst_limit": 100
}

### Data Protection & Privacy

#### AWS Parameter Store Configuration
```python
# OpenWeather API key stored in AWS Systems Manager Parameter Store
# Parameter Name: /house-mgmt/openweather-api-key
# Type: SecureString (encrypted with AWS KMS)
# 
# Setup completed in AWS Console:
# 1. Navigate to AWS Systems Manager > Parameter Store
# 2. Create parameter: /house-mgmt/openweather-api-key
# 3. Type: SecureString 
# 4. Value: [OpenWeather API key]
# 5. Configure Lambda execution role with ssm:GetParameter permission

import boto3
from botocore.exceptions import ClientError

class ParameterStoreConfig:
    def __init__(self):
        self.ssm_client = boto3.client('ssm')
        self.parameter_cache = {}
    
    def get_parameter(self, parameter_name: str, decrypt: bool = True) -> str:
        """Get parameter from AWS Parameter Store with caching"""
        if parameter_name in self.parameter_cache:
            return self.parameter_cache[parameter_name]
        
        try:
            response = self.ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=decrypt
            )
            value = response['Parameter']['Value']
            self.parameter_cache[parameter_name] = value
            return value
        except ClientError as e:
            logger.error(f"Failed to get parameter {parameter_name}: {e}")
            raise
    
    def get_openweather_api_key(self) -> str:
        """Get OpenWeather API key from Parameter Store"""
        return self.get_parameter('/house-mgmt/openweather-api-key')

# Environment variables for sensitive configuration
import os
from typing import Dict, Any

class SecurityConfig:
    def __init__(self):
        self.param_store = ParameterStoreConfig()
    
    # API Gateway and Lambda environment variables
    @property
    def OPENWEATHER_API_KEY(self) -> str:
        """Get OpenWeather API key from Parameter Store"""
        return self.param_store.get_openweather_api_key()
    
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
    
    # DynamoDB encryption at rest (enabled by default)
    # S3 server-side encryption for weather data (enabled by default)
    
    # No sensitive PII stored - only family names and basic task data
    # No financial, medical, or personal information beyond task names
    
    @staticmethod
    def get_allowed_ips() -> list:
        """Get IP allowlist from environment"""
        return os.getenv('ALLOWED_IPS', '192.168.1.100/32').split(',')

# CloudWatch logs configuration - no sensitive data logging
LOGGING_EXCLUDES = [
    'password', 'api_key', 'secret', 'token'
]

def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive fields from log output"""
    sanitized = {}
    for key, value in data.items():
        if any(exclude in key.lower() for exclude in LOGGING_EXCLUDES):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized
```

### Security Summary
- **Network Security**: IP allowlisting at API Gateway level
- **Data Validation**: Comprehensive Pydantic models with sanitization
- **Input Security**: UUID validation, character filtering, length limits
- **Rate Limiting**: Per-IP throttling via API Gateway
- **Data Protection**: No sensitive PII, basic family task data only
- **Encryption**: DynamoDB/S3 server-side encryption enabled
- **CORS**: Restricted to Amplify domain only
- **Logging**: Sensitive data excluded from CloudWatch logs
```

## Performance & Monitoring

### Caching Strategy
```python
# Multi-layer caching for optimal performance
import json
from datetime import datetime, timedelta

class CachingStrategy:
    # S3 caching for weather data (updated hourly)
    S3_WEATHER_CACHE_TTL = 3600  # 1 hour
    
    # DynamoDB caching via query optimization
    # - Family members: Rarely change, cache in frontend for session
    # - Daily tasks: Cache for 5 minutes, refresh on user action
    # - Recurring tasks: Cache for 30 minutes
    
    @staticmethod
    def should_refresh_daily_tasks(last_updated: datetime) -> bool:
        """Check if daily tasks cache needs refresh"""
        return datetime.utcnow() - last_updated > timedelta(minutes=5)
    
    @staticmethod
    def should_refresh_weather(last_updated: datetime) -> bool:
        """Check if weather cache needs refresh"""
        return datetime.utcnow() - last_updated > timedelta(minutes=30)

# Lambda performance optimizations
LAMBDA_CONFIG = {
    "memory_size": 512,  # MB - sufficient for FastAPI + DynamoDB operations
    "timeout": 30,       # seconds - API Gateway max timeout
    "environment": {
        "PYTHONPATH": "/var/task",
        "LOG_LEVEL": "INFO"
    },
    # Cold start mitigation
    "provisioned_concurrency": 1,  # Keep 1 instance warm during peak hours
    "reserved_concurrency": 10     # Limit concurrent executions
}

# DynamoDB performance tuning
DYNAMODB_CONFIG = {
    "table_class": "STANDARD",
    "billing_mode": "PAY_PER_REQUEST",  # No need to predict capacity
    "point_in_time_recovery": True,
    # Global Secondary Index optimization
    "gsi_projection": "ALL",  # Include all attributes for complex queries
    # Query optimization patterns
    "batch_size": 25,        # DynamoDB batch operations limit
    "parallel_scan": False   # Single tablet use case doesn't need parallel scanning
}
```

### Error Handling & Logging
```python
import structlog
import uuid
from fastapi import Request, HTTPException
import traceback

# Structured logging with correlation IDs for debugging
logger = structlog.get_logger()

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = str(uuid.uuid4())[:8]  # Short ID for kitchen tablet logs
    request.state.correlation_id = correlation_id
    
    # Log only essential info (no sensitive data)
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path.split('?')[0],  # Remove query params
        correlation_id=correlation_id,
        source_ip=request.client.host if request.client else "unknown"
    )
    
    start_time = datetime.utcnow()
    response = await call_next(request)
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(
        "request_completed",
        status_code=response.status_code,
        duration_ms=int(duration * 1000),
        correlation_id=correlation_id
    )
    
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    # Log error details for debugging (excluding sensitive data)
    logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        correlation_id=correlation_id,
        path=request.url.path,
        # Don't log full traceback in production for security
        traceback=traceback.format_exc() if os.getenv('LOG_LEVEL') == 'DEBUG' else None
    )
    
    # Return generic error to frontend
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred",
            "code": "INTERNAL_ERROR",
            "correlation_id": correlation_id
        }
    )

# Health check monitoring
@app.get("/api/health")
async def health_check():
    """Health endpoint for monitoring systems"""
    try:
        # Test DynamoDB connection
        await test_dynamodb_connection()
        
        # Test S3 weather data access
        await test_s3_weather_access()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": os.getenv('APP_VERSION', 'unknown')
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(500, "Health check failed")

# CloudWatch metrics for monitoring
CUSTOM_METRICS = {
    "task_completions_per_hour": "Count",
    "api_response_time": "Milliseconds", 
    "weather_api_failures": "Count",
    "background_task_failures": "Count"
}
```

## Deployment & Infrastructure

### AWS SAM Configuration
```yaml
# template.yaml - House Management Infrastructure
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: House Management System - Backend Infrastructure

Parameters:
  AllowedIPs:
    Type: CommaDelimitedList
    Default: "192.168.1.100/32"
    Description: IP addresses allowed to access the API
  # OpenWeather API key stored in AWS Parameter Store instead of template parameter
  # Parameter Store path: /house-mgmt/openweather-api-key

Globals:
  Function:
    Runtime: python3.11
    MemorySize: 512
    Timeout: 30
    Environment:
      Variables:
        DYNAMODB_TABLE: !Ref HouseMgmtTable
        S3_WEATHER_BUCKET: !Ref WeatherDataBucket
        # OpenWeather API key retrieved from Parameter Store, not environment variable
        LOG_LEVEL: INFO

Resources:
  # DynamoDB Table for all house management data
  HouseMgmtTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "house-mgmt-${AWS::StackName}"
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK  
          AttributeType: S
        - AttributeName: GSI1PK
          AttributeType: S
        - AttributeName: GSI1SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      GlobalSecondaryIndexes:
        - IndexName: GSI1
          KeySchema:
            - AttributeName: GSI1PK
              KeyType: HASH
            - AttributeName: GSI1SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
      BillingMode: PAY_PER_REQUEST
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      SSESpecification:
        SSEEnabled: true

  # S3 Bucket for weather data caching
  WeatherDataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "house-mgmt-weather-${AWS::StackName}"
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

  # Main API Lambda Function
  HouseMgmtApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "house-mgmt-api-${AWS::StackName}"
      CodeUri: src/
      Handler: main.handler
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref HouseMgmtApi
            Path: /{proxy+}
            Method: ANY
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref HouseMgmtTable
        - S3ReadPolicy:
            BucketName: !Ref WeatherDataBucket
        - Statement:
            - Effect: Allow
              Action:
                - ssm:GetParameter
              Resource: !Sub "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/house-mgmt/*"

  # Weather Update Lambda Function
  WeatherUpdateFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "house-mgmt-weather-${AWS::StackName}"
      CodeUri: src/
      Handler: weather.handler
      Events:
        WeatherSchedule:
          Type: Schedule
          Properties:
            Schedule: rate(1 hour)
            Description: "Update weather data hourly"
      Policies:
        - S3WritePolicy:
            BucketName: !Ref WeatherDataBucket
        - Statement:
            - Effect: Allow
              Action:
                - ssm:GetParameter
              Resource: !Sub "arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/house-mgmt/*"

  # Daily Task Generation Lambda Function
  TaskGenerationFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub "house-mgmt-tasks-${AWS::StackName}"
      CodeUri: src/
      Handler: tasks.handler
      Events:
        TaskSchedule:
          Type: Schedule
          Properties:
            Schedule: cron(0 5 * * ? *)  # 5 AM UTC = Midnight EST
            Description: "Generate daily tasks at local midnight"
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref HouseMgmtTable

  # API Gateway with IP restrictions
  HouseMgmtApi:
    Type: AWS::Serverless::Api
    Properties:
      Name: !Sub "house-mgmt-api-${AWS::StackName}"
      StageName: prod
      Cors:
        AllowMethods: "'GET,POST,PUT,DELETE,OPTIONS'"
        AllowHeaders: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
        AllowOrigin: "'*'"  # Restricted by resource policy below
      Auth:
        ResourcePolicy:
          CustomStatements:
            - Effect: Allow
              Principal: "*"
              Action: execute-api:Invoke
              Resource: "execute-api:/*"
              Condition:
                IpAddress:
                  aws:SourceIp: !Ref AllowedIPs

Outputs:
  ApiUrl:
    Description: "API Gateway endpoint URL"
    Value: !Sub "https://${HouseMgmtApi}.execute-api.${AWS::Region}.amazonaws.com/prod"
    Export:
      Name: !Sub "${AWS::StackName}-ApiUrl"
  
  DynamoDBTable:
    Description: "DynamoDB table name"
    Value: !Ref HouseMgmtTable
    Export:
      Name: !Sub "${AWS::StackName}-TableName"
```

### GitHub Actions CI/CD
```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend
on:
  push:
    branches: [main]
    paths: ['backend/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install SAM CLI
        uses: aws-actions/setup-sam@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy with SAM
        run: |
          cd backend
          sam build
          sam deploy --no-confirm-changeset --no-fail-on-empty-changeset \
            --parameter-overrides \
              AllowedIPs="${{ secrets.ALLOWED_IPS }}"
          # Note: OpenWeather API key is stored in AWS Parameter Store, not GitHub Secrets
```

### Deployment Summary
- **Frontend**: AWS Amplify (automatic deployment from Git)
- **Backend**: AWS SAM + GitHub Actions CI/CD
- **Infrastructure**: CloudFormation via SAM template
- **Security**: IP allowlisting, encrypted storage, no authentication needed
- **Monitoring**: CloudWatch logs, custom metrics, health checks
- **Scaling**: Serverless auto-scaling based on demand

---

**Next Step:** Create development phases and milestones in `06-IMPLEMENTATION-PLAN.md`