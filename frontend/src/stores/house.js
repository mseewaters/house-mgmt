// src/stores/house.js
// Simple Pinia store for house management data

import { defineStore } from 'pinia'
import { apiService } from '../services/api.js'

export const useHouseStore = defineStore('house', {
  state: () => ({
    // Loading states
    loading: {
      family: false,
      tasks: false,
      weather: false
    },
    
    // Error states
    errors: {
      family: null,
      tasks: null,
      weather: null
    },
    
    // Data
    familyMembers: [],
    dailyTasks: [],
    recurringTasks: [],
    weather: null,
    
    // UI state
    activeTab: 'focus',
    currentDate: new Date().toISOString().split('T')[0], // YYYY-MM-DD
    
    // Time
    currentTime: '',
    currentDayName: '',
    currentDay: '',
    currentMonth: ''
  }),

  getters: {
    // Get tasks by member for display
    tasksByMember: (state) => {
      const memberMap = {}
      
      // Initialize all family members
      state.familyMembers.forEach(member => {
        memberMap[member.member_id] = {
          ...member,
          tasks: [],
          progress: { completed: 0, total: 0, percentage: 0 }
        }
      })
      
      // Add tasks to members
      state.dailyTasks.forEach(task => {
        if (memberMap[task.assigned_to]) {
          memberMap[task.assigned_to].tasks.push(task)
        }
      })
      
      // Calculate progress
      Object.values(memberMap).forEach(member => {
        const completed = member.tasks.filter(t => t.status === 'Completed').length
        const total = member.tasks.length
        member.progress = {
          completed,
          total,
          percentage: total > 0 ? Math.round((completed / total) * 100) : 0
        }
      })
      
      return memberMap
    },

    // Get focus items (due now or overdue)
    focusItems: (state) => {
      const now = new Date()
      const currentHour = now.getHours()
      
      return state.dailyTasks.filter(task => {
        if (task.status === 'Completed') return false
        
        // Simple logic: if it's past noon and task contains "morning", it's overdue
        // if it's past 6pm and task contains "evening", it's overdue
        const taskName = task.task_name.toLowerCase()
        const isOverdue = (
          (currentHour >= 12 && taskName.includes('morning')) ||
          (currentHour >= 18 && taskName.includes('evening')) ||
          (currentHour >= 14 && taskName.includes('lunch'))
        )
        
        const isDueNow = (
          (currentHour >= 11 && currentHour <= 13 && taskName.includes('lunch')) ||
          (currentHour >= 17 && currentHour <= 19 && taskName.includes('evening'))
        )
        
        return isOverdue || isDueNow
      }).map(task => {
        const member = state.familyMembers.find(m => m.member_id === task.assigned_to)
        return {
          ...task,
          member_name: member?.name || 'Unknown',
          member_avatar: member?.name?.[0] || '?',
          is_overdue: task.task_name.toLowerCase().includes('morning') && new Date().getHours() >= 12
        }
      })
    },

    // Separate people and pets
    people: (state) => state.familyMembers.filter(m => m.member_type === 'Person'),
    pets: (state) => state.familyMembers.filter(m => m.member_type === 'Pet')
  },

  actions: {
    // Initialize all data
    async initializeData() {
      console.log('🏠 Initializing house data...')
      await Promise.all([
        this.loadFamilyMembers(),
        this.loadDailyTasks(), // Load all tasks, no date filter
        this.loadWeather()
      ])
      this.updateDateTime()
    },

    // Load family members
    async loadFamilyMembers() {
      this.loading.family = true
      this.errors.family = null
      
      try {
        this.familyMembers = await apiService.getFamilyMembers()
        console.log(`✅ Loaded ${this.familyMembers.length} family members`)
      } catch (error) {
        this.errors.family = error.message
        console.error('❌ Failed to load family members:', error)
      } finally {
        this.loading.family = false
      }
    },

    // Load daily tasks
    async loadDailyTasks(date = null) {
      this.loading.tasks = true
      this.errors.tasks = null
      
      try {
        // If no date specified, get all tasks (don't pass date parameter)
        // If date specified, use that specific date
        this.dailyTasks = await apiService.getDailyTasks(date)
        console.log(`✅ Loaded ${this.dailyTasks.length} daily tasks${date ? ` for ${date}` : ' (all dates)'}`)
      } catch (error) {
        this.errors.tasks = error.message
        console.error('❌ Failed to load daily tasks:', error)
      } finally {
        this.loading.tasks = false
      }
    },

    // Load weather
    async loadWeather() {
      this.loading.weather = true
      this.errors.weather = null
      
      try {
        this.weather = await apiService.getWeather()
        console.log('✅ Weather loaded:', this.weather.current.temperature + '°F')
      } catch (error) {
        this.errors.weather = error.message
        console.error('❌ Failed to load weather:', error)
      } finally {
        this.loading.weather = false
      }
    },

    // Complete a task
    async completeTask(taskId) {
      try {
        const result = await apiService.completeTask(taskId)
        
        // Update local state
        const taskIndex = this.dailyTasks.findIndex(t => t.task_id === taskId)
        if (taskIndex !== -1) {
          this.dailyTasks[taskIndex] = result.task
        }
        
        console.log('✅ Task completed:', result.task.task_name)
        return result
      } catch (error) {
        console.error('❌ Failed to complete task:', error)
        throw error
      }
    },

    // Update current time
    updateDateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString([], {hour: 'numeric', minute:'2-digit'})
      this.currentDayName = now.toLocaleDateString([], {weekday: 'long'})
      this.currentDay = now.getDate().toString()
      this.currentMonth = now.toLocaleDateString([], {month: 'long'})
    },

    // Set active tab
    setActiveTab(tab) {
      this.activeTab = tab
      console.log('📱 Active tab:', tab)
    },

    // Change date for daily tasks
    async changeDate(newDate) {
      this.currentDate = newDate
      await this.loadDailyTasks(newDate)
    }
  }
})