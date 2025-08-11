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

// API Functions
export const apiService = {
  // Health check
  async checkHealth() {
    const response = await api.get('/api/health')
    return response.data
  },

  // Family Members
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

  // Recurring Tasks
  async getRecurringTasks() {
    const response = await api.get('/api/recurring-tasks')
    return response.data
  },

  async createRecurringTask(taskData) {
    const response = await api.post('/api/recurring-tasks', taskData)
    return response.data
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

  // Weather
  async getWeather() {
    const response = await api.get('/api/weather')
    return response.data
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