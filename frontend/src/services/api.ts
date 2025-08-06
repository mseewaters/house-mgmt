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

export default api