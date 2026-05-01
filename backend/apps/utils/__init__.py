"""
INEC Underage Eradicator - Utils App
Provides utility functions and data for the system.
"""

default_app_config = 'apps.utils.apps.UtilsConfig'

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == 'SecurityUtils':
        from .security import SecurityUtils
        return SecurityUtils
    elif name == 'FileHandler':
        from .security import FileHandler
        return FileHandler
    elif name == 'ComplianceUtils':
        from .security import ComplianceUtils
        return ComplianceUtils
    elif name == 'CaptchaUtils':
        from .security import CaptchaUtils
        return CaptchaUtils
    elif name == 'FakeDataGenerator':
        from .fake_data_generator import FakeDataGenerator
        return FakeDataGenerator
    elif name == 'TVCGenerator':
        from .pdf_generator import TVCGenerator
        return TVCGenerator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")