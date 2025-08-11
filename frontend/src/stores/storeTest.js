// src/stores/storeTest.js
// Test utility for Pinia store

import { useHouseStore } from './house.js'

export const storeTest = {
  async testStore() {
    console.log('🏪 Testing Pinia Store...')
    
    // Get store instance
    const store = useHouseStore()
    
    try {
      // Test initialization
      console.log('1️⃣ Initializing store data...')
      await store.initializeData()
      
      // Check data
      console.log('2️⃣ Checking loaded data:')
      console.log(`   Family Members: ${store.familyMembers.length}`)
      console.log(`   Daily Tasks: ${store.dailyTasks.length}`)
      console.log(`   Weather: ${store.weather?.current?.temperature}°F`)
      
      // Test getters
      console.log('3️⃣ Testing getters:')
      console.log(`   People: ${store.people.length}`)
      console.log(`   Pets: ${store.pets.length}`)
      console.log(`   Focus Items: ${store.focusItems.length}`)
      
      // Test tasks by member
      const tasksByMember = store.tasksByMember
      console.log(`   Tasks organized by ${Object.keys(tasksByMember).length} members`)
      
      // Show sample member data
      const firstMember = Object.values(tasksByMember)[0]
      if (firstMember) {
        console.log(`   Sample: ${firstMember.name} has ${firstMember.tasks.length} tasks`)
      }
      
      console.log('🎉 Store test completed successfully!')
      return store
      
    } catch (error) {
      console.error('❌ Store test failed:', error)
      throw error
    }
  },

  // Quick access to store
  getStore() {
    return useHouseStore()
  }
}

// Attach to window for easy testing
if (typeof window !== 'undefined') {
  window.storeTest = storeTest
  console.log('🏪 Store test: window.storeTest.testStore()')
}