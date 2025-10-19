<template>
  <div class="clock-view">
    <!-- Main Clock Section (Top Left - 80%) -->
    <div class="clock-section">
      <div class="day-name">{{ store.currentDayName }}</div>
      <div class="time-display">{{ store.currentTime }}</div>
      <div class="date-display">
        <span class="day-number">{{ store.currentDay }}</span>
        <span class="month-name">{{ store.currentMonth }}</span>
        <span class="year-number">{{ new Date().getFullYear() }}</span>
      </div>
    </div>

    <!-- Overdue Tasks Section (Top Right - 20%) -->
    <div class="overdue-section">
      <div class="overdue-header">Overdue Tasks</div>
      <div v-if="overdueByPerson.length > 0" class="overdue-list">
        <div 
          v-for="person in overdueByPerson" 
          :key="person.memberId"
          class="overdue-person"
        >
          <div class="person-initial" :class="getPersonClass(person.memberId)">
            {{ person.avatar }}
          </div>
          <div class="person-name">{{ person.name }}</div>
          <div class="overdue-count">{{ person.count }}</div>
        </div>
      </div>
      <div v-else class="no-overdue">
        <div class="success-icon">✓</div>
        <div class="success-text">All caught up!</div>
      </div>
    </div>

    <!-- Weather Section (Bottom - 100%) -->
    <div class="weather-section">
      <div class="weather-header">Weather in Cranbury, NJ</div>
      
      <div class="weather-container">
        <!-- Today's Weather (25% left) -->
        <div v-if="store.weather?.today" class="weather-today">
          <div class="today-label">Today</div>
          <div class="today-content">
            <div class="today-temps">
              <div class="temp-line">Low: <span class="temp-value">{{ store.weather.today.low }}°F</span></div>
              <div class="temp-line">High: <span class="temp-value">{{ store.weather.today.high }}°F</span></div>
              <div class="detail-line">Humidity: {{ store.weather.current.humidity }}%</div>
              <div class="detail-line">Wind: {{ store.weather.current.wind_speed }} mph</div>
            </div>
            <div class="today-icon">
              <div class="weather-emoji">{{ getWeatherEmoji(store.weather.today.icon) }}</div>
              <div class="condition-text">{{ store.weather.today.condition }}</div>
            </div>
          </div>
        </div>
        <div v-else class="weather-today weather-loading">
          <div class="loading-text">Loading weather...</div>
        </div>

        <!-- This Week Forecast (75% right) -->
        <div v-if="store.weather?.forecast?.length > 0" class="weather-forecast">
          <div class="forecast-label">This Week</div>
          <div class="forecast-days">
            <div 
              v-for="day in store.weather.forecast.slice(0, 5)" 
              :key="day.day"
              class="forecast-day"
            >
              <div class="forecast-day-name">{{ day.day }}</div>
              <div class="forecast-icon">{{ getWeatherEmoji(day.icon) }}</div>
              <div class="forecast-high">{{ day.high }}°F</div>
              <div class="forecast-low">{{ day.low }}°F</div>
            </div>
          </div>
        </div>
        <div v-else class="weather-forecast weather-loading">
          <div class="loading-text">Loading forecast...</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useHouseStore } from '../stores/house.js'

const store = useHouseStore()

// Computed: Group overdue tasks by person
const overdueByPerson = computed(() => {
  const tasksByPerson = {}
  
  store.overdueTasks.forEach(task => {
    if (!tasksByPerson[task.assigned_to]) {
      const member = store.familyMembers.find(m => m.member_id === task.assigned_to)
      tasksByPerson[task.assigned_to] = {
        memberId: task.assigned_to,
        name: member?.name || 'Unknown',
        avatar: task.member_avatar,
        count: 0
      }
    }
    tasksByPerson[task.assigned_to].count++
  })
  
  return Object.values(tasksByPerson).sort((a, b) => a.name.localeCompare(b.name))
})

// Helper: Get person color class
function getPersonClass(memberId) {
  const member = store.familyMembers.find(m => m.member_id === memberId)
  if (!member) return 'person-unknown'
  
  const colors = ['person-blue', 'person-green', 'person-purple', 'person-orange', 'person-pink']
  const index = store.familyMembers.indexOf(member)
  return colors[index % colors.length]
}

// Helper: Get day name from date string
function getDayName(dateStr) {
  const date = new Date(dateStr)
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  
  if (date.toDateString() === tomorrow.toDateString()) {
    return 'Tomorrow'
  }
  
  return date.toLocaleDateString('en-US', { weekday: 'long' })
}

// Helper: Get weather emoji
function getWeatherEmoji(icon) {
  if (!icon) return '☁️'
  
  // OpenWeather icon codes: 01d/01n = clear, 02d/02n = few clouds, etc.
  const iconMap = {
    '01': '☀️',  // clear sky
    '02': '🌤️',  // few clouds
    '03': '☁️',  // scattered clouds
    '04': '☁️',  // broken clouds
    '09': '🌧️',  // shower rain
    '10': '🌦️',  // rain
    '11': '⛈️',  // thunderstorm
    '13': '❄️',  // snow
    '50': '🌫️'   // mist
  }
  
  const iconCode = icon.substring(0, 2)
  return iconMap[iconCode] || '☁️'
}

// Lifecycle: Initialize and auto-refresh
onMounted(async () => {
  console.log('🕐 ClockView mounted - initializing...')
  
  // Initialize store data
  await store.initializeData()
  
  // Update time every second for smooth clock
  const timeInterval = setInterval(() => {
    store.updateDateTime()
  }, 1000)
  
  // Refresh weather every 30 minutes
  const weatherInterval = setInterval(() => {
    store.loadWeather()
  }, 30 * 60 * 1000)
  
  // Refresh tasks every 5 minutes
  const taskInterval = setInterval(() => {
    store.loadDailyTasks()
  }, 5 * 60 * 1000)
  
  // Cleanup on unmount
  onUnmounted(() => {
    clearInterval(timeInterval)
    clearInterval(weatherInterval)
    clearInterval(taskInterval)
  })
  
  console.log('✅ ClockView ready!')
})
</script>

<style scoped>
/* Clock View Layout - Full Screen Standalone */
.clock-view {
  position: fixed !important;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: grid !important;
  grid-template-areas:
    "clock overdue"
    "weather weather" !important;
  grid-template-columns: 80% 20% !important;
  grid-template-rows: 50% 50% !important;
  gap: 20px;
  padding: 40px;
  background: var(--bg-sidebar);
  color: var(--text-white);
  font-family: var(--font-family-display);
  overflow: hidden;
  align-items: stretch !important;
}

/* Clock Section */
.clock-section {
  grid-area: clock;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  height: 100%;
}

.day-name {
  font-size: clamp(60px, 8vw, 120px);
  font-weight: 700;
  color: var(--text-white);
  letter-spacing: 2px;
}

.time-display {
  font-size: clamp(80px, 12vw, 180px);
  font-weight: 700;
  color: var(--accent-success);
  letter-spacing: 4px;
  line-height: 1;
}

.date-display {
  display: flex;
  gap: 20px;
  font-size: clamp(40px, 5vw, 80px);
  font-weight: 600;
  color: var(--text-white);
}

.day-number {
  color: var(--text-white);
}

.month-name {
  color: var(--text-white);
}

.year-number {
  color: var(--text-white);
}

/* Overdue Section - Compact Right Side */
.overdue-section {
  grid-area: overdue;
  background: var(--bg-weather-section);
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  min-height: 100%;
}

.overdue-header {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent-success);
  margin-bottom: 12px;
  flex-shrink: 0;
  text-align: center;
}

.overdue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  flex: 1; /* Take remaining space */
}

.overdue-person {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.overdue-person:hover {
  background: rgba(255, 255, 255, 0.1);
}

.person-initial {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
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

.person-name {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-white);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overdue-count {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-success);
  min-width: 32px;
  text-align: center;
  flex-shrink: 0;
}

/* No Overdue State */
.no-overdue {
  flex: 1; /* Take full remaining space */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.success-icon {
  font-size: 48px;
  color: var(--accent-success);
}

.success-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-success);
  text-align: center;
}

/* Weather Section */
.weather-section {
  grid-area: weather;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.weather-header {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-success);
}

/* Weather Container - 25/75 Split */
.weather-container {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

/* Today's Weather - 25% Left */
.weather-today {
  flex: 0 0 40%;
  background: var(--bg-weather-section);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.today-label {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-success);
  margin-bottom: 12px;
}

.today-content {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.today-temps {
  flex: 1;
}

.temp-line {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-white);
  margin-bottom: 6px;
}

.temp-value {
  font-weight: 700;
}

.detail-line {
  font-size: 24px;
  color: var(--text-white-muted);
  margin-bottom: 4px;
}

.today-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.weather-emoji {
  font-size: 80px;
  line-height: 1;
}

.condition-text {
  font-size: 24px;
  color: var(--text-white-muted);
  text-align: center;
}

/* Weather Loading State */
.weather-loading {
  background: var(--bg-weather-section);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: 18px;
  color: var(--text-white-muted);
  font-style: italic;
}

/* Forecast - 75% Right */
.weather-forecast {
  flex: 0 0 55%;
  background: var(--bg-weather-section);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.forecast-label {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-success);
  margin-bottom: 16px;
}

.forecast-days {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.forecast-day {
  flex: 1;
  text-align: center;
}

.forecast-day-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-white);
  margin-bottom: 8px;
}

.forecast-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.forecast-high {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-white);
}

.forecast-low {
  font-size: 24px;
  color: var(--text-white-muted);
}

/* Responsive adjustments */
@media (max-width: 1280px) {
  .clock-view {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    grid-template-areas:
      "clock"
      "overdue"
      "weather";
    padding: 20px;
    gap: 16px;
  }
  
  .overdue-section {
    max-height: 200px;
  }
  
  .day-name {
    font-size: 60px;
  }
  
  .time-display {
    font-size: 100px;
  }
  
  .date-display {
    font-size: 40px;
  }
}

/* Fire 10 HD Tablet Optimizations (1920x1200) */
@media (min-width: 1900px) {
  .clock-view {
    padding: 60px;
    gap: 30px;
  }
  
  .day-name {
    font-size: 140px;
  }
  
  .time-display {
    font-size: 220px;
  }
  
  .date-display {
    font-size: 100px;
  }
}
</style>