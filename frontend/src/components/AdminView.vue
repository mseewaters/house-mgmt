<template>
  <div class="admin-layout">
    <!-- Tab Switcher -->
    <div class="admin-tabs">
      <button 
        class="tab-button" 
        :class="{ active: activeTab === 'family' }"
        @click="activeTab = 'family'"
      >
        Family Members
      </button>
      <button 
        class="tab-button" 
        :class="{ active: activeTab === 'tasks' }"
        @click="activeTab = 'tasks'"
      >
        Recurring Tasks
      </button>
    </div>

    <!-- Family Members Tab -->
    <div v-if="activeTab === 'family'" class="tab-content">
      <div class="content-header">
        <h2>Family Members</h2>
        <button class="add-button" @click="addFamilyMember">
          + Add Member
        </button>
      </div>
      
      <div class="data-table">
        <div class="table-header">
          <div class="col-name">Name</div>
          <div class="col-type">Type</div>
          <div class="col-pet-type">Pet Type</div>
          <div class="col-status">Status</div>
          <div class="col-actions">Actions</div>
        </div>
        
        <div class="table-body">
          <div 
            v-for="member in store.familyMembers" 
            :key="member.member_id"
            class="table-row"
          >
            <div class="col-name">
              <div class="member-info">
                <div class="person-initial" :class="getPersonClass(member.member_id)">
                  {{ member.name?.[0] || '?' }}
                </div>
                {{ member.name }}
              </div>
            </div>
            <div class="col-type">{{ member.member_type }}</div>
            <div class="col-pet-type">{{ member.pet_type || '-' }}</div>
            <div class="col-status">
              <span class="status-badge" :class="member.status?.toLowerCase()">
                {{ member.status }}
              </span>
            </div>
            <div class="col-actions">
              <button class="edit-btn" @click="editFamilyMember(member)">Edit</button>
              <button class="delete-btn" @click="deleteFamilyMember(member)">Delete</button>
            </div>
          </div>
        </div>
        
        <div v-if="store.familyMembers.length === 0" class="empty-table">
          <p>Add family members to get started</p>
        </div>
      </div>
    </div>

    <!-- Recurring Tasks Tab -->
    <div v-if="activeTab === 'tasks'" class="tab-content">
      <div class="content-header">
        <h2>Recurring Tasks</h2>
        <button class="add-button" @click="addRecurringTask">
          + Add Task
        </button>
      </div>
      
      <div class="data-table">
        <div class="table-header">
          <div class="col-task-name">Task Name</div>
          <div class="col-assigned">Assigned To</div>
          <div class="col-frequency">Frequency</div>
          <div class="col-due">Due</div>
          <div class="col-category">Category</div>
          <div class="col-status">Status</div>
          <div class="col-actions">Actions</div>
        </div>
        
        <div class="table-body">
          <div 
            v-for="task in store.recurringTasks" 
            :key="task.task_id"
            class="table-row"
          >
            <div class="col-task-name">{{ task.task_name }}</div>
            <div class="col-assigned">{{ getAssignedMemberName(task.assigned_to) }}</div>
            <div class="col-frequency">{{ task.frequency }}</div>
            <div class="col-due">{{ task.due }}</div>
            <div class="col-category">{{ task.category }}</div>
            <div class="col-status">
              <span class="status-badge" :class="task.status?.toLowerCase()">
                {{ task.status }}
              </span>
            </div>
            <div class="col-actions">
              <button class="edit-btn" @click="editRecurringTask(task)">Edit</button>
              <button class="delete-btn" @click="deleteRecurringTask(task)">Delete</button>
            </div>
          </div>
        </div>
        
        <div v-if="store.recurringTasks.length === 0" class="empty-table">
          <p>Add recurring tasks to get started</p>
        </div>
      </div>
    </div>

    <!-- Modal for Add/Edit Family Member -->
    <div v-if="showFamilyModal" class="modal-overlay" @click="closeFamilyModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>{{ editingFamilyMember ? 'Edit' : 'Add' }} Family Member</h3>
          <button class="close-btn" @click="closeFamilyModal">×</button>
        </div>
        
        <form @submit.prevent="saveFamilyMember" class="modal-form">
          <div class="form-group">
            <label>Name</label>
            <input 
              v-model="familyForm.name" 
              type="text" 
              required 
              maxlength="15"
              placeholder="Enter name"
            />
          </div>
          
          <div class="form-group">
            <label>Type</label>
            <select v-model="familyForm.member_type" required @change="onMemberTypeChange">
              <option value="">Select type</option>
              <option value="Person">Person</option>
              <option value="Pet">Pet</option>
            </select>
          </div>
          
          <div v-if="familyForm.member_type === 'Pet'" class="form-group">
            <label>Pet Type</label>
            <select v-model="familyForm.pet_type" required>
              <option value="">Select pet type</option>
              <option value="dog">Dog</option>
              <option value="cat">Cat</option>
              <option value="other">Other</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Status</label>
            <select v-model="familyForm.status" required>
              <option value="">Select status</option>
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="closeFamilyModal">Cancel</button>
            <button type="submit" class="save-btn" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal for Add/Edit Recurring Task -->
    <div v-if="showTaskModal" class="modal-overlay" @click="closeTaskModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3>{{ editingRecurringTask ? 'Edit' : 'Add' }} Recurring Task</h3>
          <button class="close-btn" @click="closeTaskModal">×</button>
        </div>
        
        <form @submit.prevent="saveRecurringTask" class="modal-form">
          <div class="form-group">
            <label>Task Name</label>
            <input 
              v-model="taskForm.task_name" 
              type="text" 
              required 
              maxlength="30"
              placeholder="Enter task name"
            />
          </div>
          
          <div class="form-group">
            <label>Assigned To</label>
            <select v-model="taskForm.assigned_to" required>
              <option value="">Select family member</option>
              <option 
                v-for="member in store.familyMembers.filter(m => m.status === 'Active')" 
                :key="member.member_id"
                :value="member.member_id"
              >
                {{ member.name }} ({{ member.member_type }})
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Frequency</label>
            <select v-model="taskForm.frequency" required @change="updateDueOptions">
              <option value="">Select frequency</option>
              <option value="Daily">Daily</option>
              <option value="Weekly">Weekly</option>
              <option value="Monthly">Monthly</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Due</label>
            <select v-model="taskForm.due" required>
              <option value="">Select due time</option>
              <option v-for="option in dueOptions" :key="option" :value="option">
                {{ option }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Overdue When</label>
            <select v-model="taskForm.overdue_when" required>
              <option value="">Select overdue timing</option>
              <option value="Immediate">Immediate</option>
              <option value="1 hour">1 hour</option>
              <option value="6 hours">6 hours</option>
              <option value="1 day">1 day</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Category</label>
            <select v-model="taskForm.category" required>
              <option value="">Select category</option>
              <option value="Medication">Medication</option>
              <option value="Feeding">Feeding</option>
              <option value="Health">Health</option>
              <option value="Hygiene">Hygiene</option>
              <option value="Cleaning">Cleaning</option>
              <option value="Other">Other</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>Status</label>
            <select v-model="taskForm.status" required>
              <option value="">Select status</option>
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button type="button" class="cancel-btn" @click="closeTaskModal">Cancel</button>
            <button type="submit" class="save-btn" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="closeDeleteModal">
      <div class="modal delete-modal" @click.stop>
        <div class="modal-header">
          <h3>Confirm Delete</h3>
          <button class="close-btn" @click="closeDeleteModal">×</button>
        </div>
        
        <div class="modal-body">
          <p>Are you sure you want to delete <strong>{{ deleteTarget?.name || deleteTarget?.task_name }}</strong>?</p>
          <p class="warning-text">This action cannot be undone.</p>
        </div>
        
        <div class="form-actions">
          <button type="button" class="cancel-btn" @click="closeDeleteModal">Cancel</button>
          <button type="button" class="delete-btn" @click="confirmDelete" :disabled="saving">
            {{ saving ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useHouseStore } from '../stores/house.js'

// Store
const store = useHouseStore()

// State
const activeTab = ref('family')
const saving = ref(false)

// Family Member Modal
const showFamilyModal = ref(false)
const editingFamilyMember = ref(null)
const familyForm = ref({
  name: '',
  member_type: '',
  pet_type: '',
  status: 'Active'
})

// Recurring Task Modal
const showTaskModal = ref(false)
const editingRecurringTask = ref(null)
const taskForm = ref({
  task_name: '',
  assigned_to: '',
  frequency: '',
  due: '',
  overdue_when: '',
  category: '',
  status: 'Active'
})

// Delete Modal
const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const deleteType = ref('') // 'family' or 'task'

// Computed
const dueOptions = computed(() => {
  switch (taskForm.value.frequency) {
    case 'Daily':
      return ['Morning', 'Afternoon', 'Evening']
    case 'Weekly':
      return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    case 'Monthly':
      return ['1st', '15th']
    default:
      return []
  }
})

// Helper functions
function getPersonClass(memberId) {
  const member = store.familyMembers.find(m => m.member_id === memberId)
  if (!member) return 'person-unknown'
  
  const colors = ['person-blue', 'person-green', 'person-purple', 'person-orange', 'person-pink']
  const index = (member.name?.charCodeAt(0) || 0) % colors.length
  return colors[index]
}

function getAssignedMemberName(memberId) {
  const member = store.familyMembers.find(m => m.member_id === memberId)
  return member?.name || 'Unknown'
}

function updateDueOptions() {
  taskForm.value.due = '' // Reset due when frequency changes
}

function onMemberTypeChange() {
  // Reset pet_type when switching member types
  if (familyForm.value.member_type === 'Person') {
    familyForm.value.pet_type = ''
  }
}

// Family Member Actions
function addFamilyMember() {
  editingFamilyMember.value = null
  familyForm.value = {
    name: '',
    member_type: '',
    pet_type: '',
    status: 'Active'
  }
  showFamilyModal.value = true
}

function editFamilyMember(member) {
  editingFamilyMember.value = member
  familyForm.value = { ...member }
  showFamilyModal.value = true
}

function deleteFamilyMember(member) {
  deleteTarget.value = member
  deleteType.value = 'family'
  showDeleteModal.value = true
}

function closeFamilyModal() {
  showFamilyModal.value = false
  editingFamilyMember.value = null
}

async function saveFamilyMember() {
  saving.value = true
  try {
    // Clean the form data - remove pet_type for Person members
    const submitData = { ...familyForm.value }
    
    if (submitData.member_type === 'Person') {
      delete submitData.pet_type // Remove pet_type completely for Person
    }
    
    console.log('💾 Saving family member:', submitData)
    
    if (editingFamilyMember.value) {
      await store.updateFamilyMember(editingFamilyMember.value.member_id, submitData)
      console.log('✅ Family member updated')
    } else {
      await store.createFamilyMember(submitData)
      console.log('✅ Family member created')
    }
    closeFamilyModal()
  } catch (error) {
    console.error('❌ Failed to save family member:', error)
    console.error('❌ Error details:', error.response?.data)
    // TODO: Show error message to user
  } finally {
    saving.value = false
  }
}

// Recurring Task Actions
function addRecurringTask() {
  editingRecurringTask.value = null
  taskForm.value = {
    task_name: '',
    assigned_to: '',
    frequency: '',
    due: '',
    overdue_when: '',
    category: '',
    status: 'Active'
  }
  showTaskModal.value = true
}

function editRecurringTask(task) {
  editingRecurringTask.value = task
  taskForm.value = { ...task }
  showTaskModal.value = true
}

function deleteRecurringTask(task) {
  deleteTarget.value = task
  deleteType.value = 'task'
  showDeleteModal.value = true
}

function closeTaskModal() {
  showTaskModal.value = false
  editingRecurringTask.value = null
}

async function saveRecurringTask() {
  saving.value = true
  try {
    if (editingRecurringTask.value) {
      await store.updateRecurringTask(editingRecurringTask.value.task_id, taskForm.value)
      console.log('✅ Recurring task updated')
    } else {
      await store.createRecurringTask(taskForm.value)
      console.log('✅ Recurring task created')
    }
    closeTaskModal()
  } catch (error) {
    console.error('❌ Failed to save recurring task:', error)
    // TODO: Show error message to user
  } finally {
    saving.value = false
  }
}

// Delete Actions
function closeDeleteModal() {
  showDeleteModal.value = false
  deleteTarget.value = null
  deleteType.value = ''
}

async function confirmDelete() {
  saving.value = true
  try {
    if (deleteType.value === 'family') {
      await store.deleteFamilyMember(deleteTarget.value.member_id)
      console.log('✅ Family member deleted')
    } else if (deleteType.value === 'task') {
      await store.deleteRecurringTask(deleteTarget.value.task_id)
      console.log('✅ Recurring task deleted')
    }
    closeDeleteModal()
  } catch (error) {
    console.error('❌ Failed to delete:', error)
    // TODO: Show error message to user
  } finally {
    saving.value = false
  }
}

// Load data on mount
onMounted(async () => {
  console.log('🔧 AdminView mounted')
  // Load data if not already loaded
  if (store.familyMembers.length === 0) {
    await store.loadFamilyMembers()
  }
  if (store.recurringTasks.length === 0) {
    await store.loadRecurringTasks()
  }
  console.log(`🔧 Admin ready - ${store.familyMembers.length} members, ${store.recurringTasks.length} tasks`)
})
</script>

<style scoped>
.admin-layout {
  height: 100%;
  padding: 20px;
  overflow-y: auto;
}

/* Tab Navigation */
.admin-tabs {
  display: flex;
  gap: 2px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
}

.tab-button {
  padding: 12px 24px;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  cursor: pointer;
  font-weight: 500;
  border-radius: 6px 6px 0 0;
  transition: all 0.15s ease;
}

.tab-button.active {
  background: white;
  color: #1f2937;
  border-bottom: 2px solid white;
  margin-bottom: -2px;
}

.tab-button:hover:not(.active) {
  background: #e5e7eb;
}

/* Content */
.tab-content {
  background: white;
  border-radius: 0 8px 8px 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.content-header h2 {
  margin: 0;
  color: #1f2937;
  font-size: 24px;
}

.add-button {
  background: var(--accent-red);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity 0.15s ease;
}

.add-button:hover {
  opacity: 0.9;
}

/* Data Table */
.data-table {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.table-header {
  display: grid;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
  padding: 12px 0;
}

.table-header.family-grid {
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
}

.table-header.tasks-grid {
  grid-template-columns: 2fr 1.5fr 1fr 1fr 1fr 1fr 1.5fr;
}

/* Family Members Grid */
.table-header:has(.col-name) {
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
}

.table-body .table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1.5fr;
  border-bottom: 1px solid #f3f4f6;
  padding: 12px 0;
  transition: background-color 0.15s ease;
}

/* Recurring Tasks Grid */
.table-header:has(.col-task-name) {
  grid-template-columns: 2fr 1.5fr 1fr 1fr 1fr 1fr 1.5fr;
}

.table-row:has(.col-task-name) {
  grid-template-columns: 2fr 1.5fr 1fr 1fr 1fr 1fr 1.5fr;
}

.table-row:hover {
  background: #f8f9fa;
}

.table-row:last-child {
  border-bottom: none;
}

.table-header > div,
.table-row > div {
  padding: 0 12px;
  display: flex;
  align-items: center;
  font-size: 14px;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.person-initial {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: white;
  flex-shrink: 0;
}

.person-blue { background: #3b82f6; }
.person-green { background: #10b981; }
.person-purple { background: #8b5cf6; }
.person-orange { background: #f59e0b; }
.person-pink { background: #ec4899; }
.person-unknown { background: #6b7280; }

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
}

.status-badge.active {
  color: #374151;
}

.status-badge.inactive {
  color: #6b7280;
}

.col-actions {
  gap: 8px;
}

.edit-btn, .delete-btn {
  padding: 4px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  background: white;
  color: #374151;
  transition: all 0.15s ease;
}

.edit-btn:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.delete-btn:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.empty-table {
  padding: 40px;
  text-align: center;
  color: #6b7280;
  font-style: italic;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f3f4f6;
}

.modal-form {
  padding: 20px;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.cancel-btn:hover {
  background: #f9fafb;
}

.save-btn {
  padding: 8px 16px;
  border: none;
  background: var(--accent-red);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.save-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.delete-modal .modal-body {
  text-align: center;
}

.warning-text {
  color: #dc2626;
  font-size: 14px;
  margin-top: 8px;
}

.delete-modal .delete-btn {
  background: #dc2626;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.delete-modal .delete-btn:hover:not(:disabled) {
  background: #b91c1c;
}

.delete-modal .delete-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>