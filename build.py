#!/usr/bin/env python3
"""
Build script for Python Screenshot application using Nuitka
"""

import os
import sys
import yaml
import glob
import logging
import subprocess
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build.log'),
        logging.StreamHandler()
    ]
)

def load_version_info():
    """Load version information from version.yaml"""
    try:
        with open('version.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load version info: {e}")
        raise

def get_data_file_args():
    """Get data file arguments for Nuitka"""
    args = []
    
    try:
        # Add YAML files that should be included in the executable
        args.append("--include-data-files=version.yaml=version.yaml")
        args.append("--include-data-files=mainwindow.ui=mainwindow.ui")
        args.append("--include-data-files=PythonScreenShotFont.ttf=PythonScreenShotFont.ttf")
        
        # Add icon files
        if os.path.exists("SCPILogoDinosaur.ico"):
            args.append("--include-data-files=SCPILogoDinosaur.ico=SCPILogoDinosaur.ico")
            logging.info("ICO file found and included")
        else:
            logging.warning("ICO file not found")
            
        if os.path.exists("SCPILogoDinosaur.png"):
            args.append("--include-data-files=SCPILogoDinosaur.png=SCPILogoDinosaur.png")
            logging.info("PNG file found and included")
        else:
            logging.warning("PNG file not found")
        
        logging.info(f"Data files to be included: {args}")
        return args
    except Exception as e:
        logging.error(f"Error preparing data file arguments: {e}")
        raise

def build_application():
    """Build the application using Nuitka"""
    try:
        version_info = load_version_info()
        version = version_info['version']
        
        # Get data file arguments
        data_file_args = get_data_file_args()
        
        # Build the command as a single list
        cmd_parts = [
            sys.executable,
            "-m",
            "nuitka",
            "--standalone",
            "--onefile",
            "--follow-imports",
            "--plugin-enable=pyside6",
            "--enable-plugin=pyside6",
            "--python-flag=-O",  # Remove docstrings
            "--remove-output",  # Remove build directory after compilation
            "--windows-console-mode=attach",  # Attach console for GUI app
            "--nofollow-import-to=tkinter,matplotlib",  # Exclude unused large packages
            "--include-package-data=PySide6",  # Only include necessary PySide6 data
            "--include-qt-plugins=platforms,styles",  # Only include necessary Qt plugins
            "--include-package=PySide6.QtCore",
            "--include-package=PySide6.QtGui",
            "--include-package=PySide6.QtWidgets",
            "--include-package=shiboken6",
            "--include-package=numpy",  # Include numpy as it's required
            "--report=compilation-report.xml"
        ]
        
        # Add data files
        cmd_parts.extend(data_file_args)
        
        # Add Windows metadata
        cmd_parts.extend([
            "--windows-company-name=DL1DWG",
            f"--windows-product-version={version}",
            f"--windows-file-version={version}",
            f"--windows-product-name={version_info['app_name']}",
            f"--windows-file-description={version_info['app_name']} V{version}"
        ])
        
        # Add icon if it exists
        if os.path.exists("SCPILogoDinosaur.ico"):
            cmd_parts.append("--windows-icon-from-ico=SCPILogoDinosaur.ico")
        
        # Add output configuration
        cmd_parts.extend([
            "--output-dir=dist",
            f"--output-filename=PythonScreenShot_v{version}",
            "--verbose",
            "--show-modules",
            "--show-progress"
        ])
        
        # Add the main Python file as the ONLY positional argument
        cmd_parts.append("PythonScreenShot.py")
        
        # Create output directory if it doesn't exist
        os.makedirs("dist", exist_ok=True)
        
        # Log the full command for debugging
        logging.info("Build command: %s", " ".join(cmd_parts))
        
        # Run Nuitka compilation
        logging.info(f"Building Python Screenshot v{version}...")
        
        logging.info("Starting Nuitka process...")
        # Run process with direct console output
        try:
            process = subprocess.Popen(
                cmd_parts,
                stdout=None,
                stderr=None,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Wait for the process to complete
            return_code = process.wait()
            
            if return_code == 0:
                logging.info("Build completed successfully!")
                # Copy external files next to the executable
                exe_dir = "dist"
                external_files = [
                    'instrument_screenshots.yaml',
                    'PythonScreenShotInstruments.CSV'
                ]
                for file in external_files:
                    if os.path.exists(file):
                        shutil.copy2(file, os.path.join(exe_dir, file))
                        logging.info(f"Copied {file} to dist directory")
                    else:
                        logging.warning(f"External file {file} not found")
            else:
                logging.error(f"Build failed with return code {return_code}")
                raise subprocess.CalledProcessError(return_code, cmd_parts)
        except subprocess.TimeoutExpired:
            logging.error("Build process timed out")
            process.kill()
            raise
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Build failed with error code {e.returncode}")
        if e.stdout:
            logging.error("Build output:\n%s", e.stdout)
        if e.stderr:
            logging.error("Build errors:\n%s", e.stderr)
        raise
    except Exception as e:
        logging.error(f"Unexpected error during build: {e}")
        raise

if __name__ == "__main__":
    try:
        build_application()
    except Exception as e:
        logging.error(f"Build failed: {e}")
        sys.exit(1)