<template>
  <div class="meals-view">
    <div class="header">
      <div class="filter-controls">
        <select v-model="statusFilter" @change="fetchMeals" class="status-filter">
          <option value="">All Meals</option>
          <option value="available">Available</option>
          <option value="prepared">Prepared</option>
          <option value="expired">Expired</option>
        </select>
        <button @click="refreshMeals" class="refresh-btn" :disabled="loading">
          <span v-if="loading">⟳</span>
          <span v-else">↻</span>
          Refresh
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && Object.keys(mealsByDate).length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>Loading meals...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="fetchMeals" class="retry-btn">Try Again</button>
    </div>

    <!-- Empty State -->
    <div v-else-if="Object.keys(mealsByDate).length === 0" class="empty-state">
      <div class="empty-icon">🍽️</div>
      <h3>No meals found</h3>
      <p v-if="statusFilter">No meals found with status "{{ statusFilter }}"</p>
      <p v-else">No meals have been delivered yet.</p>
    </div>

    <!-- Meals by Date -->
    <div v-else class="meals-by-date">
      <div 
        v-for="(mealsForDate, date) in mealsByDate" 
        :key="date" 
        class="date-section"
      >
        <!-- Date Header with Expand/Collapse -->
        <div class="date-header-wrapper" @click="toggleDateSection(date)">
          <h3 class="date-header">
            <span class="expand-icon" :class="{ 'expanded': expandedDates[date] }">▶</span>
            {{ formatDateHeader(date) }}
            <span class="meal-count">({{ mealsForDate.length }})</span>
          </h3>
        </div>
        
        <!-- Collapsible Meals for this date -->
        <div class="meals-list" v-if="expandedDates[date]">
          <div 
            v-for="meal in mealsForDate" 
            :key="meal.meal_id" 
            class="meal-row"
            :class="{ 'prepared': meal.status === 'prepared', 'expired': meal.status === 'expired' }"
          >
            <!-- Compact Meal Display -->
            <div class="meal-compact" @click="toggleMealDetails(meal.meal_id)">
              <!-- Meal Thumbnail -->
              <div class="meal-thumbnail">
                <img 
                  :src="meal.thumbnail_url" 
                  :alt="meal.meal_name"
                  @error="handleImageError"
                  loading="lazy"
                />
                <div class="status-badge" :class="meal.status">
                  {{ meal.status === 'prepared' ? '✓' : meal.status === 'expired' ? '⚠' : '📦' }}
                </div>
              </div>

              <!-- Meal Info -->
              <div class="meal-info">
                <h4 class="meal-name">{{ meal.meal_name }}</h4>
                <p class="meal-description">{{ meal.description }}</p>
                <div class="meal-meta" v-if="meal.prepared_at">
                  <span class="prepared-time">✅ Prepared: {{ formatDateTime(meal.prepared_at) }}</span>
                </div>
              </div>

              <!-- Meal Actions -->
              <div class="meal-actions">
                <div class="checkbox-container" v-if="meal.status !== 'expired'">
                  <button 
                    class="prepared-button"
                    :class="{ 'prepared': meal.status === 'prepared' }"
                    @click.stop="toggleMealStatus(meal)"
                    :disabled="updating === meal.meal_id"
                  >
                    <span class="button-icon">{{ meal.status === 'prepared' ? '✅' : '📦' }}</span>
                    <span class="button-text">
                      {{ meal.status === 'prepared' ? 'Mark Available' : 'Mark Prepared' }}
                    </span>
                  </button>
                </div>
                
                <div class="loading-indicator" v-if="updating === meal.meal_id">
                  <span class="spinner-small"></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { apiService } from '../services/api.js'

// Reactive data
const meals = ref([])
const loading = ref(false)
const error = ref(null)
const statusFilter = ref('')
const updating = ref(null)
const expandedDates = ref({})
const expandedMeals = ref({})

// Computed property to group meals by date
const mealsByDate = computed(() => {
  const grouped = {}
  meals.value.forEach(meal => {
    const date = meal.date_shipped
    if (!grouped[date]) {
      grouped[date] = []
    }
    grouped[date].push(meal)
  })
  
  // Sort dates descending (newest first) - ensure proper date comparison
  const sortedEntries = Object.entries(grouped).sort((a, b) => {
    // Parse dates as UTC to avoid timezone issues
    const dateA = new Date(a[0] + 'T00:00:00Z')
    const dateB = new Date(b[0] + 'T00:00:00Z')
    return dateB - dateA
  })
  
  // Auto-expand the first (most recent) date
  const result = Object.fromEntries(sortedEntries)
  if (sortedEntries.length > 0 && !Object.keys(expandedDates.value).length) {
    const firstDate = sortedEntries[0][0]
    expandedDates.value[firstDate] = true
  }
  
  return result
})

// Methods
const fetchMeals = async () => {
  try {
    loading.value = true
    error.value = null
    
    const params = {}
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    const data = await apiService.getMeals(params)
    meals.value = data
    
  } catch (err) {
    console.error('Failed to fetch meals:', err)
    error.value = 'Failed to load meals. Please try again.'
  } finally {
    loading.value = false
  }
}

const refreshMeals = () => {
  fetchMeals()
}

const toggleDateSection = (date) => {
  expandedDates.value[date] = !expandedDates.value[date]
}

const toggleMealDetails = (mealId) => {
  expandedMeals.value[mealId] = !expandedMeals.value[mealId]
}

const toggleMealStatus = async (meal) => {
  try {
    updating.value = meal.meal_id
    
    const newStatus = meal.status === 'prepared' ? 'available' : 'prepared'
    const updatedMeal = await apiService.updateMealStatus(meal.meal_id, { status: newStatus })
    
    // Update the local meal data
    const index = meals.value.findIndex(m => m.meal_id === meal.meal_id)
    if (index !== -1) {
      meals.value[index] = updatedMeal
    }
    
  } catch (err) {
    console.error('Failed to update meal status:', err)
    error.value = 'Failed to update meal status. Please try again.'
  } finally {
    updating.value = null
  }
}

const handleImageError = (event) => {
  // Replace broken images with placeholder
  event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg=='
}

const formatDate = (dateStr) => {
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  } catch {
    return dateStr
  }
}

const formatDateTime = (dateTimeStr) => {
  try {
    return new Date(dateTimeStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    })
  } catch {
    return dateTimeStr
  }
}

const formatDateHeader = (dateStr) => {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
  } catch {
    return dateStr
  }
}

// Lifecycle
onMounted(() => {
  fetchMeals()
})
</script>

<style scoped>
.meals-view {
  padding: 0.75rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.filter-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.status-filter {
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 0.375rem;
  background: var(--surface);
  color: var(--text-primary);
  font-size: 0.875rem;
}

.refresh-btn {
  padding: 0.375rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 0.375rem;
  background: var(--surface);
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--surface-hover);
  border-color: var(--primary);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 2rem 1rem;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 0.75rem;
}

.error-state p {
  color: var(--danger);
  margin-bottom: 0.75rem;
}

.retry-btn {
  padding: 0.5rem 1rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.empty-state {
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 0.75rem;
  opacity: 0.3;
}

.meals-by-date {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.date-section {
  background: var(--surface);
  border-radius: 0.5rem;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.date-header-wrapper {
  cursor: pointer;
  padding: 0.75rem;
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s ease;
}

.date-header-wrapper:hover {
  background: var(--surface-hover);
}

.date-header {
  font-family: var(--font-family-display);
  font-size: 1.125rem;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.expand-icon {
  font-size: 0.75rem;
  transition: transform 0.2s ease;
  color: var(--text-secondary);
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.meal-count {
  font-size: 0.875rem;
  font-weight: normal;
  color: var(--text-secondary);
  margin-left: auto;
}

.meals-list {
  display: flex;
  flex-direction: column;
}

.meal-row {
  border-bottom: 1px solid var(--border-color);
  transition: all 0.2s ease;
}

.meal-row:last-child {
  border-bottom: none;
}

.meal-row.prepared {
  background: rgba(34, 197, 94, 0.08);
  border-left: 3px solid var(--success);
}

.meal-row.expired {
  opacity: 0.7;
  background: rgba(251, 191, 36, 0.03);
}

.meal-compact {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.meal-compact:hover {
  background: var(--background);
}

.meal-thumbnail {
  position: relative;
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  border-radius: 0.375rem;
  overflow: hidden;
}

.meal-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status-badge {
  position: absolute;
  top: 0.125rem;
  right: 0.125rem;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(2px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.status-badge.available {
  color: var(--primary);
}

.status-badge.prepared {
  color: var(--success);
}

.status-badge.expired {
  color: var(--warning);
}

.meal-info {
  flex: 1;
  min-width: 0;
}

.meal-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.125rem 0;
  line-height: 1.3;
}

.meal-row.prepared .meal-name {
  color: var(--success);
}

.meal-description {
  color: var(--text-secondary);
  font-size: 0.8rem;
  line-height: 1.4;
  margin: 0 0 0.25rem 0;
}

.meal-meta {
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.prepared-time {
  color: var(--success);
  font-weight: 600;
  font-size: 0.75rem;
}

.meal-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.checkbox-container {
  display: flex;
  align-items: center;
}

.prepared-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 2px solid var(--border-color);
  border-radius: 0.375rem;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.8rem;
  font-weight: 500;
  user-select: none;
  min-width: 120px;
}

.prepared-button:hover {
  border-color: var(--primary);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}

.prepared-button:active {
  transform: translateY(0);
}

.prepared-button.prepared {
  background: var(--success-light);
  border-color: var(--success);
  color: var(--success-dark);
}

.prepared-button.prepared:hover {
  background: var(--success);
  color: white;
}

.prepared-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.button-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.button-text {
  white-space: nowrap;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5rem;
  height: 1.5rem;
}

.spinner-small {
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--border-color);
  border-top: 2px solid var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Tablet optimizations */
@media (max-width: 1024px) {
  .meals-view {
    padding: 0.5rem;
  }
  
  .date-header-wrapper {
    padding: 0.625rem;
  }
  
  .meal-compact {
    padding: 0.625rem;
    gap: 0.625rem;
  }
  
  .meal-thumbnail {
    width: 50px;
    height: 50px;
  }
  
  .meal-name {
    font-size: 0.875rem;
  }
  
  .meal-description {
    font-size: 0.75rem;
  }
}

/* Mobile optimizations */
@media (max-width: 768px) {
  .meals-view {
    padding: 0.375rem;
  }
  
  .header {
    justify-content: center;
  }
  
  .filter-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .date-section {
    border-radius: 0.375rem;
  }
  
  .date-header-wrapper {
    padding: 0.5rem;
  }
  
  .date-header {
    font-size: 1rem;
  }
  
  .meal-compact {
    padding: 0.5rem;
    gap: 0.5rem;
  }
  
  .meal-thumbnail {
    width: 45px;
    height: 45px;
  }
  
  .meal-name {
    font-size: 0.8rem;
  }
  
  .meal-description {
    font-size: 0.7rem;
  }
  
  .checkmark {
    width: 1.25rem;
    height: 1.25rem;
  }
}
</style>