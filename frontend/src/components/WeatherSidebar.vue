<template>
  <div class="sidebar" :class="sidebarClasses">
    <!-- Collapsed State: Just expand button -->
    <div v-if="state === 'collapsed'" class="collapsed-content">
      <button class="expand-button" @click="toggleState" title="Expand Weather">
        🌤️
      </button>
    </div>

    <!-- Default & Expanded States: Full content -->
    <div v-else class="sidebar-content">
      <!-- Header with toggle button -->
      <div class="sidebar-header">
        <h2 v-if="state === 'expanded'" class="sidebar-title">Weather</h2>
        <button class="toggle-button" @click="toggleState" :title="toggleButtonTitle">
          {{ toggleButtonIcon }}
        </button>
      </div>
      
      <!-- DateTime Section -->
      <div class="datetime-section">
        <div class="day-date">{{ store.currentDayName }}, {{ store.currentMonth }} {{ store.currentDay }}</div>
        <div class="time-display">{{ store.currentTime }}</div>
      </div>
      
      <!-- Weather Section -->
      <div class="weather-section" v-if="store.weather">
        <!-- Current Weather -->
        <div class="weather-current">
          <div class="weather-icon">{{ getWeatherEmoji(store.weather.today.icon) }}</div>
          <div class="weather-desc">{{ store.weather.today.condition }}</div>
          
          <div class="temp-section">
            <div class="temp-high">High: {{ store.weather.today.high }}°F</div>
            <div class="temp-low">Low: {{ store.weather.today.low }}°F</div>
          </div>
          
          <div class="weather-details">
            <div>Humidity: {{ store.weather.current.humidity }}%</div>
            <div>Wind: {{ store.weather.current.wind_speed }} mph</div>
          </div>
        </div>
        
        <!-- Forecast Section -->
        <div class="forecast-section">
          <h4 v-if="state === 'expanded'" class="forecast-title">5-Day Forecast</h4>
          
          <div class="forecast-list" :class="{ 'forecast-expanded': state === 'expanded' }">
            <div 
              v-for="day in store.weather.forecast" 
              :key="day.day"
              class="forecast-day"
            >
              <div class="forecast-icon">{{ getWeatherEmoji(day.icon) }}</div>
              <div class="forecast-name">{{ day.day }}</div>
              <div class="forecast-temps">H: {{ day.high }} L: {{ day.low }}</div>
            </div>
          </div>
        </div>

        <!-- Focus Items Preview (Default state only) -->
        <div v-if="state === 'default' && store.focusItems.length > 0" class="focus-preview">
          <div class="focus-header">
            <span class="focus-count">{{ store.focusItems.length }}</span>
            <span class="focus-label">items need attention</span>
          </div>
        </div>

        <!-- Weather timestamp -->
        <div class="weather-updated">
          Last updated: {{ formatWeatherTime(store.weather.updated_at) }}
        </div>
      </div>

      <!-- Loading state -->
      <div v-else-if="store.loading.weather" class="loading-state">
        <div class="loading-spinner">⏳</div>
        <div>Loading weather...</div>
      </div>

      <!-- Error state -->
      <div v-else-if="store.errors.weather" class="error-state">
        <div class="error-icon">❌</div>
        <div>{{ store.errors.weather }}</div>
        <button @click="store.loadWeather()" class="retry-button">Retry</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useHouseStore } from '../stores/house.js'

// Props
const props = defineProps({
  state: {
    type: String,
    default: 'default',
    validator: (value) => ['collapsed', 'default', 'expanded'].includes(value)
  }
})

// Emits
const emit = defineEmits(['toggle-state'])

// Store
const store = useHouseStore()

// Computed properties
const sidebarClasses = computed(() => ({
  'sidebar-collapsed': props.state === 'collapsed',
  'sidebar-default': props.state === 'default',
  'sidebar-expanded': props.state === 'expanded'
}))

const toggleButtonIcon = computed(() => {
  switch (props.state) {
    case 'default': return '⛶' // Expand
    case 'expanded': return '⚏' // Collapse
    default: return '🌤️'
  }
})

const toggleButtonTitle = computed(() => {
  switch (props.state) {
    case 'default': return 'Expand Weather Panel'
    case 'expanded': return 'Collapse Weather Panel'
    default: return 'Show Weather'
  }
})

// Methods
function toggleState() {
  emit('toggle-state')
}

function getWeatherEmoji(iconCode) {
  const iconMap = {
    '01d': '☀️', '01n': '🌙',
    '02d': '🌤️', '02n': '☁️',
    '03d': '☁️', '03n': '☁️',
    '04d': '☁️', '04n': '☁️',
    '09d': '🌧️', '09n': '🌧️',
    '10d': '🌧️', '10n': '🌧️',
    '11d': '⚡', '11n': '⚡',
    '13d': '❄️', '13n': '❄️',
    '50d': '🌫️', '50n': '🌫️'
  }
  return iconMap[iconCode] || '🌤️'
}

function formatWeatherTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], {hour: 'numeric', minute:'2-digit'})
}
</script>

<style scoped>
/* Base Sidebar Styles */
.sidebar {
  background: var(--bg-sidebar);
  color: var(--text-white);
  display: flex;
  flex-direction: column;
  transition: var(--transition-normal);
  position: relative;
  flex-shrink: 0;
}

/* State-specific widths */
.sidebar-collapsed {
  width: 50px;
  padding: 10px 5px;
}

.sidebar-default {
  width: var(--sidebar-width);
  padding: 15px 15px;
}

.sidebar-expanded {
  width: 400px;
  padding: 20px 20px;
}

/* Collapsed Content */
.collapsed-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: center;
}

.expand-button {
  background: rgba(255,255,255,0.1);
  border: none;
  color: var(--text-white);
  padding: 12px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 20px;
  transition: var(--transition-normal);
  min-height: var(--touch-target);
  min-width: var(--touch-target);
}

.expand-button:hover {
  background: rgba(255,255,255,0.2);
  transform: scale(1.05);
}

/* Sidebar Content */
.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Header */
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.sidebar-title {
  font-family: var(--font-family-display);
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}

.toggle-button {
  background: rgba(255,255,255,0.1);
  border: none;
  color: var(--text-white);
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  transition: var(--transition-normal);
  min-height: var(--touch-target);
  min-width: var(--touch-target);
}

.toggle-button:hover {
  background: rgba(255,255,255,0.2);
}

/* DateTime Section */
.datetime-section {
  margin-bottom: 20px;
  text-align: center;
}

.day-date {
  font-size: 18px;
  color: var(--text-white-muted);
  margin-bottom: 8px;
  font-weight: 500;
}

.sidebar-expanded .day-date {
  font-size: 24px;
  margin-bottom: 12px;
}

.time-display {
  font-size: 36px;
  font-weight: 700;
  color: var(--text-white);
  text-shadow: 1px 1px 4px var(--accent-red);
  margin-bottom: 4px;
  line-height: 1;
}

.sidebar-expanded .time-display {
  font-size: 64px;
  margin-bottom: 20px;
}

/* Weather Section */
.weather-section {
  background: var(--bg-weather-section);
  border-radius: 12px;
  padding: 15px;
  backdrop-filter: blur(10px);
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sidebar-expanded .weather-section {
  padding: 25px;
  gap: 25px;
}

/* Current Weather */
.weather-current {
  text-align: center;
}

.weather-icon {
  font-size: 50px;
  margin-bottom: 10px;
}

.sidebar-expanded .weather-icon {
  font-size: 80px;
  margin-bottom: 15px;
}

.weather-desc {
  font-size: 20px;
  color: var(--text-white);
  margin-bottom: 15px;
  text-transform: capitalize;
  line-height: 1.4;
}

.sidebar-expanded .weather-desc {
  font-size: 28px;
  margin-bottom: 20px;
}

.temp-section {
  margin-bottom: 15px;
}

.temp-high, .temp-low {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text-white);
}

.sidebar-expanded .temp-high,
.sidebar-expanded .temp-low {
  font-size: 24px;
  margin-bottom: 8px;
}

.weather-details {
  font-size: 14px;
  color: var(--text-white);
  line-height: 1.6;
}

.sidebar-expanded .weather-details {
  font-size: 18px;
  line-height: 1.8;
}

/* Forecast Section */
.forecast-section {
  border-top: 1px solid var(--border-weather);
  padding-top: 15px;
}

.forecast-title {
  font-weight: 600;
  margin-bottom: 15px;
  font-size: 16px;
}

.forecast-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.forecast-list.forecast-expanded {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.forecast-day {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
}

.forecast-expanded .forecast-day {
  flex-direction: column;
  text-align: center;
  gap: 8px;
  padding: 10px;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  font-size: 14px;
}

.forecast-name {
  font-weight: 500;
  min-width: 60px;
  color: var(--text-white-muted);
}

.forecast-icon {
  font-size: 16px;
}

.forecast-expanded .forecast-icon {
  font-size: 32px;
}

.forecast-temps {
  color: var(--text-white-muted);
  text-align: right;
}

/* Focus Preview */
.focus-preview {
  background: rgba(196, 12, 12, 0.2);
  border: 1px solid rgba(196, 12, 12, 0.4);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.focus-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.focus-count {
  background: var(--accent-red);
  color: var(--text-white);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
}

.focus-label {
  font-size: 12px;
  color: var(--text-white-muted);
}

/* States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
  color: var(--text-white-muted);
  flex: 1;
}

.loading-spinner,
.error-icon {
  font-size: 2rem;
  margin-bottom: 10px;
}

.retry-button {
  margin-top: 10px;
  padding: 8px 16px;
  background: var(--accent-red);
  color: var(--text-white);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: var(--transition-normal);
}

.retry-button:hover {
  background: #a00a0a;
}

/* Weather Updated */
.weather-updated {
  text-align: center;
  font-size: 10px;
  color: var(--text-white-light);
  margin-top: auto;
  padding-top: 10px;
}

.sidebar-expanded .weather-updated {
  font-size: 12px;
}

/* Touch interactions */
.expand-button:active,
.toggle-button:active,
.retry-button:active {
  transform: scale(0.95);
}
</style>