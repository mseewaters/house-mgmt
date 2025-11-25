// Simple API service without interceptor logging issues
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
})

// Add auth token to requests (without logging)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Test function to verify connectivity
export async function testApiConnectivity() {
  try {
    const response = await api.get('/api/health')
    console.log('✅ API connectivity test passed:', response.data)
    return response.data
  } catch (error) {
    console.error('❌ API connectivity test failed:', error)
    throw error
  }
}

// Meal API functions
export async function fetchMealsAPI(params = {}) {
  try {
    const response = await api.get('/api/meals', { params })
    return response.data
  } catch (error) {
    console.error('Failed to fetch meals:', error)
    throw error
  }
}

export async function getMealByIdAPI(mealId: string) {
  try {
    const response = await api.get(`/api/meals/${mealId}`)
    return response.data
  } catch (error) {
    console.error(`Failed to fetch meal ${mealId}:`, error)
    throw error
  }
}

export async function updateMealStatusAPI(mealId: string, statusUpdate: { status: string }) {
  try {
    const response = await api.put(`/api/meals/${mealId}/status`, statusUpdate)
    return response.data
  } catch (error) {
    console.error(`Failed to update meal ${mealId} status:`, error)
    throw error
  }
}

export async function prepareMealAPI(mealId: string) {
  try {
    const response = await api.put(`/api/meals/${mealId}/prepare`)
    return response.data
  } catch (error) {
    console.error(`Failed to prepare meal ${mealId}:`, error)
    throw error
  }
}

export async function unprepareMealAPI(mealId: string) {
  try {
    const response = await api.put(`/api/meals/${mealId}/unprepare`)
    return response.data
  } catch (error) {
    console.error(`Failed to unprepare meal ${mealId}:`, error)
    throw error
  }
}

export default api