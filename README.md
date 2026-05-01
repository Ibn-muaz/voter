# INEC Voter Registration System

An AI-powered voter registration system with underage detection.

## Quick Start (Windows)

Simply double-click the `run.bat` file in the root directory. This will:
1. Create a Python virtual environment.
2. Install all necessary dependencies.
3. Run database migrations.
4. Seed initial data (Nigerian States and LGAs).
5. Create an admin user (**admin** / **admin**).
6. Start the development server and open your browser to `http://127.0.0.1:8000/`.

## Access Info
- **Main App**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Panel**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Credentials**: `admin` / `admin`

## Manual Setup

If you prefer to set it up manually:

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Run migrations**:
   ```bash
   cd backend
   python manage.py migrate
   ```

4. **Start the server**:
   ```bash
   python manage.py runserver
   ```

## Features
- Multi-step registration wizard.
- AI-powered document verification.
- Biometric capture simulation.
- Automated underage detection.

## Troubleshooting

If the system fails to start or you encounter errors:

1. **Run Diagnostics**: Run `run.bat` and select **Option 6 (Run System Diagnostics)**.
2. **Check Architecture**: Ensure you have **64-bit Python 3.10+** installed. The AI components will not work on 32-bit Python.
3. **Missing C++ Libraries**: If you see errors about "DLL load failed", you likely need the [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe).
4. **Tesseract OCR**: Ensure Tesseract is installed. If `setup_dependencies.bat` couldn't install it, download it manually from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
5. **Logs**: Check `backend/logs/inec_voter.log` for detailed error messages.
