"""
Security utilities for the INEC system.
"""

import hashlib
import secrets
import string
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.files.base import ContentFile
import os


class SecurityUtils:
    """
    Security utilities for encryption, hashing, and file handling.
    """

    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Generate a cryptographically secure secret key."""
        return secrets.token_hex(length)

    @staticmethod
    def hash_file(file_content) -> str:
        """Generate SHA-256 hash of file content."""
        if hasattr(file_content, 'read'):
            # File-like object
            content = file_content.read()
            if hasattr(file_content, 'seek'):
                file_content.seek(0)  # Reset file pointer
        else:
            content = file_content

        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def encrypt_data(data: bytes, key: str = None) -> bytes:
        """Encrypt data using Fernet (AES)."""
        if key is None:
            key = settings.SECRET_KEY[:32].encode()  # Use Django secret key

        fernet_key = Fernet(base64.b64encode(key.ljust(32)[:32].encode()))
        return fernet_key.encrypt(data)

    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: str = None) -> bytes:
        """Decrypt data using Fernet (AES)."""
        if key is None:
            key = settings.SECRET_KEY[:32].encode()

        fernet_key = Fernet(base64.b64encode(key.ljust(32)[:32].encode()))
        return fernet_key.decrypt(encrypted_data)

    @staticmethod
    def generate_password(length: int = 12) -> str:
        """Generate a secure random password."""
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(characters) for _ in range(length))

    @staticmethod
    def validate_file_type(file, allowed_types: list) -> bool:
        """Validate file type against allowed MIME types."""
        if hasattr(file, 'content_type'):
            return file.content_type in allowed_types

        # Fallback: check file extension
        if hasattr(file, 'name'):
            extension = os.path.splitext(file.name)[1].lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
            }
            return mime_map.get(extension) in allowed_types

        return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent security issues."""
        # Remove path separators and dangerous characters
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext

        return filename

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
        """Mask sensitive data like ID numbers."""
        if len(data) <= visible_chars:
            return data

        masked_length = len(data) - visible_chars
        return '*' * masked_length + data[-visible_chars:]


class FileHandler:
    """
    Secure file handling utilities.
    """

    @staticmethod
    def save_encrypted_file(file_content, filename: str, encryption_key: str = None) -> ContentFile:
        """Save file with optional encryption."""
        if encryption_key:
            encrypted_content = SecurityUtils.encrypt_data(file_content, encryption_key)
        else:
            encrypted_content = file_content

        return ContentFile(encrypted_content, name=filename)

    @staticmethod
    def read_encrypted_file(file_path: str, encryption_key: str = None) -> bytes:
        """Read and decrypt file if encrypted."""
        with open(file_path, 'rb') as f:
            content = f.read()

        if encryption_key:
            return SecurityUtils.decrypt_data(content, encryption_key)

        return content

    @staticmethod
    def validate_file_integrity(file_path: str, expected_hash: str) -> bool:
        """Validate file integrity using hash."""
        with open(file_path, 'rb') as f:
            actual_hash = SecurityUtils.hash_file(f)

        return actual_hash == expected_hash


# Compliance utilities
class ComplianceUtils:
    """
    GDPR and NDPA compliance utilities.
    """

    @staticmethod
    def anonymize_personal_data(data: dict) -> dict:
        """Anonymize personal data for reporting."""
        anonymized = data.copy()

        # Mask sensitive fields
        sensitive_fields = ['phone_number', 'address', 'vin']
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = SecurityUtils.mask_sensitive_data(str(anonymized[field]))

        return anonymized

    @staticmethod
    def log_data_access(user, data_type: str, data_id: int, action: str):
        """Log data access for compliance."""
        from apps.audit.models import DataAccessLog
        from django.contrib.gis.geoip2 import GeoIP2

        # Get IP address (simplified)
        ip_address = '127.0.0.1'  # Would get from request

        DataAccessLog.objects.create(
            user=user,
            access_type=action,
            data_type=data_type,
            data_id=data_id,
            ip_address=ip_address,
            purpose='system_operation'
        )

    @staticmethod
    def check_retention_policy(data_age_days: int) -> bool:
        """Check if data should be retained based on age."""
        # Nigerian data protection law requires 7 years retention for some data
        max_retention_days = 2555  # 7 years
        return data_age_days <= max_retention_days


# CAPTCHA utilities (placeholder)
class CaptchaUtils:
    """
    CAPTCHA generation and validation.
    """

    @staticmethod
    def generate_captcha() -> tuple:
        """Generate a simple image CAPTCHA."""
        from PIL import Image, ImageDraw, ImageFont
        import io
        import random
        import base64

        # Generate random text
        text = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

        # Create image
        width, height = 150, 50
        image = Image.new('RGB', (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(image)

        # Draw random noise lines
        for _ in range(15):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line((x1, y1, x2, y2), fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)), width=1)

        # Draw text
        try:
            # Try common system fonts
            font_paths = [
                "C:\\Windows\\Fonts\\arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "arial.ttf"
            ]
            font = None
            for path in font_paths:
                if os.path.exists(path):
                    font = ImageFont.truetype(path, 28)
                    break
            if not font:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # Center text with some randomness
        for i, char in enumerate(text):
            char_pos = (20 + i * 20, 10 + random.randint(-5, 5))
            draw.text(char_pos, char, fill=(0, random.randint(0, 100), random.randint(100, 200)), font=font)

        # Save to buffer
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        image_data = buf.getvalue()

        return text, image_data

    @staticmethod
    def validate_captcha(user_input: str, expected: str) -> bool:
        """Validate CAPTCHA input."""
        return user_input.upper() == expected.upper()