// src/services/api.js
// Simple JavaScript API service - no TypeScript complexity

import axios from 'axios'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://klfhoqakm5.execute-api.us-east-1.amazonaws.com/Stage'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
})

// Simple request logging
api.interceptors.request.use(config => {
  console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)
  return config
})

api.interceptors.response.use(
  response => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`)
    return response
  },
  error => {
    console.error(`❌ API Error: ${error.response?.status || error.code} ${error.config?.url}`)
    return Promise.reject(error)
  }
)

// Export all API functions as a service object
export const apiService = {
  // Health check
  async checkHealth() {
    const response = await api.get('/api/health')
    return response.data
  },

  // Family Members - Using correct endpoints from your backend
  async getFamilyMembers() {
    const response = await api.get('/api/family-members')
    return response.data
  },

  async getFamilyMember(memberId) {
    const response = await api.get(`/api/family-members/${memberId}`)
    return response.data
  },

  async createFamilyMember(memberData) {
    const response = await api.post('/api/family-members', memberData)
    return response.data
  },

  async updateFamilyMember(memberId, memberData) {
    const response = await api.put(`/api/family-members/${memberId}`, memberData)
    return response.data
  },

  async deleteFamilyMember(memberId) {
    await api.delete(`/api/family-members/${memberId}`)
    return true
  },

  // Recurring Tasks
  async getRecurringTasks() {
    const response = await api.get('/api/recurring-tasks')
    return response.data
  },

  async getRecurringTask(taskId) {
    const response = await api.get(`/api/recurring-tasks/${taskId}`)
    return response.data
  },

  async createRecurringTask(taskData) {
    const response = await api.post('/api/recurring-tasks', taskData)
    return response.data
  },

  async updateRecurringTask(taskId, taskData) {
    const response = await api.put(`/api/recurring-tasks/${taskId}`, taskData)
    return response.data
  },

  async deleteRecurringTask(taskId) {
    await api.delete(`/api/recurring-tasks/${taskId}`)
    return true
  },

  // Daily Tasks
  async getDailyTasks(date = null) {
    const params = date ? { date } : {}
    const response = await api.get('/api/daily-tasks', { params })
    return response.data
  },

  async completeTask(taskId) {
    const response = await api.put(`/api/daily-tasks/${taskId}/complete`)
    return response.data
  },

  async undoTaskCompletion(taskId) {
    try {
      const response = await api.put(`/api/daily-tasks/${taskId}/uncomplete`)
      console.log('✅ Task uncompleted via backend API')
      return response.data
    } catch (error) {
      console.error('❌ API Error - Undo task completion:', error)
      throw error
    }
  },

  // Weather
  async getWeather() {
    const response = await api.get('/api/weather')
    return response.data
  },

  // Meals
  async getMeals(params = {}) {
    const response = await api.get('/api/meals', { params })
    return response.data
  },

  async getMeal(mealId) {
    const response = await api.get(`/api/meals/${mealId}`)
    return response.data
  },

  async updateMealStatus(mealId, statusUpdate) {
    const response = await api.put(`/api/meals/${mealId}/status`, statusUpdate)
    return response.data
  },

  async prepareMeal(mealId) {
    const response = await api.put(`/api/meals/${mealId}/prepare`)
    return response.data
  },

  async unprepareMeal(mealId) {
    const response = await api.put(`/api/meals/${mealId}/unprepare`)
    return response.data
  },

  async deleteMeal(mealId) {
    await api.delete(`/api/meals/${mealId}`)
    return true
  },

  // Test connectivity
  async testApiConnectivity() {
    try {
      const response = await api.get('/api/health')
      console.log('✅ API connectivity test passed:', response.data)
      return response.data
    } catch (error) {
      console.error('❌ API connectivity test failed:', error)
      throw error
    }
  }
}

// Simple test functions for browser console
export const apiTest = {
  async runAll() {
    console.log('🧪 Testing all API endpoints...')
    
    try {
      const health = await apiService.checkHealth()
      console.log('✅ Health:', health)
      
      const family = await apiService.getFamilyMembers()
      console.log('✅ Family Members:', family.length, 'found')
      
      const recurringTasks = await apiService.getRecurringTasks()
      console.log('✅ Recurring Tasks:', recurringTasks.length, 'found')
      
      const tasks = await apiService.getDailyTasks()
      console.log('✅ Daily Tasks:', tasks.length, 'found')
      
      const weather = await apiService.getWeather()
      console.log('✅ Weather:', weather.current.temperature + '°F')
      
      console.log('🎉 All tests passed!')
      return true
      
    } catch (error) {
      console.error('❌ Test failed:', error.message)
      return false
    }
  },

  async health() {
    return await apiService.checkHealth()
  },

  async family() {
    return await apiService.getFamilyMembers()
  },

  async recurringTasks() {
    return await apiService.getRecurringTasks()
  },

  async tasks() {
    return await apiService.getDailyTasks()
  },

  async weather() {
    return await apiService.getWeather()
  }
}

// Attach to window for easy testing
if (typeof window !== 'undefined') {
  window.apiTest = apiTest
  window.api = apiService
  console.log('🔧 API utilities: window.apiTest.runAll() or window.api.getFamilyMembers()')
}

export default apiService