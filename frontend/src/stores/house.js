// src/stores/house.js
// Simple Pinia store for house management data

import { defineStore } from 'pinia'
import { apiService } from '../services/api.js'
import { timingService } from '../services/timingService.js'

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
  // Enhanced focus items with proper timing logic
  focusItems: (state) => {
    return state.dailyTasks
      .filter(task => task.status !== 'Completed')
      .map(task => {
        const member = state.familyMembers.find(m => m.member_id === task.assigned_to)
        return {
          ...task,
          member_name: member?.name || 'Unknown',
          member_avatar: member?.name?.[0] || '?',
          is_overdue: timingService.isTaskOverdue(task),
          is_due_now: timingService.isTaskDueNow(task),
          priority: timingService.getTaskPriority(task),
          display_time: timingService.formatDisplayTime(task.due_time || task.due),
          overdue_message: timingService.isTaskOverdue(task) ? timingService.getOverdueMessage(task) : null
        }
      })
      .sort((a, b) => b.priority - a.priority) // Sort by priority (overdue first)
  },

  // Separate overdue tasks
  overdueTasks: (state) => {
    return state.dailyTasks
      .filter(task => task.status !== 'Completed')
      .map(task => {
        const member = state.familyMembers.find(m => m.member_id === task.assigned_to)
        return {
          ...task,
          member_name: member?.name || 'Unknown',
          member_avatar: member?.name?.[0] || '?',
          is_overdue: timingService.isTaskOverdue(task),
          display_time: timingService.formatDisplayTime(task.due_time || task.due),
          overdue_message: timingService.getOverdueMessage(task)
        }
      })
      .filter(task => task.is_overdue)
      .sort((a, b) => {
        // Sort by member name, then by task name
        if (a.member_name !== b.member_name) {
          return a.member_name.localeCompare(b.member_name)
        }
        return a.task_name.localeCompare(b.task_name)
      })
  },

  // Current period tasks (due now, not overdue)
  currentPeriodTasks: (state) => {
    return state.dailyTasks
      .filter(task => task.status !== 'Completed')
      .map(task => {
        const member = state.familyMembers.find(m => m.member_id === task.assigned_to)
        return {
          ...task,
          member_name: member?.name || 'Unknown',
          member_avatar: member?.name?.[0] || '?',
          is_overdue: timingService.isTaskOverdue(task),
          is_due_now: timingService.isTaskDueNow(task),
          display_time: timingService.formatDisplayTime(task.due_time || task.due)
        }
      })
      .filter(task => !task.is_overdue && (task.is_due_now || task.status === 'Pending'))
      .sort((a, b) => {
        // Sort due now first, then by member name
        if (a.is_due_now && !b.is_due_now) return -1
        if (!a.is_due_now && b.is_due_now) return 1
        if (a.member_name !== b.member_name) {
          return a.member_name.localeCompare(b.member_name)
        }
        return a.task_name.localeCompare(b.task_name)
      })
  },

  // Completed tasks for today
  completedTasks: (state) => {
    return state.dailyTasks
      .filter(task => task.status === 'Completed')
      .map(task => {
        const member = state.familyMembers.find(m => m.member_id === task.assigned_to)
        return {
          ...task,
          member_name: member?.name || 'Unknown',
          member_avatar: member?.name?.[0] || '?',
          completed_display_time: task.completed_at ? 
            new Date(task.completed_at).toLocaleTimeString([], {hour: 'numeric', minute:'2-digit'}) : 
            'Unknown time'
        }
      })
      .sort((a, b) => {
        // Sort by completion time, most recent first
        if (!a.completed_at) return 1
        if (!b.completed_at) return -1
        return new Date(b.completed_at) - new Date(a.completed_at)
      })
  },

  // Get current period name for display
  currentPeriodName: () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'This Morning'
    if (hour < 17) return 'This Afternoon' 
    if (hour < 21) return 'This Evening'
    return 'Tonight'
  },

  // Get next period name
  nextPeriodName: () => {
    const hour = new Date().getHours()
    if (hour < 11) return 'This Afternoon'
    if (hour < 16) return 'This Evening'
    if (hour < 20) return 'Tonight'
    return 'Tomorrow Morning'
  },

  // Enhanced tasks by member with timing info
  tasksByMember: (state) => {
    const memberMap = {}
    
    // Initialize all family members
    state.familyMembers.forEach(member => {
      memberMap[member.member_id] = {
        ...member,
        tasks: [],
        progress: { completed: 0, total: 0, percentage: 0, overdue: 0 }
      }
    })
    
    // Add tasks to members with timing info
    state.dailyTasks.forEach(task => {
      if (memberMap[task.assigned_to]) {
        const enhancedTask = {
          ...task,
          is_overdue: timingService.isTaskOverdue(task),
          is_due_now: timingService.isTaskDueNow(task),
          display_time: timingService.formatDisplayTime(task.due_time || task.due)
        }
        memberMap[task.assigned_to].tasks.push(enhancedTask)
      }
    })
    
    // Calculate enhanced progress
    Object.values(memberMap).forEach(member => {
      const completed = member.tasks.filter(t => t.status === 'Completed').length
      const overdue = member.tasks.filter(t => t.is_overdue && t.status !== 'Completed').length
      const total = member.tasks.length
      member.progress = {
        completed,
        total,
        overdue,
        percentage: total > 0 ? Math.round((completed / total) * 100) : 0
      }
    })
    
    return memberMap
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
    },

    // Family Member CRUD
    async createFamilyMember(memberData) {
      try {
        const newMember = await apiService.createFamilyMember(memberData)
        this.familyMembers.push(newMember)
        console.log('✅ Family member created:', newMember.name)
        return newMember
      } catch (error) {
        console.error('❌ Failed to create family member:', error)
        throw error
      }
    },

    async updateFamilyMember(memberId, memberData) {
      try {
        const updatedMember = await apiService.updateFamilyMember(memberId, memberData)
        const index = this.familyMembers.findIndex(m => m.member_id === memberId)
        if (index !== -1) {
          this.familyMembers[index] = updatedMember
        }
        console.log('✅ Family member updated:', updatedMember.name)
        return updatedMember
      } catch (error) {
        console.error('❌ Failed to update family member:', error)
        throw error
      }
    },

    async deleteFamilyMember(memberId) {
      try {
        await apiService.deleteFamilyMember(memberId)
        const index = this.familyMembers.findIndex(m => m.member_id === memberId)
        if (index !== -1) {
          const deletedMember = this.familyMembers.splice(index, 1)[0]
          console.log('✅ Family member deleted:', deletedMember.name)
        }
      } catch (error) {
        console.error('❌ Failed to delete family member:', error)
        throw error
      }
    },

    // Recurring Task CRUD
    async loadRecurringTasks() {
      this.loading.tasks = true
      this.errors.tasks = null
      
      try {
        this.recurringTasks = await apiService.getRecurringTasks()
        console.log(`✅ Loaded ${this.recurringTasks.length} recurring tasks`)
      } catch (error) {
        this.errors.tasks = error.message
        console.error('❌ Failed to load recurring tasks:', error)
      } finally {
        this.loading.tasks = false
      }
    },

    async createRecurringTask(taskData) {
      try {
        const newTask = await apiService.createRecurringTask(taskData)
        this.recurringTasks.push(newTask)
        console.log('✅ Recurring task created:', newTask.task_name)
        return newTask
      } catch (error) {
        console.error('❌ Failed to create recurring task:', error)
        throw error
      }
    },

    async updateRecurringTask(taskId, taskData) {
      try {
        const updatedTask = await apiService.updateRecurringTask(taskId, taskData)
        const index = this.recurringTasks.findIndex(t => t.task_id === taskId)
        if (index !== -1) {
          this.recurringTasks[index] = updatedTask
        }
        console.log('✅ Recurring task updated:', updatedTask.task_name)
        return updatedTask
      } catch (error) {
        console.error('❌ Failed to update recurring task:', error)
        throw error
      }
    },

    async deleteRecurringTask(taskId) {
      try {
        await apiService.deleteRecurringTask(taskId)
        const index = this.recurringTasks.findIndex(t => t.task_id === taskId)
        if (index !== -1) {
          const deletedTask = this.recurringTasks.splice(index, 1)[0]
          console.log('✅ Recurring task deleted:', deletedTask.task_name)
        }
      } catch (error) {
        console.error('❌ Failed to delete recurring task:', error)
        throw error
      }
    },

  }
})