import os
import sys
import platform
import subprocess
import json
import socket
from datetime import datetime

def check_python():
    print("[*] Checking Python environment...")
    version = sys.version
    bitness = platform.architecture()[0]
    executable = sys.executable
    
    print(f"    - Version: {version}")
    print(f"    - Bitness: {bitness}")
    print(f"    - Executable: {executable}")
    
    if "64bit" not in bitness:
        print("    [!] WARNING: You are using 32-bit Python. AI libraries (TensorFlow/DeepFace) require 64-bit Python.")
        return False, "32-bit Python detected"
    
    if sys.version_info < (3, 10):
        print("    [!] WARNING: Python 3.10+ is recommended.")
        return False, "Python version too old"
        
    return True, "OK"

def check_dependencies():
    print("[*] Checking package dependencies...")
    critical_packages = [
        "django", "tensorflow", "deepface", "cv2", "easyocr", "pytesseract", "numpy"
    ]
    results = {}
    all_ok = True
    
    for pkg in critical_packages:
        try:
            if pkg == "cv2":
                import cv2
                results[pkg] = f"OK ({cv2.__version__})"
            elif pkg == "pytesseract":
                import pytesseract
                results[pkg] = "OK (Imported)"
            else:
                module = __import__(pkg)
                results[pkg] = f"OK ({getattr(module, '__version__', 'Imported')})"
            print(f"    - {pkg}: {results[pkg]}")
        except ImportError as e:
            results[pkg] = f"MISSING ({str(e)})"
            print(f"    - {pkg}: [!] {results[pkg]}")
            all_ok = False
        except Exception as e:
            results[pkg] = f"ERROR ({str(e)})"
            print(f"    - {pkg}: [!!] {results[pkg]}")
            all_ok = False
            
    return all_ok, results

def check_system_binaries():
    print("[*] Checking system binaries...")
    binaries = {
        "tesseract": ["tesseract", "--version"]
    }
    results = {}
    
    for name, cmd in binaries.items():
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).decode()
            results[name] = "FOUND: " + output.split('\n')[0]
            print(f"    - {name}: {results[name]}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            results[name] = "NOT FOUND"
            print(f"    - {name}: [!] NOT FOUND. Please install Tesseract OCR.")
            
    return results

def check_connectivity():
    print("[*] Checking connectivity...")
    hosts = ["google.com", "pypi.org", "github.com"]
    results = {}
    
    for host in hosts:
        try:
            socket.gethostbyname(host)
            results[host] = "CONNECTED"
            print(f"    - {host}: OK")
        except socket.error:
            results[host] = "FAILED"
            print(f"    - {host}: [!] FAILED")
            
    return results

def run_diagnostics():
    report = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine()
        }
    }
    
    print("="*50)
    print(" INEC VOTER REGISTRATION SYSTEM - DIAGNOSTICS")
    print("="*50)
    print(f"Time: {report['timestamp']}")
    print(f"OS: {report['system']['os']} {report['system']['release']}")
    print("-"*50)
    
    py_ok, py_msg = check_python()
    report["python"] = {"ok": py_ok, "message": py_msg}
    
    print("-"*50)
    dep_ok, dep_results = check_dependencies()
    report["packages"] = dep_results
    
    print("-"*50)
    report["binaries"] = check_system_binaries()
    
    print("-"*50)
    report["connectivity"] = check_connectivity()
    
    print("-"*50)
    
    # Save report
    report_file = "diag_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=4)
    
    print(f"\n[SUCCESS] Diagnostic report saved to {report_file}")
    print("="*50)
    
    if not py_ok or not dep_ok:
        print("\n[!] SUGGESTIONS:")
        if not py_ok:
            print("    - Reinstall Python using the 64-bit installer from python.org.")
        if "MISSING" in str(dep_results):
            print("    - Run 'run.bat' and select option 2 (Setup Dependencies).")
        if report["binaries"].get("tesseract") == "NOT FOUND":
            print("    - Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
    else:
        print("\n[*] Environment looks good. If you still have issues, check the server logs in 'backend/logs/'.")

if __name__ == "__main__":
    run_diagnostics()
