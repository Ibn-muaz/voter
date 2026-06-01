# Generated migration for admin approval system

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0001_initial'),  # Update this with your actual last migration
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Add new status choice
        migrations.AlterField(
            model_name='voterregistration',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('pending_verification', 'Pending Verification'),
                    ('pending_admin_approval', 'Pending Admin Approval'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                    ('flagged', 'Flagged for Review')
                ],
                default='draft',
                max_length=20
            ),
        ),
        
        # Add new rejection reason
        migrations.AlterField(
            model_name='voterregistration',
            name='rejection_reason',
            field=models.CharField(
                blank=True,
                choices=[
                    ('underage', 'Underage (below 18 years)'),
                    ('document_mismatch', 'Document information mismatch'),
                    ('biometric_failure', 'Biometric verification failed'),
                    ('duplicate', 'Duplicate registration detected'),
                    ('anomaly_detected', 'Anomaly detected in registration'),
                    ('manual_review', 'Requires manual review'),
                    ('admin_rejection', 'Rejected by admin')
                ],
                max_length=50
            ),
        ),
        
        # Add admin approval fields
        migrations.AddField(
            model_name='voterregistration',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='registrations_approved',
                to='auth.user'
            ),
        ),
        
        migrations.AddField(
            model_name='voterregistration',
            name='approval_notes',
            field=models.TextField(
                blank=True,
                help_text='Admin notes during approval process'
            ),
        ),
        
        migrations.AddField(
            model_name='voterregistration',
            name='approval_timestamp',
            field=models.DateTimeField(null=True, blank=True),
        ),
        
        # Add risk assessment fields
        migrations.AddField(
            model_name='voterregistration',
            name='risk_level',
            field=models.CharField(
                choices=[
                    ('low', 'Low Risk'),
                    ('medium', 'Medium Risk'),
                    ('high', 'High Risk')
                ],
                default='medium',
                help_text='Auto-calculated risk level based on AI verification',
                max_length=20
            ),
        ),
        
        migrations.AddField(
            model_name='voterregistration',
            name='risk_assessment_notes',
            field=models.TextField(
                blank=True,
                help_text='Detailed risk assessment notes'
            ),
        ),
        
        # Add index for status and approved_by
        migrations.AddIndex(
            model_name='voterregistration',
            index=models.Index(
                fields=['status', 'approved_by'],
                name='registration_status_approv_idx'
            ),
        ),
        
        # Create ApprovalAuditLog model
        migrations.CreateModel(
            name='ApprovalAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('approve', 'Approved'),
                        ('reject', 'Rejected'),
                        ('flag', 'Flagged for Review'),
                        ('override', 'Manual Override')
                    ],
                    max_length=20
                )),
                ('reason', models.TextField(help_text='Reason for the approval/rejection decision')),
                ('risk_assessment', models.CharField(
                    blank=True,
                    choices=[
                        ('low', 'Low Risk'),
                        ('medium', 'Medium Risk'),
                        ('high', 'High Risk')
                    ],
                    max_length=20
                )),
                ('ai_score_at_approval', models.FloatField(
                    validators=[
                        django.core.validators.MinValueValidator(0.0),
                        django.core.validators.MaxValueValidator(1.0)
                    ]
                )),
                ('documents_verified', models.BooleanField(default=False)),
                ('biometrics_verified', models.BooleanField(default=False)),
                ('age_verified', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('admin_user', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approval_actions',
                    to='auth.user'
                )),
                ('registration', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='approval_audits',
                    to='registration.voterregistration'
                )),
            ],
            options={
                'verbose_name': 'Approval Audit Log',
                'verbose_name_plural': 'Approval Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add indexes for ApprovalAuditLog
        migrations.AddIndex(
            model_name='approvalauditlog',
            index=models.Index(
                fields=['registration', 'timestamp'],
                name='registration_regist_timesta_idx'
            ),
        ),
        
        migrations.AddIndex(
            model_name='approvalauditlog',
            index=models.Index(
                fields=['admin_user', 'action'],
                name='registration_admin_user_act_idx'
            ),
        ),
    ]
