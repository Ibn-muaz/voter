# Admin Approval System Documentation

## Overview

The Admin Approval System is a robust workflow mechanism that ensures all voter registrations pass through an admin approval stage before final acceptance. This system includes risk assessment, comprehensive audit logging, and multi-layer verification checks.

## Key Features

### 1. **Registration Status Workflow**

```
draft → pending_verification → pending_admin_approval → approved
                             ↓
                           rejected
```

**Status Definitions:**
- **draft**: Initial registration state
- **pending_verification**: AI verification completed
- **pending_admin_approval**: Awaiting admin approval (NEW)
- **approved**: Admin approved, VIN generated
- **rejected**: Registration rejected
- **flagged**: Flagged for manual review

### 2. **Admin Approval Process**

#### Step 1: Registration Submission
- User completes 4-step registration wizard
- AI verification runs automatically
- Risk level is calculated
- Status changes to `pending_admin_approval` (no longer auto-approved)

#### Step 2: Admin Review
Admins access pending registrations via:
- Admin Dashboard: `/admin/registration/voterregistration/`
- Pending Approvals View: `/registration/pending-approvals/`

#### Step 3: Approval Decision
Admins can:
- **Approve**: Generate VIN and TVC, set status to `approved`
- **Reject**: Provide rejection reason, set status to `rejected`
- **Flag**: Mark for manual review without rejecting
- **Override**: Manually override AI decisions

#### Step 4: Audit Logging
Each decision creates an `ApprovalAuditLog` entry with:
- Admin user who made the decision
- Action taken (approve/reject/flag/override)
- Reason for the decision
- Risk assessment at time of approval
- AI score snapshot
- Verification checks performed
- IP address and user agent (for compliance)

### 3. **Risk Assessment System**

Risk levels are auto-calculated based on AI verification score:

```python
if ai_verification_score >= 0.85:
    risk_level = 'low'      # Green badge
elif ai_verification_score >= 0.65:
    risk_level = 'medium'   # Yellow badge
else:
    risk_level = 'high'     # Red badge
```

**Color Coding in Admin Panel:**
- 🟢 Low Risk: Green (#28a745)
- 🟡 Medium Risk: Yellow (#ffc107)
- 🔴 High Risk: Red (#dc3545)

### 4. **Approval Audit Trail**

The `ApprovalAuditLog` model tracks:
- **registration**: Link to VoterRegistration
- **admin_user**: Admin who made the decision
- **action**: Type of action (approve/reject/flag/override)
- **reason**: Detailed reason for decision
- **risk_assessment**: Risk level at approval
- **ai_score_at_approval**: AI verification score snapshot
- **documents_verified**: Boolean flag
- **biometrics_verified**: Boolean flag
- **age_verified**: Boolean flag
- **timestamp**: When action was taken (auto_now_add)
- **ip_address**: Admin's IP address
- **user_agent**: Admin's browser info

### 5. **Permission Control**

**Superuser Only Actions:**
- Approve registrations
- Reject registrations
- Override admin decisions

**Staff Actions:**
- View all registrations
- View pending approvals
- Filter by status and risk level
- Search registrations
- View audit logs
- Export reports

**Non-Staff:**
- View own registration status
- Download TVC after approval

## Database Models

### VoterRegistration (Extended)

```python
# New fields
approved_by = ForeignKey(User, related_name='registrations_approved')
approval_notes = TextField()
approval_timestamp = DateTimeField()
risk_level = CharField(choices=['low', 'medium', 'high'])
risk_assessment_notes = TextField()

# New methods
def calculate_risk_level(self):
    """Calculate risk based on AI score"""
    
def is_ready_for_approval(self):
    """Check if registration can be approved"""
```

### ApprovalAuditLog (New)

Complete audit trail of all approval decisions for compliance and forensics.

## Admin Panel Features

### Registration List View

Enhanced list display with:
- **vin**: Voter Identification Number
- **full_name**: Applicant's full name
- **date_of_birth**: Age calculation
- **status**: Current status badge
- **risk_level_badge**: Color-coded risk level
- **ai_verification_score**: Numerical score
- **approved_by_name**: Admin who approved
- **created_at**: When registered
- **approval_actions**: Quick action buttons

### Filter Options

- **Status**: All status types
- **Risk Level**: Low/Medium/High
- **Gender**: Male/Female
- **State of Origin**: All Nigerian states
- **Flagged for Review**: Yes/No
- **Date Range**: Creation and approval dates

### Bulk Actions

- ✓ Approve selected registrations
- ✗ Reject selected registrations
- 🚩 Flag for review
- 🗑️ Clear review flag
- Mark as suspected underage
- Clear underage suspicion
- 📥 Export to CSV
- 📊 Export pending approvals report

### Pending Approvals Dashboard

**URL**: `/registration/pending-approvals/`

Features:
- Quick stats on pending registrations
- Filter by risk level
- Sort by date or AI score
- Pagination (20 per page)
- Direct review links

**Stats Panel:**
```
Total Pending: X
├── High Risk: Y
├── Medium Risk: Z
└── Low Risk: W
```

## API Endpoints

### Admin Endpoints (Staff Only)

```
GET  /admin/registration/voterregistration/
     - List all registrations with filters

GET  /registration/pending-approvals/
     - View pending approvals dashboard

POST /admin/registration/voterregistration/<id>/
     - Update registration (approve/reject/flag)

GET  /admin/registration/approvalauditlog/
     - View approval audit logs

POST /admin/registration/voterregistration/approve_registrations/
     - Bulk approve action

POST /admin/registration/voterregistration/reject_registrations/
     - Bulk reject action

POST /admin/registration/voterregistration/export_selected/
     - Export selected to CSV

POST /admin/registration/voterregistration/export_pending_approvals/
     - Export pending approvals report
```

### User Endpoints

```
GET  /registration/submitted/<id>/
     - View submission confirmation

GET  /registration/success/<id>/
     - View approval confirmation

GET  /registration/rejected/<id>/
     - View rejection notice

GET  /registration/download-tvc/<id>/
     - Download temporary voter card (PDF)
```

## Workflows

### Approval Flow

```
1. User submits registration
   ↓
2. AI verification runs
   ↓
3. Risk level calculated
   ↓
4. Status → pending_admin_approval
   ↓
5. Admin reviews in dashboard
   ↓
6. Admin makes decision:
   ├─ APPROVE → Generate VIN + TVC → Create AuditLog
   ├─ REJECT → Set rejection reason → Create AuditLog
   ├─ FLAG → Mark for manual review → Continue waiting
   └─ OVERRIDE → Manual decision → Create AuditLog
   ↓
7. User notified of result
```

### Rejection Flow

```
1. Admin selects registration
   ↓
2. Clicks "Reject" action
   ↓
3. System prompts for reason
   ↓
4. Creates ApprovalAuditLog:
   - action = 'reject'
   - reason = admin input
   - risk_assessment = current level
   ↓
5. User receives rejection email
   ↓
6. Registration shows rejection reason
```

### Audit Trail Access

**View audit logs:**
```
/admin/registration/approvalauditlog/

Filters:
- Action type (approve/reject/flag/override)
- Risk assessment level
- Date range
- Admin user

Columns:
- Registration VIN (linked)
- Action badge (color-coded)
- Admin username
- Risk level
- AI score
- Timestamp
```

## Security Features

### 1. Permission-Based Access

```python
@login_required
@user_passes_test(is_admin)
def pending_approvals(request):
    """Only admins can access"""
```

### 2. Audit Logging

All decisions tracked with:
- Timestamp
- Admin user
- IP address
- User agent
- Decision reason
- Risk assessment
- AI score snapshot

### 3. Compliance

- Immutable audit logs (no deletion)
- Complete decision history
- Traceable approval chain
- Risk assessments preserved

### 4. Data Validation

```python
def is_ready_for_approval(self):
    """Validate registration can be approved"""
    return (
        self.status == 'pending_verification' and
        self.step_4_completed and
        not self.is_underage_suspected
    )
```

## Usage Examples

### Approve a Registration (Admin)

```python
# Via admin panel
1. Go to Admin > Voter Registrations
2. Find registration in pending_admin_approval status
3. Click registration
4. Review details and risk assessment
5. Click "Approve" button
6. System creates:
   - VIN: NE1234567890
   - TVC (Temporary Voter Card)
   - ApprovalAuditLog entry

# Email sent to user with VIN
```

### Reject a Registration (Admin)

```python
# Via bulk action
1. Select multiple registrations
2. Choose "Reject selected registrations"
3. System prompts for reason
4. Each creates ApprovalAuditLog with:
   - action = 'reject'
   - reason = provided input
   - timestamp = now
```

### Export Pending Approvals (Admin)

```
1. Go to Registrations list or pending-approvals
2. Click "Export pending approvals" button
3. Download CSV with columns:
   - VIN
   - Full Name
   - Age
   - Risk Level
   - AI Score
   - Documents Verified
   - Biometrics Score
   - Days Pending
   - Created At
```

## Migration Steps

### 1. Create Migration

```bash
cd backend
python manage.py makemigrations registration
```

### 2. Apply Migration

```bash
python manage.py migrate registration
```

### 3. Test Workflows

```bash
python manage.py test registration.tests.AdminApprovalTest
```

## Database Performance

### Indexes Added

```python
models.Index(fields=['status', 'approved_by'])
models.Index(fields=['registration', 'timestamp'])
models.Index(fields=['admin_user', 'action'])
```

These ensure fast filtering on:
- Pending approvals queries
- Audit log lookups
- Admin activity reports

## Error Handling

### Validation Errors

```python
# If registration not ready for approval
"Registration must complete all steps and pass AI verification"

# If underage suspected
"Registration rejected: Suspected underage attempt"

# If permission denied
"Only superusers can approve registrations"
```

### Audit Log Errors

All errors are logged to:
```
ApprovalAuditLog with action='error'
```

## Compliance & INEC Standards

✓ Complete approval audit trail
✓ Admin decision tracking
✓ Risk assessment documentation
✓ Immutable logs for forensics
✓ IP address logging
✓ User agent logging
✓ Timestamp preservation
✓ Decision reason storage

## Future Enhancements

- [ ] Email notifications on approval/rejection
- [ ] SMS notifications for registrants
- [ ] Approval workflows with multiple admins
- [ ] Rejection appeal process
- [ ] Analytics dashboard
- [ ] Advanced risk scoring
- [ ] Machine learning for auto-decisions
- [ ] Two-factor auth for high-risk approvals

## Support & Troubleshooting

### Issue: "Only superusers can approve"

**Solution**: Ensure admin user has `is_superuser=True`

```bash
python manage.py shell
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
user.is_superuser = True
user.save()
```

### Issue: Audit logs not appearing

**Solution**: Verify migration was applied

```bash
python manage.py showmigrations registration
```

### Issue: Risk level not calculated

**Solution**: Call calculate_risk_level() after AI verification

```python
registration.calculate_risk_level()
registration.save()
```
