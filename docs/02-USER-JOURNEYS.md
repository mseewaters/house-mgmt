# User Journeys: house-mgmt

## Primary User Personas

### Sarah - Wife
- **Goal:** Know when medication has been taken, remind on missing dose.  Know when pets ahve bene taken care of.
- **Pain Points:** No way to know when pets have been fed, if treats have been given out
- **Tech Comfort:** High - supports all engagement

### Mike - Husband  
- **Goal:** Ensure wife knows that acitivites have taken place, know what meals wife has ordered and what is available for dinner
- **Pain Points:** Not having recipes for meal kits
- **Tech Comfort:** Medium - uses technology at surface level

## Core User Journeys

### Journey 1: First-Time Setup (Sarah)
**Goal:** Set up recurring activities

1. **Landing** - Visits app homepage, sees activitity tracking, knows what is completed and isnt
2. **Meals** - No longer has to tell Mike what meals are coming
3. **Task Admin** - Creates recurring tasks, along with expectations of due dates, reminders


**Critical Success Factors:**
- [ ] Setup completes in under 3 minutes
- [ ] Touch screen based activity completion
- [ ] Immediate visual of what is complete vs due

### Journey 2: Menu Management (Mike)
**Goal:** See available meals for the week with recipes

1. **Landing** - Easy pas through to meal with useful daily infomation
2. **Meals** - Shows what meals are coming by date, what has already been prepared
3. **Links** - Quick access to recipes that can be displayed on screen


**Critical Success Factors:**
- [ ] Meals loads in under 2 seconds
- [ ] Easy access to recipes that can be siplayed on mostly full screen
- [ ] Only non-cooked meals are displayed


### Journey 3: Tracking (Sarah)
**Goal:** Marks what has been completed real-time

1. **Landing** - View of all activites that are due for a given day, including weekly and monthly
2. **Landing** - Can check off with a button what has been complete, but still see closed items
3. **Landing** - Overdue items are shown with increased focus by color and order
4. **Landing** - Non time relevant items do not show up and obscure the view, focus


**Critical Success Factors:**
- [ ] Visual progress indicators are immediately clear
- [ ] Reminders aid in completing important tasks
- [ ] only taks for that day are shown

## Edge Cases & Error Scenarios

### Scenario 1: Fat finger issue
**Situation:** Wrong task selected as complete

- **Expected Behavior:** 
  - Uncehcking clears all recognition of completeness


## User Experience Principles

1. **Immediate Feedback** - Every action provides instant visual confirmation
2. **Forgiveness** - Easy to undo actions, hard to lose data permanently  
3. **Progressive Disclosure** - Simple by default, advanced features discoverable
4. **Contextual Help** - Guidance appears when and where users need it
5. **Accessibility** - Keyboard navigation, screen reader support, color contrast

---

**Next Step:** Define business rules and validation logic in `03-BUSINESS-LOGIC.md`