# Prototypes & Wireframes: house-mgmt

## Design System Foundation

### Color Palette
```css
/* Background Colors */
  --bg-body: #e5e5e5;
  --bg-container: #ffffff;
  --bg-sidebar: #343c40;
  --bg-tab-nav: #495255;
  --bg-tab-active: #d25151;
  --bg-weather-section: #495255;

/* Text Colors */  
  --text-white: #f2f2f2;
  --text-white-muted: rgba(255,255,255,0.8);
  --text-white-light: rgba(255,255,255,0.7);
  --text-primary: #2b3134;     /* Dark steel grey (main text, great on light backgrounds) */
  --text-secondary: #5b6368;   /* Medium muted steel grey (subtext, hints of blue undertone) */
  --text-muted: #9ba2a7;       /* Muted cool grey (disabled, less prominent text) */

/* Card Accent Colors */
  --accent-red: #C40C0C;
  --accent-success: #95A985;
  --accent-gradient: linear-gradient(135deg, #C40C0C, #d25151);
  --accent-card-top: linear-gradient(90deg, #B85450, #95A985, #9CAAB6);

/* Border Colors */
  --border-light: #e8eaed;
  --border-divider: #f0f0f0;
  --border-weather: rgba(255,255,255,0.2);

/* Task Colors */  
  --task-bg-completed: #f0f8f4;
  --task-bg-overdue: #fef2f2;
  --task-border-completed: #95A985;
  --task-border-overdue: #fecaca;
```

### Typography Scale
```css
/* ===== TYPOGRAPHY ===== */
  --font-family-primary: 'Inter', system-ui, sans-serif;
  --font-family-display: 'Nunito Sans', system-ui, sans-serif;
  
  --font-size-xs: 0.75rem;    /* 12px */
  --font-size-sm: 0.875rem;   /* 14px */
  --font-size-base: 1rem;     /* 16px */
  --font-size-lg: 1.125rem;   /* 18px */
  --font-size-xl: 1.25rem;    /* 20px */
  --font-size-2xl: 1.5rem;    /* 24px */
  --font-size-3xl: 1.875rem;  /* 30px */
  --font-size-4xl: 2.25rem;   /* 36px */
  --font-size-5xl: 2.5rem;    /* 40px */

/* ===== SPACING ===== */
  --spacing-xs: 0.25rem;   /* 4px */
  --spacing-sm: 0.5rem;    /* 8px */
  --spacing-md: 0.75rem;   /* 12px */
  --spacing-lg: 1rem;      /* 16px */
  --spacing-xl: 1.5rem;    /* 24px */
  --spacing-2xl: 2rem;     /* 32px */
  --spacing-3xl: 3rem;     /* 48px */

/* ===== BORDER RADIUS ===== */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  --radius-xl: 1.5rem;
  --radius-full: 9999px;

/* ===== COMPONENT STANDARDS ===== */
  --touch-target: 44px;
  --max-content-width: 24rem;
  --border-width: 1px;
  
/* ===== TABLET LAYOUT ===== */
  --container-width: 1280px;
  --container-height: 800px;
  --sidebar-width: 220px;
  --progress-ring-size: 50px;
  --avatar-size: 40px;
  --forecast-icon-size: 60px;

/* ===== SHADOWS ===== */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-focus: 0 0 0 2px var(--yellow-safety);

/* ===== CSS RESET ===== */
  *,
  *::before,
  *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

/* ===== BASE STYLES ===== */
  html {
    font-size: 16px;
  }

  body {
    min-height: 100vh;
    font-family: var(--font-family-primary);
    font-size: var(--font-size-base);
    line-height: 1.5;
    color: var(--text-primary);
    background-color: var(--bg-body);
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    display: flex;
  }

/* ===== UTILITY CLASSES ===== */
  .text-center { text-align: center; }
  .text-left { text-align: left; }
  .text-right { text-align: right; }

  .mt-4 { margin-top: var(--spacing-lg); }
  .mb-4 { margin-bottom: var(--spacing-lg); }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

```

## Page Wireframes

### 1. Daily Activities Tracking Interface
```
┌─ Sidebar ─┐ ┌─ Top Navigation ──────────────────────────────────────────────┐
│           │ │ [Activities] [Meals] [Add Tasks]                              │
│ Saturday  │ ├───────────────────────────────────────────────────────────────┤
│ August 2  │ │                                                               │
│           │ │ ┌─ PEOPLE ROW ──────────────────────────────────────────────┐ │
│ 9:39 AM   │ │ │                                                           │ │
│           │ │ │ ┌─ Bob Card ────────────┐  ┌─ Marjorie Card ──────────────┐ │ │
│ ☁️        │ │ │ │ [B] Bob        [1/2]  │  │ [M] Marjorie         [1/2]  │ │ │
│ Few       │ │ │ │ ┌───────────────────┐ │  │ ┌─────────────────────────┐ │ │ │
│ Clouds    │ │ │ │ │ ○ Evening pills   │ │  │ │ ○ Lunch vitamins        │ │ │ │
│           │ │ │ │ │   Overdue         │ │  │ │   Overdue               │ │ │ │
│ High: 77°F│ │ │ │ │ ● Morning pills   │ │  │ │ ● Morning pill         │ │ │ │
│ Low: 60°F │ │ │ │ │   Completed       │ │  │ │   Completed             │ │ │ │
│           │ │ │ │ │ [scroll...]       │ │  │ │ [scroll...]             │ │ │ │
│ Humidity: │ │ │ │ └───────────────────┘ │  │ └─────────────────────────┘ │ │ │
│ 56%       │ │ │ └───────────────────────┘  └─────────────────────────────┘ │ │
│ Wind:     │ │ └───────────────────────────────────────────────────────────┘ │
│ 7 mph     │ │                                                               │
│           │ │ ┌─ PETS ROW ────────────────────────────────────────────────┐ │
│ ☀️ Tmrw   │ │ │                                                           │ │
│ H:82 L:60 │ │ │ ┌─ Layla ──────┐ ┌─ Lucy ───────┐ ┌─ Sadie ─────────────┐ │ │
│ ☁️ Mon    │ │ │ │ [L] Layla     │ │ [L] Lucy     │ │ [S] Sadie           │ │ │
│ H:86 L:61 │ │ │ │      [0/2]    │ │     [0/2]    │ │       [0/1]         │ │ │
│ ☁️ Tue    │ │ │ │ ┌───────────┐ │ │ ┌──────────┐ │ │ ┌─────────────────┐ │ │ │
│ H:84 L:64 │ │ │ │ │○ Before   │ │ │ │○ Before  │ │ │ │ ○ Slurp         │ │ │ │
│ ☁️ Wed    │ │ │ │ │  bed      │ │ │ │  bed     │ │ │ │   Overdue       │ │ │ │
│ H:85 L:65 │ │ │ │ │  Overdue  │ │ │ │  Overdue │ │ │ │                 │ │ │ │
│ ⚡ Thu    │ │ │ │ │○ Dinner   │ │ │ │○ Dinner  │ │ │ │                 │ │ │ │
│ H:82 L:66 │ │ │ │ │  Due daily│ │ │ │  Overdue │ │ │ │                 │ │ │ │
│           │ │ │ │ └───────────┘ │ │ └──────────┘ │ │ └─────────────────┘ │ │ │
│           │ │ │ └───────────────┘ └──────────────┘ └─────────────────────┘ │ │
│           │ │ └───────────────────────────────────────────────────────────┘ │
│           │ └───────────────────────────────────────────────────────────────┘
└───────────┘

Components:
- Sidebar: Weather widget with date/time and forecast
- Navigation: Tab-based navigation (Activities highlighted)
- Person Cards: Family members with progress dial and scrollable task list
- Pet Cards: Similar structure for pets
- Task Items: Radio buttons for completion, status labels
- Progress Indicators: Fraction display (completed/total)
```

Reference: [tracking.png](./tracking.png)

### 2. Admin Dashboard - Family & Tasks Management
```
┌─ Sidebar ─┐ ┌─ Top Navigation ──────────────────────────────────────────────┐
│           │ │ [Activities] [Meals] [Add Tasks]                              │
│ Saturday  │ ├───────────────────────────────────────────────────────────────┤
│ August 2  │ │ Manage Family & Tasks                                         │
│           │ │                                                               │
│ 9:41 AM   │ │ ┌─ Tab Selection ──────────────────────────────────────────┐ │
│           │ │ │ [Family Members] [Recurring Tasks]                       │ │
│ ☁️        │ │ └──────────────────────────────────────────────────────────┘ │
│ Few       │ │                                                               │
│ Clouds    │ │ [Add Family Member]                                           │
│           │ │                                                               │
│ High: 77°F│ │ ┌─ Family Members Table ───────────────────────────────────┐ │
│ Low: 60°F │ │ │ Name     │ Type   │ Pet Type │ Status │ Actions          │ │
│           │ │ ├──────────┼────────┼──────────┼────────┼──────────────────┤ │
│ Humidity: │ │ │ Bob      │ Person │ -        │ Active │ [Edit] [Delete] │ │
│ 56%       │ │ │ Marjorie │ Person │ -        │ Active │ [Edit] [Delete] │ │
│ Wind:     │ │ │ Layla    │ Pet    │ dog      │ Active │ [Edit] [Delete] │ │
│ 7 mph     │ │ │ Lucy     │ Pet    │ dog      │ Active │ [Edit] [Delete] │ │
│           │ │ │ Sadie    │ Pet    │ cat      │ Active │ [Edit] [Delete] │ │
│ ☀️ Tmrw   │ │ └───────────────────────────────────────────────────────────┘ │
│ H:82 L:60 │ │                                                               │
│ ☁️ Mon    │ │                                                               │
│ H:86 L:61 │ │ ┌─ Add/Edit Family Member Modal ──────────────────────────┐ │
│ ☁️ Tue    │ │ │                                 [x] Close                │ │
│ H:84 L:64 │ │ │                                                          │ │
│ ☁️ Wed    │ │ │ Name: ________________                                   │ │
│ H:85 L:65 │ │ │                                                          │ │
│ ⚡ Thu    │ │ │ Type: [Person ▼] [Pet ▼]                                │ │
│ H:82 L:66 │ │ │                                                          │ │
│           │ │ │ Pet Type: [dog ▼] [cat ▼] [other ▼] (if Type = Pet)     │ │
│           │ │ │                                                          │ │
│           │ │ │ Status: [Active ▼] [Inactive ▼]                         │ │
│           │ │ │                                                          │ │
│           │ │ │                          [Cancel] [Save]                 │ │
│           │ │ └──────────────────────────────────────────────────────────┘ │
│           │ └───────────────────────────────────────────────────────────────┘
└───────────┘

┌─ Recurring Tasks Tab View ─────────────────────────────────────────────────┐
│                                                                            │
│ [Add Recurring Task]                                                       │
│                                                                            │
│ ┌─ Recurring Tasks Table ────────────────────────────────────────────────┐ │
│ │ Task Name │ Assigned To │ Frequency │ Due │ Overdue │ Category │ Status │ Actions          │ │
│ ├───────────┼─────────────┼───────────┼─────┼─────────┼──────────┼────────┼──────────────────┤ │
│ │ [Sample recurring tasks would be listed here with edit/delete actions] │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│ ┌─ Add/Edit Recurring Task Modal ──────────────────────────────────────┐   │
│ │                                              [x] Close               │   │
│ │                                                                      │   │
│ │ Task Name: ________________                                          │   │
│ │                                                                      │   │
│ │ Assigned to: [Bob ▼] [Marjorie ▼] [Layla ▼] [Lucy ▼] [Sadie ▼]     │   │
│ │                                                                      │   │
│ │ Frequency: [Daily ▼] [Weekly ▼] [Monthly ▼]                         │   │
│ │                                                                      │   │
│ │ Due: [Morning ▼] [Evening ▼] (Daily)                                │   │
│ │      [Monday ▼] [Tuesday ▼]... (Weekly)                             │   │
│ │      [1st ▼] [2nd ▼] [15th ▼]... (Monthly)                          │   │
│ │                                                                      │   │
│ │ Overdue when: [Immediate ▼] [1 hour ▼] [6 hours ▼] [1 day ▼]       │   │
│ │                                                                      │   │
│ │ Category: [Medication ▼] [Feeding ▼] [Other ▼]                      │   │
│ │                                                                      │   │
│ │ Status: [Active ▼] [Inactive ▼]                                     │   │
│ │                                                                      │   │
│ │                                   [Cancel] [Save]                    │   │
│ └──────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘

Components:
- Sidebar: Same weather widget as Activities
- Navigation: Tab-based with "Add Tasks" highlighted
- Tab Switcher: Family Members / Recurring Tasks
- Data Tables: Sortable columns with inline edit/delete actions
- Modal Forms: Popup forms with validation and cancel/save actions
- Conditional Fields: Pet Type appears only when Type = Pet
- Dynamic Due Fields: Content changes based on Frequency selection
```

Reference: [admin.png](./admin.png)

### 3. Meals - Show available meal kits
'''
Not for MVP, Next release
'''

## UI States & Behavior Specifications

### Task State Visual Indicators
```css
/* Task Item States */
.task-item {
  /* Default: Due tasks */
  background-color: var(--bg-container);
  
  /* Completed tasks */
  &.completed {
    background-color: var(--accent-success);
    color: var(--text-white);
  }
  
  /* Overdue tasks */
  &.overdue {
    background-color: var(--accent-red);
    color: var(--text-white);
  }
}
```

### Loading States
- **Page Load**: Full-screen spinner or loading bar
- **Data Refresh**: Loading bar at top of content area
- **Form Submission**: Button shows spinner with "Saving..." text

### Empty States
- **Admin Tables**: Empty table with centered message:
  - Family Members: "Add family members to get started"
  - Recurring Tasks: "Add recurring tasks to get started"
- **Daily Cards**: Family member card shows "No tasks today" when no tasks assigned

### Task Completion Flow
```
User taps radio button → Immediate UI update (color + progress dial) → Background API save
│
├─ Success: State persisted
└─ Failure: Retry with exponential backoff
   └─ Final failure: Modal alert + revert UI state
```

**State Management Requirements:**
- Queue user actions during slow network
- Handle rapid tap/untap sequences with proper state reconciliation
- Optimistic UI updates with rollback capability

### Form Validation Rules
```javascript
// Family Member Form
{
  name: { required: true, maxLength: 15 },
  type: { required: true, enum: ['Person', 'Pet'] },
  petType: { required: true if type === 'Pet', enum: ['dog', 'cat', 'other'] },
  status: { required: true, enum: ['Active', 'Inactive'] }
}

// Recurring Task Form  
{
  taskName: { required: true, maxLength: 30 },
  assignedTo: { required: true, uuid: familyMemberId },
  frequency: { required: true, enum: ['Daily', 'Weekly', 'Monthly'] },
  due: { required: true, conditional: true }, // Content varies by frequency
  overdueWhen: { required: true, enum: ['Immediate', '1 hour', '6 hours', '1 day'] },
  category: { required: true, enum: ['Medication', 'Feeding', 'Other'] },
  status: { required: true, enum: ['Active', 'Inactive'] }
}
```

### Data Model Keys
- **Family Members**: UUID primary key, name not unique
- **Activities**: UUID primary key with family member relationship
- **Completions**: UUID primary key with activity + date relationship

### Progress Calculation
- **Dial Logic**: `completed_tasks_today / total_tasks_today` for each family member
- **Real-time Updates**: Progress recalculates immediately on task completion

### Modal Behavior
- **Add**: Empty form with default values
- **Edit**: Same form component, pre-populated with existing data
- **Delete Confirmation**: Simple "Are you sure you want to delete [Name]?" with Cancel/Delete buttons

### Error Handling Strategy
```
Network Request → Retry (3x with backoff) → Success/Final Failure
│
├─ Success: Update UI state
└─ Final Failure: 
   ├─ Revert optimistic UI changes
   ├─ Show modal alert with error message
   └─ Option to retry or dismiss
```

### Touch Interface Optimizations
- **Target Size**: Minimum 44px touch targets for radio buttons and action buttons
- **Visual Feedback**: Subtle press animation (scale 0.95) on button tap
- **No Hover States**: Interface designed for direct touch interaction

Reference: [admin.png](./admin.png)

## Component Specifications

### Weather icons
```
<!-- Icons for weather api mapping -->
function getWeatherEmoji(iconCode: string) {
  const iconMap: { [key: string]: string } = {
    '01d': '☀️', '01n': '🌙',
    '02d': '🌤️', '02n': '☁️',
    '03d': '☁️', '03n': '☁️',
    '04d': '☁️', '04n': '☁️',
    '09d': '🌧️', '09n': '🌧️',
    '10d': '🌧️', '10n': '🌧️',
    '11d': '⚡', '11n': '⚡',
    '13d': '❄️', '13n': '❄️',
    '50d': '🌫️', '50n': '🌫️'
  }
  return iconMap[iconCode] || '🌤️'
```

## Mobile Responsive Design

### Breakpoints
```css
/* Mobile First Approach */
.container { max-width: 100%; }

@media (min-width: 1280px) { /* lg */
  .container { max-width: 1280px; }
}
```

## Accessibility Considerations

### Screen Reader Support
- All interactive elements have `aria-label` attributes
- Status changes announced via `aria-live` regions
- Touchscreen navigation follows logical tab order

## Usability Testing Plan

### Key Testing Scenarios
1. **First-time user onboarding** - Can complete setup in under 5 minutes?
2. **Task creation flow** - Intuitive form flow and validation?
3. **Status updates** - Clear visual feedback and confirmation?
4. **Mobile usage** - Touch targets adequate?
5. **Error recovery** - Clear error messages and recovery paths?

---

**Next Step:** Define technical architecture and data models in `05-TECHNICAL-DESIGN.md`