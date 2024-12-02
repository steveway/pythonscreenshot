"""
Script to compile Qt translation files (.ts) to binary format (.qm)
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

def find_lrelease():
    """Find the lrelease executable."""
    base_dir = Path(__file__).resolve().parent
    venv_dir = base_dir / ".venv"
    
    # Common paths for lrelease
    possible_paths = [
        base_dir / ".venv" / "Lib" / "site-packages" / "PySide6" / "lrelease.exe",
        venv_dir / "Scripts" / "lrelease.exe",
        Path("lrelease"),  # If in PATH
        Path(r"C:\Qt\6.5.2\msvc2019_64\bin\lrelease.exe"),
        Path(r"C:\Qt\Tools\QtCreator\bin\lrelease.exe"),
    ]
    
    print("Searching for lrelease in:")
    for path in possible_paths:
        abs_path = path.resolve() if not path.is_absolute() else path
        print(f"  Checking {abs_path}")
        
        if abs_path.exists():
            print(f"Found lrelease at: {abs_path}")
            return str(abs_path)
        else:
            print(f"  Path does not exist")
    
    return None

def compile_translations():
    """Compile all .ts files to .qm files"""
    base_dir = Path(__file__).resolve().parent
    translations_dir = base_dir / "resources" / "translations"
    
    print(f"\nBase directory: {base_dir}")
    print(f"Translations directory: {translations_dir}")
    
    if not translations_dir.exists():
        print(f"Error: Translations directory not found at {translations_dir}")
        return False
    
    # Create translations directory if it doesn't exist
    translations_dir.mkdir(parents=True, exist_ok=True)
    
    lrelease = find_lrelease()
    if not lrelease:
        print("Error: Could not find lrelease. Please install Qt tools or add it to PATH")
        print("You can download Qt tools from: https://www.qt.io/download")
        return False
    
    success = True
    for ts_file in translations_dir.glob("*.ts"):
        qm_file = ts_file.with_suffix(".qm")
        print(f"\nCompiling {ts_file.name} to {qm_file.name}")
        print(f"Input file exists: {ts_file.exists()}")
        print(f"Input file size: {ts_file.stat().st_size} bytes")
        
        cmd = [lrelease, str(ts_file), "-qm", str(qm_file)]
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Successfully compiled {ts_file.name} to {qm_file.name}")
            print("Output:")
            print(result.stdout)
            
            if qm_file.exists():
                print(f"Output file size: {qm_file.stat().st_size} bytes")
            else:
                print("Warning: Output file was not created")
                success = False
                
        except subprocess.CalledProcessError as e:
            print(f"Error compiling {ts_file.name}:")
            print(f"Exit code: {e.returncode}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            success = False
    
    return success

if __name__ == "__main__":
    if compile_translations():
        print("\nAll translations compiled successfully!")
    else:
        print("\nError compiling translations")
        sys.exit(1)
