# Business Logic: house-mgmt

## Core Business Rules

### Set up
- **Member creation**
  - Name must be unique and have attribute to suppot visuals
  - Must identify person or pet
  - If pet, must identify pet type


- **Activity creation**
  - Activity must have short descriptions
  - Activity must have a frequency
  - Activity must have a timing for when it is due and overdue
  - Activity must have rules for when to skip and move to next cycle, eg if daily vitamin not taken by midnight, release and move to next day

### Completion
- **Task Completion**
  - Should be push buttom
  - Can be undone if error
  - Must be assigned to one family member and one recurring task
  - Can be skipped if time period passes without completiona nd next cycle starts


### Menus
- **Available kits**
  - Available meal kits reflecting what has been shipped for that week and not cooked should be shown
  - Shipped meals shoudl be determined form Home Chef email
  - Meals that have been cooked are removed from the list

- **Recipes**
  - Online recipes can be shown on screen without leaving the app
  - Recipes can be found via clicking linf

## Data Validation Rules

### Input Validation
```python
# Family members
member_id = uuid
member_type: one_of(['person', 'pet'])
pet_type: if member_type=pet, one_of(['dog', 'cat','bird','fish','other'])
name: max_length(50) AND not_empty

# Recurring Activities 
activity_id = uuid
assigned to = member_id
category: one_of['medication','feeding','health','hygiene','cleaning','other']
frequency: one_of['daily','weekly','monthly']
name: max_length(100) AND not_empty AND sanitized_html
is_active: boolean

# Completions
completion_id: uuid
activity_id: activity_id
member_id: member_id
completed_by: 'user'
completion_date: UTC date
```

### Business Logic Constraints
```python
# Prevent orphaned projects
def delete_team(team_id):
    if team.projects.count() > 0:
        raise ValidationError("Cannot delete team with active projects")
    
# Enforce admin requirement
def remove_team_admin(user_id, team_id):
    remaining_admins = team.admins.exclude(id=user_id).count()
    if remaining_admins == 0:
        raise ValidationError("Team must have at least one admin")

# Task status transitions
def update_task_status(task_id, new_status, user_id):
    if new_status == "Done" and not user.is_team_admin():
        raise PermissionError("Only admins can mark tasks as Done")
```

## Notification & Communication Rules

### Real-time Updates
- **Task Status Changes:** Change visual colors, check boxes


## Reporting & Analytics Rules

### Metrics Calculation
```python
# Completion (tasks completed per week)
complete = completed_tasks / daily_tasks_inscope

```

### Data Retention
- **Active Recurrign task:** Unlimited retention
- **Completions:** 1 years then soft delete
- **User Activity Logs:** 90 days for debugging

## Integration Rules

### API Rate Limiting
- **Authenticated Users:** 100 requests/hour per user

### External Dependencies
- **Email Service:** SES
- **AWS Services:** Graceful degradation if services unavailable
- **Database:** no-SQL, free tier read replicas

---

**Next Step:** Create UI/UX mockups and wireframes in `04-PROTOTYPES.md`