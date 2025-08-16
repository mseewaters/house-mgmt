// src/services/timingService.js
// Business logic for task timing and status management

export class TimingService {
  constructor() {
    this.now = new Date()
    this.currentHour = this.now.getHours()
    this.currentMinutes = this.now.getMinutes()
  }

  /**
   * Determine if a task is overdue based on due_time and current time
   * @param {Object} task - Daily task object
   * @returns {boolean} - True if task is overdue
   */
  isTaskOverdue(task) {
    if (task.status === 'Completed') return false
    
    const dueTime = task.due_time || task.due || 'Anytime'
    const taskName = task.task_name?.toLowerCase() || ''
    
    // Parse due time patterns
    if (dueTime.toLowerCase().includes('morning') || taskName.includes('morning')) {
      // Morning tasks overdue after 12:00 PM
      return this.currentHour >= 12
    }
    
    if (dueTime.toLowerCase().includes('lunch') || taskName.includes('lunch')) {
      // Lunch tasks overdue after 2:00 PM
      return this.currentHour >= 14
    }
    
    if (dueTime.toLowerCase().includes('afternoon') || taskName.includes('afternoon')) {
      // Afternoon tasks overdue after 6:00 PM
      return this.currentHour >= 18
    }
    
    if (dueTime.toLowerCase().includes('evening') || taskName.includes('evening')) {
      // Evening tasks overdue after 11:00 PM
      return this.currentHour >= 23
    }
    
    if (dueTime.toLowerCase().includes('night') || taskName.includes('night')) {
      // Night tasks overdue after 2:00 AM next day
      return this.currentHour >= 2 && this.currentHour < 6
    }
    
    // Time-specific patterns (e.g., "9:00 AM", "3:30 PM")
    const timeMatch = dueTime.match(/(\d{1,2}):?(\d{0,2})\s*(AM|PM)/i)
    if (timeMatch) {
      const [, hours, minutes = '0', period] = timeMatch
      let dueHour = parseInt(hours)
      const dueMinutes = parseInt(minutes)
      
      if (period.toUpperCase() === 'PM' && dueHour !== 12) {
        dueHour += 12
      } else if (period.toUpperCase() === 'AM' && dueHour === 12) {
        dueHour = 0
      }
      
      const dueTimeInMinutes = dueHour * 60 + dueMinutes
      const currentTimeInMinutes = this.currentHour * 60 + this.currentMinutes
      
      // Task is overdue if current time is 1 hour past due time
      return currentTimeInMinutes > (dueTimeInMinutes + 60)
    }
    
    // Default: no specific timing rules
    return false
  }

  /**
   * Determine if a task is due now (within the current time window)
   * @param {Object} task - Daily task object
   * @returns {boolean} - True if task should be highlighted as due now
   */
  isTaskDueNow(task) {
    if (task.status === 'Completed') return false
    
    const dueTime = task.due_time || task.due || 'Anytime'
    const taskName = task.task_name?.toLowerCase() || ''
    
    // Morning window: 6:00 AM - 11:59 AM
    if (dueTime.toLowerCase().includes('morning') || taskName.includes('morning')) {
      return this.currentHour >= 6 && this.currentHour < 12
    }
    
    // Lunch window: 11:00 AM - 1:59 PM
    if (dueTime.toLowerCase().includes('lunch') || taskName.includes('lunch')) {
      return this.currentHour >= 11 && this.currentHour < 14
    }
    
    // Afternoon window: 12:00 PM - 5:59 PM
    if (dueTime.toLowerCase().includes('afternoon') || taskName.includes('afternoon')) {
      return this.currentHour >= 12 && this.currentHour < 18
    }
    
    // Evening window: 5:00 PM - 10:59 PM
    if (dueTime.toLowerCase().includes('evening') || taskName.includes('evening')) {
      return this.currentHour >= 17 && this.currentHour < 23
    }
    
    // Night window: 9:00 PM - 1:59 AM
    if (dueTime.toLowerCase().includes('night') || taskName.includes('night')) {
      return this.currentHour >= 21 || this.currentHour < 2
    }
    
    return false
  }

  /**
   * Determine if a task is specifically for the next time period
   * @param {Object} task - Daily task object
   * @returns {boolean} - True if task is scheduled for the next period
   */
  isTaskForNextPeriod(task) {
    if (task.status === 'Completed') return false
    
    const dueTime = task.due_time || task.due || 'Anytime'
    const taskName = task.task_name?.toLowerCase() || ''
    const nextPeriod = this.getNextPeriodType()

    // DEBUG: Log what we're checking
    console.log(`🔍 Task: "${task.task_name}", Due: "${dueTime}", Next period: "${nextPeriod}", Current hour: ${this.currentHour}`)

    
    // Check if task matches the next period (case-insensitive)
    let matches = false
    if (nextPeriod === 'afternoon') {
      matches = dueTime.toLowerCase().includes('afternoon') || taskName.includes('afternoon')
    } else if (nextPeriod === 'evening') {
      matches = dueTime.toLowerCase().includes('evening') || taskName.includes('evening')
    } else if (nextPeriod === 'morning') {
      matches = dueTime.toLowerCase().includes('morning') || taskName.includes('morning')
    }
    
    console.log(`  ✅ Task "${task.task_name}" matches next period (${nextPeriod}): ${matches}`)
    return matches
  }

  /**
   * Get the type of the next time period (for filtering tasks)
   * @returns {string} - 'morning', 'afternoon', 'evening', or 'night'
   */
  getNextPeriodType() {
    const hour = this.currentHour
    // Morning period = 12am-11:59am (0-11)
    // Afternoon period = 12pm-5:59pm (12-17) 
    // Evening period = 6pm-11:59pm (18-23)
    
    if (hour >= 0 && hour <= 11) return 'afternoon'    // Morning -> next is afternoon
    if (hour >= 12 && hour <= 17) return 'evening'     // Afternoon -> next is evening  
    if (hour >= 18 && hour <= 23) return 'morning'     // Evening -> next is morning (tomorrow)
    
    return 'afternoon' // fallback
  }

  /**
   * Get display priority for task ordering
   * @param {Object} task - Daily task object
   * @returns {number} - Priority score (higher = more important)
   */
  getTaskPriority(task) {
    if (task.status === 'Completed') return 0
    
    if (this.isTaskOverdue(task)) return 100 // Highest priority
    if (this.isTaskDueNow(task)) return 50  // Medium priority
    return 10 // Normal priority
  }

  /**
   * Format time for display
   * @param {string} dueTime - Due time string
   * @returns {string} - Formatted display time
   */
  formatDisplayTime(dueTime) {
    if (!dueTime) return 'Anytime'
    
    // Clean up common patterns
    return dueTime
      .replace(/^(Morning|Lunch|Afternoon|Evening|Night)$/i, '$1')
      .replace(/(\d{1,2}):?(\d{0,2})\s*(AM|PM)/i, (match, h, m, period) => {
        const minutes = m || '00'
        return `${h}:${minutes.padStart(2, '0')} ${period.toUpperCase()}`
      })
  }

  /**
   * Get overdue message for display
   * @param {Object} task - Daily task object
   * @returns {string} - Overdue display message
   */
  getOverdueMessage(task) {
    const dueTime = task.due_time || task.due || 'Anytime'
    
    if (dueTime.toLowerCase().includes('morning')) {
      const hoursLate = Math.max(0, this.currentHour - 12)
      return hoursLate > 0 ? `${hoursLate}h late` : 'Due now'
    }
    
    // Add more specific overdue calculations as needed
    return 'Overdue'
  }
}

// Export singleton instance
export const timingService = new TimingService()