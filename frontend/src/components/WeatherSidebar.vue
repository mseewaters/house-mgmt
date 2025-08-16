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
  width: var(--sidebar-width);
  background-color: var(--bg-sidebar);
  color: var(--text-white);
  padding: var(--spacing-lg); /* Reduced from xl */
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  flex-shrink: 0;
  max-height: 100vh;
}

/* Sidebar Content */
.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0; /* Allow shrinking */
}

/* Responsive DateTime Section */
.datetime-section {
  margin-bottom: var(--spacing-lg);
  text-align: center;
  flex-shrink: 0; /* Keep datetime visible */
}

.day-date {
  font-size: clamp(16px, 3vw, 20px);
  color: var(--text-white-muted);
  margin-bottom: 6px;
  font-weight: 500;
}

.time-display {
  font-size: clamp(32px, 6vw, 42px);
  font-weight: 700;
  color: var(--text-white);
  text-shadow: 1px 1px 4px var(--accent-red);
  margin-bottom: var(--spacing-md);
  line-height: 1;
}

/* Responsive Weather Section */
.weather-section {
  background: var(--bg-weather-section);
  border-radius: 12px;
  padding: var(--spacing-md); /* Reduced padding */
  backdrop-filter: blur(10px);
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  min-height: 0;
  overflow-y: auto;
}

/* Compact Weather Current */
.weather-current {
  text-align: center;
  flex-shrink: 0;
}

.weather-icon {
  font-size: clamp(40px, 6vw, 60px); /* Responsive icon size */
  margin-bottom: 0px;
  line-height: 1;
}

.weather-desc {
  font-size: clamp(24px, 4vw, 32px); /* Responsive description */
  color: var(--text-white);
  margin-bottom: var(--spacing-sm);
  text-transform: capitalize;
  line-height: 1.2;
}

.temp-section {
  margin-bottom: var(--spacing-sm);
}

.temp-high, .temp-low {
  font-size: clamp(18px, 3vw, 22px); /* Responsive temps */
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--text-white);
}

.weather-details {
  font-size: clamp(14px, 2.5vw, 18px);
  color: var(--text-white);
  line-height: 1.4;
}

/* Compact Forecast Section */
.forecast-section {
  border-top: 1px solid var(--border-weather);
  padding-top: var(--spacing-sm);
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.forecast-list {
  display: flex;
  flex-direction: column;
  gap: 4px; /* Reduced gap */
}

.forecast-day {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: clamp(12px, 2vw, 14px); /* Responsive forecast text */
  padding: 2px 0;
}

.forecast-name {
  font-weight: 500;
  min-width: 50px;
  color: var(--text-white-muted);
}

.forecast-icon {
  font-size: clamp(18px, 3vw, 24px); /* Smaller forecast icons */
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

/* Compact Weather Updated */
.weather-updated {
  text-align: center;
  font-size: clamp(8px, 1.5vw, 10px);
  color: var(--text-white-light);
  margin-top: auto;
  padding-top: var(--spacing-sm);
  flex-shrink: 0;
}

/* Fire Tablet Specific Adjustments */
@media screen and (max-height: 800px) {
  .sidebar {
    padding: var(--spacing-md); /* Even smaller padding on short screens */
  }
  
  .datetime-section {
    margin-bottom: var(--spacing-md);
  }
  
  .weather-section {
    padding: var(--spacing-sm);
    gap: var(--spacing-sm);
  }
  
  .forecast-list {
    gap: 2px; /* Very tight spacing on short screens */
  }
  
  /* Ensure timestamp shows on Fire tablets */
  .weather-updated {
    font-size: 9px;
    margin-top: var(--spacing-xs);
    padding-top: var(--spacing-xs);
  }
}

/* Landscape Fire Tablet (shorter height) */
@media screen and (max-height: 600px) {
  .time-display {
    font-size: 28px; /* Smaller time for landscape */
    margin-bottom: var(--spacing-sm);
  }
  
  .weather-icon {
    font-size: 40px; /* Much smaller weather icon */
  }
  
  .weather-desc {
    font-size: 20px;
    margin-bottom: 4px;
  }
  
  .temp-high, .temp-low {
    font-size: 16px;
    margin-bottom: 2px;
  }
  
  .weather-details {
    font-size: 14px;
    line-height: 1.3;
  }
}

</style>