<template>
  <div class="sidebar">
    <div class="sidebar-content">
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
          <div class="forecast-list">
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
import { useHouseStore } from '../stores/house.js'

// Store
const store = useHouseStore()

// Methods
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
  width: var(--sidebar-width);
  padding: 15px;
  flex-shrink: 0;
}

/* Sidebar Content */
.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* DateTime Section */
.datetime-section {
  margin-bottom: 20px;
  text-align: center;
}

.day-date {
  font-size: 20px;
  color: var(--text-white-muted);
  margin-bottom: 8px;
  font-weight: 500;
}

.time-display {
  font-size: 42px;
  font-weight: 700;
  color: var(--text-white);
  text-shadow: 1px 1px 4px var(--accent-red);
  margin-bottom: 16px;
  line-height: 1;
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

/* Current Weather */
.weather-current {
  text-align: center;
}

.weather-icon {
  font-size: 70px;
  margin-bottom: 0px;
}

.weather-desc {
  font-size: 32px;
  color: var(--text-white);
  margin-bottom: 15px;
  text-transform: capitalize;
  line-height: 1.4;
}

.temp-section {
  margin-bottom: 15px;
}

.temp-high, .temp-low {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text-white);
}

.weather-details {
  font-size: 18px;
  color: var(--text-white);
  line-height: 1.6;
}

/* Forecast Section */
.forecast-section {
  border-top: 1px solid var(--border-weather);
  padding-top: 15px;
}

.forecast-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.forecast-day {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
}

.forecast-name {
  font-weight: 500;
  min-width: 60px;
  color: var(--text-white-muted);
}

.forecast-icon {
  font-size: 24px;
}

.forecast-temps {
  color: var(--text-white-muted);
  text-align: right;
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

.retry-button:active {
  transform: scale(0.95);
}

/* Weather Updated */
.weather-updated {
  text-align: center;
  font-size: 10px;
  color: var(--text-white-light);
  margin-top: auto;
  padding-top: 10px;
}
</style>