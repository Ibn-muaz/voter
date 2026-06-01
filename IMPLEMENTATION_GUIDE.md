# Implementation Guide - Admin Approval System

## Quick Start

### 1. Apply Migration

```bash
cd backend
python manage.py migrate registration
```

### 2. Test the System

```bash
python manage.py test registration.tests
```

### 3. Create a Test Admin User (if needed)

```bash
python manage.py shell
from django.contrib.auth.models import User
admin = User.objects.create_superuser('testadmin', 'admin@test.com', 'password123')
```

### 4. Access Admin Dashboard

Navigate to: `http://localhost:8000/admin/registration/voterregistration/`

---

## File Structure

```
backend/apps/registration/
├── models.py                    # Enhanced with admin approval fields
├── admin.py                     # Enhanced admin interface
├── views.py                     # Updated views with approval workflow
├── forms.py                     # Registration forms (unchanged)
├── urls.py                      # URL routing (needs update)
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_admin_approval_workflow.py    # NEW
├── templates/
│   ├── registration/
│   │   ├── step_1.html
│   │   ├── step_2.html
│   │   ├── step_3.html
│   │   ├── step_4.html
│   │   ├── submitted.html              # NEW - Awaiting approval
│   │   ├── success.html
│   │   ├── rejected.html
│   │   ├── list.html
│   │   ├── pending_approvals.html       # NEW - Admin dashboard
│   │   └── detail.html
```

---

## Configuration Changes

### settings.py

No changes required. Existing settings support the new workflow.

### urls.py

Update `backend/apps/registration/urls.py`:

```python
from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    # Existing patterns
    path('wizard/<int:step>/', views.registration_wizard, name='wizard'),
    path('success/<int:registration_id>/', views.registration_success, name='success'),
    path('rejected/<int:registration_id>/', views.registration_rejected, name='rejected'),
    
    # NEW: Awaiting approval page
    path('submitted/<int:registration_id>/', views.registration_submitted, name='submitted'),
    
    # Admin patterns
    path('list/', views.registration_list, name='list'),
    path('detail/<int:registration_id>/', views.registration_detail, name='detail'),
    path('search/', views.registration_search, name='search'),
    
    # NEW: Pending approvals dashboard
    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    
    # AJAX endpoints
    path('get-lgas/', views.get_lgas_for_state, name='get_lgas'),
    path('capture-photo/', views.capture_photo, name='capture_photo'),
    path('capture-fingerprint/', views.capture_fingerprint, name='capture_fingerprint'),
    
    # TVC download
    path('download-tvc/<int:registration_id>/', views.download_tvc, name='download_tvc'),
]
```

---

## Template Changes

### 1. New Template: `submitted.html`

Show when registration is submitted awaiting admin approval:

```html
{% extends "base.html" %}

{% block title %}Registration Submitted{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="alert alert-info">
        <h4>Registration Submitted Successfully</h4>
        <p>Your registration has been submitted for admin approval.</p>
    </div>
    
    <div class="card">
        <div class="card-header">
            <h5>Your Registration Details</h5>
        </div>
        <div class="card-body">
            <p><strong>Name:</strong> {{ registration.get_full_name }}</p>
            <p><strong>Status:</strong> <span class="badge badge-warning">Pending Admin Approval</span></p>
            <p><strong>Risk Level:</strong> 
                {% if registration.risk_level == 'low' %}
                    <span class="badge badge-success">Low</span>
                {% elif registration.risk_level == 'medium' %}
                    <span class="badge badge-warning">Medium</span>
                {% else %}
                    <span class="badge badge-danger">High</span>
                {% endif %}
            </p>
            <p><strong>AI Score:</strong> {{ registration.ai_verification_score|floatformat:2 }}</p>
            <p><strong>Submitted:</strong> {{ registration.created_at }}</p>
        </div>
    </div>
    
    <div class="mt-3">
        <p>An administrator will review your application and notify you of the decision.</p>
        <a href="/" class="btn btn-primary">Return Home</a>
    </div>
</div>
{% endblock %}
```

### 2. New Template: `pending_approvals.html`

Admin dashboard for pending approvals:

```html
{% extends "admin/base_site.html" %}

{% block title %}Pending Approvals{% endblock %}

{% block content %}
<div class="pending-approvals-dashboard">
    <h1>Pending Approvals Dashboard</h1>
    
    <!-- Stats -->
    <div class="row">
        <div class="col-md-3">
            <div class="card text-white bg-primary">
                <div class="card-body">
                    <h5>Total Pending</h5>
                    <h3>{{ stats.total_pending }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-danger">
                <div class="card-body">
                    <h5>High Risk</h5>
                    <h3>{{ stats.high_risk }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-warning">
                <div class="card-body">
                    <h5>Medium Risk</h5>
                    <h3>{{ stats.medium_risk }}</h3>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-white bg-success">
                <div class="card-body">
                    <h5>Low Risk</h5>
                    <h3>{{ stats.low_risk }}</h3>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Filters -->
    <form method="get" class="mt-4">
        <div class="form-group">
            <label>Filter by Risk Level:</label>
            <select name="risk_level" class="form-control">
                <option value="">All</option>
                <option value="low" {% if risk_filter == 'low' %}selected{% endif %}>Low</option>
                <option value="medium" {% if risk_filter == 'medium' %}selected{% endif %}>Medium</option>
                <option value="high" {% if risk_filter == 'high' %}selected{% endif %}>High</option>
            </select>
        </div>
        
        <div class="form-group">
            <label>Sort by:</label>
            <select name="sort_by" class="form-control">
                <option value="-created_at" {% if sort_by == '-created_at' %}selected{% endif %}>Newest First</option>
                <option value="created_at" {% if sort_by == 'created_at' %}selected{% endif %}>Oldest First</option>
                <option value="-ai_verification_score" {% if sort_by == '-ai_verification_score' %}selected{% endif %}>Highest Risk First</option>
                <option value="ai_verification_score" {% if sort_by == 'ai_verification_score' %}selected{% endif %}>Lowest Risk First</option>
            </select>
        </div>
        
        <button type="submit" class="btn btn-primary">Filter</button>
    </form>
    
    <!-- Registrations Table -->
    <table class="table table-hover mt-4">
        <thead>
            <tr>
                <th>Name</th>
                <th>Risk Level</th>
                <th>AI Score</th>
                <th>Age</th>
                <th>State</th>
                <th>Days Pending</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for registration in page_obj %}
            <tr>
                <td>{{ registration.get_full_name }}</td>
                <td>
                    {% if registration.risk_level == 'low' %}
                        <span class="badge badge-success">Low</span>
                    {% elif registration.risk_level == 'medium' %}
                        <span class="badge badge-warning">Medium</span>
                    {% else %}
                        <span class="badge badge-danger">High</span>
                    {% endif %}
                </td>
                <td>{{ registration.ai_verification_score|floatformat:2 }}</td>
                <td>{{ registration.age }}</td>
                <td>{{ registration.state_of_origin }}</td>
                <td>{{ registration.created_at|timesince }}</td>
                <td>
                    <a href="/admin/registration/voterregistration/{{ registration.id }}/change/" 
                       class="btn btn-sm btn-primary">Review</a>
                </td>
            </tr>
            {% empty %}
            <tr>
                <td colspan="7" class="text-center">No pending approvals</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <!-- Pagination -->
    {% if page_obj.has_other_pages %}
    <nav aria-label="Page navigation">
        <ul class="pagination">
            {% if page_obj.has_previous %}
            <li class="page-item">
                <a class="page-link" href="?page=1">First</a>
            </li>
            <li class="page-item">
                <a class="page-link" href="?page={{ page_obj.previous_page_number }}">Previous</a>
            </li>
            {% endif %}
            
            {% for num in page_obj.paginator.page_range %}
            <li class="page-item {% if page_obj.number == num %}active{% endif %}">
                <a class="page-link" href="?page={{ num }}">{{ num }}</a>
            </li>
            {% endfor %}
            
            {% if page_obj.has_next %}
            <li class="page-item">
                <a class="page-link" href="?page={{ page_obj.next_page_number }}">Next</a>
            </li>
            <li class="page-item">
                <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">Last</a>
            </li>
            {% endif %}
        </ul>
    </nav>
    {% endif %}
</div>
{% endblock %}
```

---

## Testing

### Test Cases

Create `backend/apps/registration/tests.py`:

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import VoterRegistration, ApprovalAuditLog
from django.utils import timezone

class AdminApprovalTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        self.registration = VoterRegistration.objects.create(
            first_name='John',
            surname='Doe',
            date_of_birth='2000-01-01',
            status='pending_admin_approval',
            ai_verification_score=0.85
        )
    
    def test_admin_approve_registration(self):
        """Test admin can approve registration"""
        self.client.login(username='admin', password='password')
        
        # Admin approves
        self.registration.approved_by = self.admin
        self.registration.status = 'approved'
        self.registration.approval_timestamp = timezone.now()
        self.registration.save()
        
        # Verify VIN generated
        self.assertIsNotNone(self.registration.vin)
        self.assertEqual(self.registration.status, 'approved')
        self.assertEqual(self.registration.approved_by, self.admin)
    
    def test_approval_audit_log_created(self):
        """Test audit log is created on approval"""
        audit = ApprovalAuditLog.objects.create(
            registration=self.registration,
            admin_user=self.admin,
            action='approve',
            reason='Meets all requirements',
            risk_assessment='medium',
            ai_score_at_approval=0.85,
            documents_verified=True,
            biometrics_verified=True,
            age_verified=True
        )
        
        self.assertIsNotNone(audit.timestamp)
        self.assertEqual(audit.action, 'approve')
    
    def test_risk_level_calculation(self):
        """Test risk level is calculated correctly"""
        self.registration.calculate_risk_level()
        self.assertEqual(self.registration.risk_level, 'low')  # 0.85 >= 0.85
        
        self.registration.ai_verification_score = 0.70
        self.registration.calculate_risk_level()
        self.assertEqual(self.registration.risk_level, 'medium')  # 0.65 <= 0.70 < 0.85
        
        self.registration.ai_verification_score = 0.50
        self.registration.calculate_risk_level()
        self.assertEqual(self.registration.risk_level, 'high')  # 0.50 < 0.65

class PendingApprovalsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        
        # Create test registrations
        for i in range(5):
            VoterRegistration.objects.create(
                first_name=f'User{i}',
                surname='Test',
                date_of_birth='2000-01-01',
                status='pending_admin_approval',
                ai_verification_score=0.75
            )
    
    def test_pending_approvals_view_accessible(self):
        """Test pending approvals view is accessible to admin"""
        self.client.login(username='admin', password='password')
        response = self.client.get('/registration/pending-approvals/')
        self.assertEqual(response.status_code, 200)
    
    def test_pending_approvals_filter(self):
        """Test filtering pending approvals"""
        self.client.login(username='admin', password='password')
        response = self.client.get('/registration/pending-approvals/?risk_level=medium')
        self.assertEqual(response.status_code, 200)
```

Run tests:

```bash
python manage.py test registration.tests.AdminApprovalTest
```

---

## Deployment Checklist

- [ ] Apply migration: `python manage.py migrate`
- [ ] Test workflows locally
- [ ] Update URL routes in `urls.py`
- [ ] Create required templates
- [ ] Test admin panel approval flow
- [ ] Test audit logging
- [ ] Configure email notifications (optional)
- [ ] Update documentation
- [ ] Train admins on new workflow
- [ ] Deploy to production
- [ ] Monitor audit logs
- [ ] Gather user feedback

---

## Monitoring

### Key Metrics

```sql
-- Pending registrations count
SELECT COUNT(*) FROM registration_voterregistration 
WHERE status = 'pending_admin_approval';

-- Average time to approval
SELECT AVG(EXTRACT(EPOCH FROM (approval_timestamp - created_at))) 
FROM registration_voterregistration 
WHERE status = 'approved';

-- High-risk registrations
SELECT COUNT(*) FROM registration_voterregistration 
WHERE risk_level = 'high' AND status = 'pending_admin_approval';

-- Admin approvals by user
SELECT admin_user_id, action, COUNT(*) 
FROM registration_approvalauditlog 
GROUP BY admin_user_id, action;
```

---

## Common Issues & Solutions

### Issue: Registration stuck in `pending_admin_approval`

**Check:**
```bash
python manage.py shell
from registration.models import VoterRegistration
pending = VoterRegistration.objects.filter(status='pending_admin_approval')
print(f"Pending: {pending.count()}")
```

### Issue: Audit log not showing in admin

**Solution:**
```bash
python manage.py migrate registration
# Ensure ApprovalAuditLogAdmin is registered in admin.py
```

### Issue: VIN not generating on approval

**Solution:**
```python
from registration.views import generate_vin, generate_temporary_voter_card

registration.vin = generate_vin(registration)
generate_temporary_voter_card(registration)
registration.save()
```

---

## Support

For issues or questions:
1. Check ADMIN_APPROVAL_SYSTEM.md documentation
2. Review audit logs in admin panel
3. Check application logs: `backend/logs/inec_voter.log`
4. Run system diagnostics: `python manage.py test registration.tests`
