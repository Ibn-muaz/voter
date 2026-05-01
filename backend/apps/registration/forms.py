"""
Forms for the voter registration system.
Implements multi-step registration wizard following INEC Form EC1A.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import VoterRegistration, RegistrationStep, TemporaryVoterCard
from apps.utils.models import NigerianState, LocalGovernmentArea
from apps.utils.security import SecurityUtils
import re


class PersonalInfoForm(forms.ModelForm):
    """
    Step 1: Personal Information Form
    Collects basic personal details and validates Nigerian identity.
    """

    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'YYYY-MM-DD'
        }),
        help_text="Enter your date of birth (must be 18+ years old)",
        required=False
    )

    confirm_date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'Confirm date of birth'
        }),
        help_text="Re-enter your date of birth for verification",
        required=False
    )

    state_of_origin = forms.ModelChoiceField(
        queryset=NigerianState.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    lga_of_origin = forms.ModelChoiceField(
        queryset=LocalGovernmentArea.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = VoterRegistration
        fields = [
            'first_name', 'middle_name', 'surname', 'date_of_birth',
            'gender', 'occupation', 'phone_number', 'state_of_origin',
            'lga_of_origin', 'ward', 'polling_unit', 'residence_address'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name',
                'maxlength': 100
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your middle name (optional)',
                'maxlength': 100
            }),
            'surname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your surname',
                'maxlength': 100
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your occupation',
                'maxlength': 100
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+234XXXXXXXXXX',
                'maxlength': 15
            }),
            'ward': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ward name',
                'maxlength': 100
            }),
            'polling_unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Polling unit code',
                'maxlength': 100
            }),
            'residence_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Full residential address'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'state_of_origin' in self.data:
            try:
                state_id = int(self.data.get('state_of_origin'))
                self.fields['lga_of_origin'].queryset = LocalGovernmentArea.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.state_of_origin:
            self.fields['lga_of_origin'].queryset = self.instance.state_of_origin.lgas.order_by('name')

    def clean_phone_number(self):
        """Validate Nigerian phone number format."""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove spaces and hyphens
            phone = re.sub(r'[\s\-]', '', phone)

            # Check Nigerian number patterns
            nigerian_patterns = [
                r'^\+234[789]\d{9}$',  # +234 format
                r'^234[789]\d{9}$',     # 234 format
                r'^0[789]\d{9}$',       # 0 format
            ]

            if not any(re.match(pattern, phone) for pattern in nigerian_patterns):
                raise ValidationError("Please enter a valid Nigerian phone number.")

            # Normalize to +234 format
            if phone.startswith('0'):
                phone = '+234' + phone[1:]
            elif phone.startswith('234'):
                phone = '+' + phone

        return phone

    def clean_date_of_birth(self):
        """Validate age is 18+."""
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = timezone.now().date()
            age = (today - dob).days // 365

            if age < 18:
                raise ValidationError("You must be at least 18 years old to register to vote.")

            if age > 120:
                raise ValidationError("Please enter a valid date of birth.")

        return dob

    def clean(self):
        """Validate date of birth confirmation."""
        cleaned_data = super().clean()
        dob = cleaned_data.get('date_of_birth')
        confirm_dob = cleaned_data.get('confirm_date_of_birth')

        if dob and confirm_dob and dob != confirm_dob:
            raise ValidationError("Date of birth confirmation does not match.")

        return cleaned_data


class DocumentUploadForm(forms.ModelForm):
    """
    Step 2: Document Upload Form
    Handles upload and validation of identity documents.
    """

    proof_of_age_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload birth certificate, school certificate, or other proof of age (PDF, JPG, PNG)"
    )

    proof_of_identity_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload national ID, driver's license, or passport (PDF, JPG, PNG)"
    )

    proof_of_address_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload utility bill, bank statement, or affidavit (PDF, JPG, PNG)"
    )

    class Meta:
        model = VoterRegistration
        fields = [
            'proof_of_age_document', 'proof_of_identity_document',
            'proof_of_address_document'
        ]

    def clean_proof_of_age_document(self):
        """Validate proof of age document."""
        return self._validate_document_file(
            self.cleaned_data.get('proof_of_age_document'),
            'proof_of_age_document'
        )

    def clean_proof_of_identity_document(self):
        """Validate proof of identity document."""
        return self._validate_document_file(
            self.cleaned_data.get('proof_of_identity_document'),
            'proof_of_identity_document'
        )

    def clean_proof_of_address_document(self):
        """Validate proof of address document."""
        return self._validate_document_file(
            self.cleaned_data.get('proof_of_address_document'),
            'proof_of_address_document'
        )

    def _validate_document_file(self, file, field_name):
        """Common document validation."""
        if not file:
            return file

        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError(f"{field_name} file size must be less than 5MB.")

        # Validate file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
        if not SecurityUtils.validate_file_type(file, allowed_types):
            raise ValidationError(
                f"{field_name} must be a PDF, JPG, or PNG file."
            )

        return file


class BiometricCaptureForm(forms.Form):
    """
    Step 3: Biometric Capture Form
    Handles fingerprint and facial image capture.
    """

    fingerprint_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': 'image/*',
            'capture': 'user'  # For mobile camera
        }),
        help_text="Capture or upload fingerprint image"
    )

    facial_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': 'image/*',
            'capture': 'user'  # For mobile camera
        }),
        help_text="Take a clear facial photo"
    )

    consent_given = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="I consent to biometric data collection and processing"
    )

    def clean_fingerprint_image(self):
        """Validate fingerprint image."""
        return self._validate_biometric_image(
            self.cleaned_data.get('fingerprint_image'),
            'fingerprint_image'
        )

    def clean_facial_image(self):
        """Validate facial image."""
        return self._validate_biometric_image(
            self.cleaned_data.get('facial_image'),
            'facial_image'
        )

    def _validate_biometric_image(self, image, field_name):
        """Common biometric image validation."""
        if not image:
            return image

        # Check file size (max 2MB)
        if image.size > 2 * 1024 * 1024:
            raise ValidationError(f"{field_name} file size must be less than 2MB.")

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png']
        if not SecurityUtils.validate_file_type(image, allowed_types):
            raise ValidationError(
                f"{field_name} must be a JPG or PNG image."
            )

        return image


class ReviewAndSubmitForm(forms.Form):
    """
    Step 4: Review and Submit Form
    Final review and consent before submission.
    """

    declaration = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="I declare that all information provided is true and correct to the best of my knowledge"
    )

    data_processing_consent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="I consent to the processing of my personal data in accordance with Nigerian data protection laws"
    )

    captcha_input = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter CAPTCHA text'
        }),
        help_text="Enter the text shown in the CAPTCHA image"
    )

    def __init__(self, *args, **kwargs):
        self.expected_captcha = kwargs.pop('expected_captcha', '')
        super().__init__(*args, **kwargs)

    def clean_captcha_input(self):
        """Validate CAPTCHA input."""
        captcha = self.cleaned_data.get('captcha_input')
        if not captcha:  # Allow empty if field is not required
            return captcha
        if captcha.upper() != self.expected_captcha.upper():
            raise ValidationError("CAPTCHA verification failed. Please try again.")
        return captcha


class RegistrationStepForm(forms.ModelForm):
    """
    Form for tracking registration steps.
    """

    class Meta:
        model = RegistrationStep
        fields = ['step_number', 'step_name', 'step_data']
        widgets = {
            'step_data': forms.HiddenInput(),
        }


class BulkRegistrationForm(forms.Form):
    """
    Form for bulk registration uploads (admin only).
    """

    csv_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file',
            'accept': '.csv'
        }),
        help_text="Upload CSV file with voter registration data"
    )

    def clean_csv_file(self):
        """Validate CSV file."""
        file = self.cleaned_data.get('csv_file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("CSV file size must be less than 10MB.")

            # Validate file type
            if not file.name.endswith('.csv'):
                raise ValidationError("File must be a CSV file.")

        return file


class RegistrationSearchForm(forms.Form):
    """
    Form for searching existing registrations.
    """

    search_type = forms.ChoiceField(
        choices=[
            ('vin', 'VIN'),
            ('phone', 'Phone Number'),
            ('name', 'Name'),
            ('polling_unit', 'Polling Unit'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='vin'
    )

    search_value = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search value'
        })
    )

    def clean_search_value(self):
        """Validate search value based on type."""
        search_type = self.cleaned_data.get('search_type')
        value = self.cleaned_data.get('search_value')

        if search_type == 'vin' and not re.match(r'^[A-Z]{2}\d{10}$', value.upper()):
            raise ValidationError("VIN must be in format: AA1234567890")

        if search_type == 'phone':
            # Allow various phone formats
            value = re.sub(r'[\s\-]', '', value)
            if not re.match(r'^(\+234|234|0)[789]\d{9}$', value):
                raise ValidationError("Please enter a valid Nigerian phone number.")

        return value