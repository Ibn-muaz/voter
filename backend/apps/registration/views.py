"""
Views for the voter registration system.
Implements multi-step registration wizard with AI verification.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count
import json
import uuid
import base64
import io

from .models import VoterRegistration, RegistrationStep, TemporaryVoterCard
from .forms import (
    PersonalInfoForm, DocumentUploadForm, BiometricCaptureForm,
    ReviewAndSubmitForm, RegistrationSearchForm, BulkRegistrationForm
)
from apps.ai_engine.underage_eradicator import UnderageEradicator
from apps.utils.pdf_generator import TVCGenerator
from apps.utils.security import SecurityUtils, CaptchaUtils
from apps.utils.fake_data_generator import FakeDataGenerator
from apps.audit.models import DataAccessLog, SystemEvent, AuditLog
from apps.documents.utils import DocumentProcessor
from apps.biometrics.utils import BiometricProcessor, process_biometric_data


def get_or_create_registration_session(request):
    """
    Get or create a registration session for the current user.
    """
    session_id = request.session.get('registration_session_id')

    if session_id:
        try:
            registration = VoterRegistration.objects.get(
                session_id=session_id,
                status__in=['draft', 'in_progress']
            )
            return registration
        except VoterRegistration.DoesNotExist:
            pass

    # Create new registration session
    session_id = str(uuid.uuid4())
    request.session['registration_session_id'] = session_id

    registration = VoterRegistration.objects.create(
        session_id=session_id,
        status='draft',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    # Log session creation
    AuditLog.objects.create(
        action_type='registration_started',
        description=f'New registration session started: {session_id}',
        user=None,
        ip_address=get_client_ip(request),
        metadata={'session_id': session_id}
    )

    return registration


def get_client_ip(request):
    """Get the client's IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def registration_wizard(request, step=1):
    """
    Main registration wizard view.
    Handles multi-step registration process.
    """
    if request.user.is_authenticated and not request.user.is_staff:
        # Regular users can only register themselves
        return redirect('registration:wizard', step=1)

    registration = get_or_create_registration_session(request)
    total_steps = 4

    # Redirect to appropriate step based on completion status
    if step > 1 and not registration.step_completed(step - 1):
        return redirect('registration:wizard', step=registration.get_next_required_step())

    if request.method == 'POST':
        return handle_registration_step(request, registration, step)

    # GET request - show the form
    context = {
        'registration': registration,
        'current_step': step,
        'total_steps': total_steps,
        'progress_percentage': (step / total_steps) * 100,
        'step_name': get_step_name(step),
    }

    if step == 1:
        context['form'] = PersonalInfoForm(instance=registration)
    elif step == 2:
        context['form'] = DocumentUploadForm(instance=registration)
    elif step == 3:
        context['form'] = BiometricCaptureForm()
    elif step == 4:
        # Generate CAPTCHA for final step
        captcha_text, captcha_image = CaptchaUtils.generate_captcha()
        request.session['captcha_text'] = captcha_text
        context['form'] = ReviewAndSubmitForm(expected_captcha=captcha_text)
        context['captcha_image'] = base64.b64encode(captcha_image).decode('utf-8')

    return render(request, f'registration/step_{step}.html', context)


def handle_registration_step(request, registration, step):
    """
    Handle POST request for a specific registration step.
    """
    if step == 1:
        return handle_personal_info_step(request, registration)
    elif step == 2:
        return handle_document_upload_step(request, registration)
    elif step == 3:
        return handle_biometric_capture_step(request, registration)
    elif step == 4:
        return handle_review_submit_step(request, registration)


def handle_personal_info_step(request, registration):
    """
    Handle personal information step.
    """
    form = PersonalInfoForm(request.POST, instance=registration)

    if form.is_valid():
        with transaction.atomic():
            registration = form.save(commit=False)
            registration.step_1_completed = True
            registration.save()

            # Create step record
            RegistrationStep.objects.create(
                registration=registration,
                step_number=1,
                step_name='Personal Information',
                completed_at=timezone.now(),
                step_data={
                    'first_name': registration.first_name,
                    'last_name': registration.surname,
                    'date_of_birth': str(registration.date_of_birth),
                }
            )

            messages.success(request, 'Personal information saved successfully.')
            return redirect('registration:wizard', step=2)

    return render(request, 'registration/step_1.html', {
        'form': form,
        'registration': registration,
        'current_step': 1,
        'total_steps': 4,
        'progress_percentage': 25,
    })


def handle_document_upload_step(request, registration):
    """
    Handle document upload step.
    """
    form = DocumentUploadForm(request.POST, request.FILES, instance=registration)

    if form.is_valid():
        with transaction.atomic():
            registration = form.save(commit=False)
            registration.step_2_completed = True
            registration.save()

            # Process documents with OCR
            doc_processor = DocumentProcessor()

            # Process proof of age document
            if registration.proof_of_age_document:
                ocr_result = doc_processor.extract_text_from_document(
                    registration.proof_of_age_document
                )
                registration.proof_of_age_ocr_text = ocr_result.get('text', '')
                registration.proof_of_age_confidence = ocr_result.get('confidence', 0)

            # Process proof of identity document
            if registration.proof_of_identity_document:
                ocr_result = doc_processor.extract_text_from_document(
                    registration.proof_of_identity_document
                )
                registration.proof_of_identity_ocr_text = ocr_result.get('text', '')
                registration.proof_of_identity_confidence = ocr_result.get('confidence', 0)

            # Process proof of address document
            if registration.proof_of_address_document:
                ocr_result = doc_processor.extract_text_from_document(
                    registration.proof_of_address_document
                )
                registration.proof_of_address_ocr_text = ocr_result.get('text', '')
                registration.proof_of_address_confidence = ocr_result.get('confidence', 0)

            registration.save()

            # Create step record
            RegistrationStep.objects.create(
                registration=registration,
                step_number=2,
                step_name='Document Upload',
                completed_at=timezone.now(),
                step_data={
                    'documents_uploaded': 3,  # All three documents
                    'ocr_processed': True,
                }
            )

            messages.success(request, 'Documents uploaded and processed successfully.')
            return redirect('registration:wizard', step=3)

    return render(request, 'registration/step_2.html', {
        'form': form,
        'registration': registration,
        'current_step': 2,
        'total_steps': 4,
        'progress_percentage': 50,
    })


def handle_biometric_capture_step(request, registration):
    """
    Handle biometric capture step.
    """
    form = BiometricCaptureForm(request.POST, request.FILES)

    if form.is_valid():
        with transaction.atomic():
            # Process biometric data
            biometric_processor = BiometricProcessor()

            fingerprint_image = form.cleaned_data['fingerprint_image']
            facial_image = form.cleaned_data['facial_image']

            # Process fingerprint
            fingerprint_result = biometric_processor.process_fingerprint(fingerprint_image)
            registration.fingerprint_template = fingerprint_result.get('template', '')
            registration.fingerprint_quality_score = fingerprint_result.get('quality_score', 0)

            # Process facial image
            facial_result = biometric_processor.process_facial_image(facial_image)
            registration.facial_template = facial_result.get('template', '')
            registration.facial_quality_score = facial_result.get('quality_score', 0)

            registration.step_3_completed = True
            registration.save()

            # Create step record
            RegistrationStep.objects.create(
                registration=registration,
                step_number=3,
                step_name='Biometric Capture',
                completed_at=timezone.now(),
                step_data={
                    'biometrics_captured': True,
                    'fingerprint_quality': registration.fingerprint_quality_score,
                    'facial_quality': registration.facial_quality_score,
                }
            )

            messages.success(request, 'Biometric data captured successfully.')
            return redirect('registration:wizard', step=4)

    return render(request, 'registration/step_3.html', {
        'form': form,
        'registration': registration,
        'current_step': 3,
        'total_steps': 4,
        'progress_percentage': 75,
    })


def handle_review_submit_step(request, registration):
    """
    Handle final review and submission step.
    """
    expected_captcha = request.session.get('captcha_text', '')
    form = ReviewAndSubmitForm(request.POST, expected_captcha=expected_captcha)

    if form.is_valid():
        with transaction.atomic():
            # Run AI verification
            eradicator = UnderageEradicator()
            verification_result = eradicator.verify_registration(registration)

            registration.ai_verification_result = verification_result
            registration.ai_verification_score = verification_result.get('score', 0)
            registration.ai_verification_layers = verification_result.get('layer_results', [])
            registration.is_underage_suspected = not verification_result.get('approved', False)
            registration.verification_completed_at = timezone.now()

            # Determine status based on AI results
            if registration.is_underage_suspected:
                registration.status = 'rejected'
                registration.rejection_reason = 'AI detected potential underage registration'
            else:
                registration.status = 'approved'
                # Generate VIN and Temporary Voter Card
                registration.vin = generate_vin(registration)
                generate_temporary_voter_card(registration)

            registration.step_4_completed = True
            registration.completed_at = timezone.now()
            registration.save()

            # Create final step record
            RegistrationStep.objects.create(
                registration=registration,
                step_number=4,
                step_name='Review and Submit',
                completed_at=timezone.now(),
                step_data={
                    'ai_verified': True,
                    'status': registration.status,
                    'vin_generated': bool(registration.vin),
                }
            )

            # Log completion
            AuditLog.objects.create(
                action_type='registration_completed',
                description=f'Registration completed with status: {registration.status}',
                user=None,
                ip_address=get_client_ip(request),
                metadata={
                    'registration_id': registration.id,
                    'vin': registration.vin,
                    'ai_score': registration.ai_verification_score,
                    'is_underage': registration.is_underage_suspected,
                }
            )

            # Clear session
            if 'registration_session_id' in request.session:
                del request.session['registration_session_id']
            if 'captcha_text' in request.session:
                del request.session['captcha_text']

            if registration.status == 'approved':
                messages.success(request, f'Registration completed successfully! Your VIN is: {registration.vin}')
                return redirect('registration:success', registration_id=registration.id)
            else:
                messages.error(request, 'Registration rejected due to suspected underage attempt.')
                return redirect('registration:rejected', registration_id=registration.id)

    # If we got here, form is invalid
    captcha_text, captcha_image = CaptchaUtils.generate_captcha()
    request.session['captcha_text'] = captcha_text
    form.expected_captcha = captcha_text

    return render(request, 'registration/step_4.html', {
        'form': form,
        'registration': registration,
        'current_step': 4,
        'total_steps': 4,
        'progress_percentage': 100,
        'captcha_image': base64.b64encode(captcha_image).decode('utf-8'),
    })


def generate_vin(registration):
    """
    Generate a unique Voter Identification Number (VIN).
    Format: AA1234567890 (2 letters + 10 digits)
    """
    # Use state code + random digits
    state_code = registration.state_of_origin.code[:2].upper() if registration.state_of_origin else 'NG'

    # Generate unique 10-digit number
    while True:
        random_digits = str(uuid.uuid4().int)[:10]
        vin = f"{state_code}{random_digits}"

        if not VoterRegistration.objects.filter(vin=vin).exists():
            return vin


def generate_temporary_voter_card(registration):
    """
    Generate and attach Temporary Voter Card (TVC) to registration.
    """
    try:
        generator = TVCGenerator()
        pdf_buffer = generator.generate_tvc(registration)

        # Save PDF to model
        filename = f"TVC_{registration.vin}.pdf"
        registration.temporary_voter_card.save(
            filename,
            ContentFile(pdf_buffer.getvalue()),
            save=False
        )
        registration.save()

    except Exception as e:
        # Log error but don't fail registration
        AuditLog.objects.create(
            action_type='tvc_generation_failed',
            description=f'Failed to generate TVC for registration {registration.id}: {str(e)}',
            user=None,
            metadata={'registration_id': registration.id, 'error': str(e)}
        )


def get_step_name(step):
    """Get the display name for a registration step."""
    step_names = {
        1: 'Personal Information',
        2: 'Document Upload',
        3: 'Biometric Capture',
        4: 'Review & Submit',
    }
    return step_names.get(step, f'Step {step}')


def registration_success(request, registration_id):
    """Display registration success page."""
    registration = get_object_or_404(VoterRegistration, id=registration_id, status='approved')

    # Log access
    DataAccessLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        access_type='view',
        data_type='registration_success',
        data_id=registration.id,
        ip_address=get_client_ip(request),
        purpose='view_registration_result'
    )

    return render(request, 'registration/success.html', {
        'registration': registration,
    })


def registration_rejected(request, registration_id):
    """Display registration rejection page."""
    registration = get_object_or_404(VoterRegistration, id=registration_id, status='rejected')

    return render(request, 'registration/rejected.html', {
        'registration': registration,
    })


@login_required
def registration_list(request):
    """List all registrations (admin only)."""
    if not request.user.is_staff:
        return redirect('home')

    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    registrations = VoterRegistration.objects.all().order_by('-created_at')

    if status_filter:
        registrations = registrations.filter(status=status_filter)

    if search_query:
        registrations = registrations.filter(
            Q(vin__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(registrations, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'registration/list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    })


@login_required
def registration_status(request, registration_id):
    """Check registration status by ID."""
    registration = get_object_or_404(VoterRegistration, id=registration_id)

    return render(request, 'registration/status.html', {
        'registration': registration,
        'status': registration.status,
        'vin': registration.vin if registration.status == 'approved' else None,
    })


def registration_detail(request, registration_id):
    """View detailed registration information (admin only)."""
    if not request.user.is_staff:
        return redirect('home')

    registration = get_object_or_404(VoterRegistration, id=registration_id)

    # Log access
    DataAccessLog.objects.create(
        user=request.user,
        access_type='view',
        data_type='registration_detail',
        data_id=registration.id,
        ip_address=get_client_ip(request),
        purpose='admin_review'
    )

    return render(request, 'registration/detail.html', {
        'registration': registration,
    })


@login_required
def registration_search(request):
    """Search for registrations."""
    if request.method == 'POST':
        form = RegistrationSearchForm(request.POST)
        if form.is_valid():
            search_type = form.cleaned_data['search_type']
            search_value = form.cleaned_data['search_value']

            # Build query based on search type
            query_kwargs = {}
            if search_type == 'vin':
                query_kwargs['vin__iexact'] = search_value.upper()
            elif search_type == 'phone':
                query_kwargs['phone_number__icontains'] = search_value
            elif search_type == 'name':
                # Search in first or last name
                query_kwargs['first_name__icontains'] = search_value
            elif search_type == 'polling_unit':
                query_kwargs['polling_unit__icontains'] = search_value

            registrations = VoterRegistration.objects.filter(**query_kwargs)

            # Log search
            DataAccessLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                access_type='search',
                data_type='registration',
                ip_address=get_client_ip(request),
                purpose='registration_search',
                metadata={'search_type': search_type, 'search_value': search_value}
            )

            return render(request, 'registration/search_results.html', {
                'registrations': registrations,
                'search_type': search_type,
                'search_value': search_value,
            })
    else:
        form = RegistrationSearchForm()

    return render(request, 'registration/search.html', {'form': form})


@require_POST
@csrf_exempt
def get_lgas_for_state(request):
    """AJAX endpoint to get LGAs for a selected state."""
    state_id = request.POST.get('state_id')
    if state_id:
        from apps.utils.models import LocalGovernmentArea
        lgas = LocalGovernmentArea.objects.filter(state_id=state_id).values('id', 'name')
        return JsonResponse({'lgas': list(lgas)})

    return JsonResponse({'lgas': []})


@login_required
def bulk_registration_upload(request):
    """Handle bulk registration uploads (admin only)."""
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        form = BulkRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']

            # Process CSV file
            try:
                generator = FakeDataGenerator()
                results = generator.process_bulk_upload(csv_file)

                messages.success(
                    request,
                    f'Bulk upload completed. Processed {results["processed"]} registrations.'
                )

                return redirect('registration_list')

            except Exception as e:
                messages.error(request, f'Error processing bulk upload: {str(e)}')
    else:
        form = BulkRegistrationForm()

    return render(request, 'registration/bulk_upload.html', {'form': form})


@login_required
def download_tvc(request, registration_id):
    """Download Temporary Voter Card PDF."""
    registration = get_object_or_404(
        VoterRegistration,
        id=registration_id,
        status='approved'
    )

    # Check permissions
    if not request.user.is_staff and registration.session_id != request.session.get('registration_session_id'):
        return HttpResponse('Unauthorized', status=403)

    if not registration.temporary_voter_card:
        return HttpResponse('TVC not available', status=404)

    # Log download
    DataAccessLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        access_type='download',
        data_type='tvc',
        data_id=registration.id,
        ip_address=get_client_ip(request),
        purpose='download_tvc'
    )

    response = HttpResponse(registration.temporary_voter_card.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="TVC_{registration.vin}.pdf"'
    return response


def success(request, vin):
    """
    Registration success page with TVC download.
    """
    registration = get_object_or_404(VoterRegistration, vin=vin, status='approved')
    return render(request, 'registration/success.html', {'registration': registration})


def rejected(request):
    """
    Registration rejection page.
    """
    return render(request, 'registration/rejected.html')


# AJAX endpoints for biometric capture
def capture_photo(request):
    """
    AJAX endpoint for photo capture.
    """
    if request.method == 'POST' and request.FILES.get('photo'):
        registration_id = request.session.get('registration_id')
        registration = get_object_or_404(VoterRegistration, id=registration_id)

        photo_file = request.FILES['photo']
        # Process photo with AI
        try:
            result = process_biometric_data(photo_file, 'photo')
            # Store result in step data
            step = registration.current_step
            step.step_data['biometric_photo'] = result
            step.save()

            return JsonResponse({'success': True, 'result': result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


def capture_fingerprint(request):
    """
    AJAX endpoint for fingerprint capture.
    """
    if request.method == 'POST' and request.FILES.get('fingerprint'):
        registration_id = request.session.get('registration_id')
        registration = get_object_or_404(VoterRegistration, id=registration_id)

        fingerprint_file = request.FILES['fingerprint']
        finger_type = request.POST.get('finger_type', 'left_thumb')

        try:
            result = process_biometric_data(fingerprint_file, 'fingerprint', finger_type)
            # Store result in step data
            step = registration.current_step
            if 'biometric_fingerprints' not in step.step_data:
                step.step_data['biometric_fingerprints'] = {}
            step.step_data['biometric_fingerprints'][finger_type] = result
            step.save()

            return JsonResponse({'success': True, 'result': result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

