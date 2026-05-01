import sys
import os

def is_venv():
    # Standard check for virtual environment
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )

if __name__ == "__main__":
    if not is_venv():
        print("[ERROR] Not running in a virtual environment.")
        sys.exit(1)
    
    try:
        import django
        print(f"[OK] Django {django.get_version()} detected.")
    except ImportError:
        print("[ERROR] Django not found in current environment.")
        sys.exit(1)
        
    sys.exit(0)
