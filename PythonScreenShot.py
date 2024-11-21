"""
Python Screenshot - Make a screenshot from a SCPI resource

This application provides a GUI interface to capture screenshots from various SCPI instruments.
It supports multiple instrument types and can be configured via YAML files.

Copyright (C) 2020-2024 DL1DWG
License: GNU General Public License v3
Author: DL1DWG

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

###############################################################################
#                                                                             #
# PythonScreenShot - Make a screenshort from a SCPI resource                  #
#                                                                             #
#                    V1.6 DIPL.ING.W.GRIEBEL  JUN 2020                        #
#                                                                             #
###############################################################################

# Standard library imports
import os
import sys
import csv
import time
import shutil
from typing import Dict, List, Optional, Union

# Third-party imports
import yaml
import array
import numpy
import pyvisa
import logging
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtWidgets import (
    QWidget,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QSizePolicy
)
from PySide6.QtGui import (
    QPixmap,
    QImage,
    QIcon,
    QPainter
)
from PySide6.QtCore import (
    Qt,
    QTimer,
    QFile,
    QSize,
)
from PySide6.QtUiTools import QUiLoader

def get_file_inside_exe(file_name):
    return os.path.join(os.path.dirname(__file__), file_name)

def get_file_near_exe(file_name):
    file_path = ""
    try:
        file_path = os.path.join(__compiled__.containing_dir, file_name)
    except NameError:
        file_path = os.path.join(os.path.dirname(sys.argv[0]), file_name)
    return file_path

# Configure logging
is_compiled = "__compiled__" in globals()

if not is_compiled:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("screenshot.log"),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("screenshot.log")
        ]
    )

logging.info(f"Starting application (Compiled: {is_compiled})")

# Constants
SCREENSHOT_EXTENSIONS = ['.PNG', '.BMP', '.JPG']
DEFAULT_CHUNK_SIZE = 8000
DEFAULT_TIMEOUT = 30000
INSTRUMENTS_CSV = get_file_near_exe('PythonScreenShotInstruments.CSV')
SCREENSHOT_CONFIG = get_file_near_exe('instrument_screenshots.yaml')
VERSION_CONFIG = get_file_inside_exe('version.yaml')

# Global variables
rm = pyvisa.ResourceManager()

# *************************************************************************** #
# Utility classes                                                             #
# *************************************************************************** #

class FileManager:
    """Handles file operations"""
    @staticmethod
    def delete_file(file_name: str) -> None:
        """Delete a file if it exists"""
        try:
            os.remove(file_name)
        except OSError:
            pass

    @staticmethod
    def write_binary_file(data: Union[bytes, bytearray], file_name: str) -> None:
        """Write binary data to file"""
        with open(file_name, 'wb') as file_handle:
            file_handle.write(data)

    @staticmethod
    def cleanup_screenshots() -> None:
        """Delete existing screenshot files"""
        for ext in SCREENSHOT_EXTENSIONS:
            FileManager.delete_file(f'SCREENSHOT{ext}')

class VersionManager:
    """Manages application version information"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VersionManager, cls).__new__(cls)
            cls._instance._load_version_info()
        return cls._instance
    
    def _load_version_info(self) -> None:
        """Load version information from YAML file"""
        try:
            
            with open(VERSION_CONFIG, 'r') as f:
                self.version_info = yaml.safe_load(f)
            logging.debug(f"Loaded version info from {VERSION_CONFIG}")
        except Exception as e:
            logging.error(f"Error loading version info: {e}", exc_info=True)
            self.version_info = {
                'version': '1.5',
                'release_date': '2020/06',
                'author': 'DL1DWG',
                'license': 'GPL V3',
                'copyright_year': '2020',
                'app_name': 'Python Screenshot'
            }
            logging.warning("Using default version info due to loading error")
    
    @property
    def version_string(self) -> str:
        """Get formatted version string"""
        return f"V{self.version_info['version']} {self.version_info['release_date']}"
    
    @property
    def window_title(self) -> str:
        """Get formatted window title"""
        return (f"{self.version_info['author']} {self.version_info['app_name']} GUI "
                f"V{self.version_info['version']} {self.version_info['release_date']} "
                f"(C) {self.version_info['author']} under {self.version_info['license']}")

class InstrumentManager:
    """Manages instrument configurations and types"""
    def __init__(self):
        self.instrument_types: Dict[str, str] = {}
        self.screenshot_config: Dict[str, dict] = {}
        self._load_instrument_types()
        self._load_screenshot_config()

    def _load_instrument_types(self) -> None:
        """Load instrument types from CSV file"""
        try:
            name_list = []
            type_list = []
            with open(INSTRUMENTS_CSV, 'r', newline='') as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                headers = next(reader)
                for row in reader:
                    name_list.append(row[0])
                    type_list.append(row[1])
            self.instrument_types = dict(zip(name_list, type_list))
        except Exception as e:
            print(f"Error loading instrument types: {e}")

    def _load_screenshot_config(self) -> None:
        """Load screenshot configuration from YAML file"""
        try:
            with open(SCREENSHOT_CONFIG, 'r') as f:
                self.screenshot_config = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading screenshot config: {e}")

    def get_instrument_type(self, instr_name: str) -> str:
        """Get instrument type from instrument name"""
        return self.instrument_types.get(instr_name, '')

    def get_screenshot_config(self, instr_type: str) -> Optional[dict]:
        """Get screenshot configuration for instrument type"""
        return self.screenshot_config.get(instr_type)

class InstrumentCommunicator:
    """Handles communication with instruments"""
    @staticmethod
    def send_command(visa_id: str, command: str) -> str:
        """Send a SCPI command to instrument"""
        try:
            instr = rm.open_resource(visa_id, chunk_size=DEFAULT_CHUNK_SIZE, timeout=DEFAULT_TIMEOUT)
            instr.write(command)
            return 'OK'
        except Exception as e:
            print(f"Error sending command: {e}")
            return 'ERROR'

    @staticmethod
    def send_query(visa_id: str, command: str) -> str:
        """Send a SCPI query to instrument"""
        try:
            instr = rm.open_resource(visa_id, chunk_size=DEFAULT_CHUNK_SIZE, timeout=DEFAULT_TIMEOUT)
            result = instr.query(command, delay=0.5)
            return result
        except Exception as e:
            print(f"Error sending query: {e}")
            return ''

    @staticmethod
    def get_visa_resources() -> List[str]:
        """Get list of available VISA resources"""
        try:
            # get all VISA resources
            resourceList = rm.list_resources()
            visaList = []
            
            # check each resource if it is a SCPI resource
            for resource in resourceList:
                try:
                    instr = rm.open_resource(resource)
                    instr.write('*IDN?')
                    visaList.append(resource)
                except:
                    pass
                    
            return visaList
        except:
            return []

# *************************************************************************** #
# functions                                                                   #
# *************************************************************************** #

# =========================================================================== #
# get a screenshot depending on instrument type class                         #
# =========================================================================== #
def GetScreenShot(instrType, visaId):
    """Get screenshot from instrument using YAML configuration"""
    logging.info(f"Getting screenshot for instrument type: {instrType}, VISA ID: {visaId}")
    
    instrument_manager = InstrumentManager()
    config = instrument_manager.get_screenshot_config(instrType)
    
    if config is None:
        logging.warning(f"No configuration found for instrument type: {instrType}")
        # Handle special cases (like Arduino devices) that aren't in YAML
        if 'DL1DWG' in instrType:
            try:
                logging.info("Attempting Arduino device screenshot")
                instr = rm.open_resource(visaId, chunk_size=DEFAULT_CHUNK_SIZE, timeout=DEFAULT_TIMEOUT)
                result = GetArDeviceScreenShot(instr)
                return 'SCREENSHOT.PNG'
            except Exception as e:
                logging.error(f"Error getting Arduino screenshot: {e}")
                return ''
        return ''

    # Clean up existing files if needed
    logging.info("Cleaning up existing screenshot files")
    FileManager.cleanup_screenshots()
    
    try:
        # Connect to instrument
        logging.info(f"Connecting to instrument: {visaId}")
        instr = rm.open_resource(visaId, chunk_size=DEFAULT_CHUNK_SIZE, timeout=DEFAULT_TIMEOUT)
        
        # Execute pre-commands
        for cmd in config.get('commands', []):
            logging.info(f"Executing pre-command: {cmd}")
            InstrumentCommunicator.send_command(visaId, cmd)
        
        # Get screenshot data
        if config['query_type'] == 'binary_values':
            params = config.get('binary_params', {})
            datatype = params.get('datatype', 'B')
            container = params.get('container', 'bytearray')
            delay = params.get('delay', 0)
            
            logging.info(f"Getting binary values with params - datatype: {datatype}, container: {container}, delay: {delay}")
            
            # Convert string container type to actual type
            if isinstance(container, str):
                if container == 'bytearray':
                    container = bytearray
                elif container == 'list':
                    container = list
                elif container == 'array':
                    container = array
            
            logging.debug(f"Executing query command: {config['query_command']}")
            result = instr.query_binary_values(
                config['query_command'],
                datatype=datatype,
                container=container,
                delay=delay
            )
            if isinstance(result, bytearray):
                result = bytes(result)
        else:  # read_raw
            logging.info("Using read_raw to get screenshot data")
            result = instr.read_raw()
        
        # Determine filename and save
        fileName = f"SCREENSHOT.{config['file_type']}"
        logging.info(f"Saving screenshot to: {fileName}")
        FileManager.write_binary_file(result, fileName)
        return fileName
        
    except Exception as e:
        logging.error(f"Error getting screenshot: {str(e)}", exc_info=True)
        raise

# =========================================================================== #
# specialized screenshot routines for a device class go here                  #
# =========================================================================== #

# --------------------------------------------------------------------------- #
# get a screenshot from an ARDUINO SCPI device with a virtual display         #
# --------------------------------------------------------------------------- #
def GetArDeviceScreenShot(instr):

    # how many lines to read ?
    noOfLines = int(instr.query('*NLINES?',delay=0.2))
    
    # read all the lines
    lineList = []
    for i in range(noOfLines):
        scpiCommand = '*LTEXT? ' + str(i+1)
        lineReceived = instr.query(scpiCommand,delay=0.2).rstrip('\n').rstrip('\r')
        lineList.append(lineReceived)
        
    # OK, now we need to create a bitmap from the text. check line length
    maxLen = 0
    for i in range(noOfLines):
        maxLen = max(maxLen,len(lineList[i]))

    # some fitting heuristics
    fontSize  = 64
    imgSizeX  = int(maxLen * fontSize * 0.75) + 20
    imgSizeY  = int(noOfLines * fontSize * 1.3)
    textFont  = ImageFont.truetype(get_file_inside_exe('PythonScreenShotFont.ttf'),fontSize)
    
    # create image and draw space, set origin    
    img       = Image.new('RGB', (imgSizeX,imgSizeY), color = (73, 109, 137))
    drawSpace = ImageDraw.Draw(img)
    dOriginX  = 20
    dOriginY  = 20
    
    # write the text, adjust line spacing
    for i in range(noOfLines):
        drawSpace.text((dOriginX,dOriginY + int(i*fontSize*1.2)),lineList[i],font=textFont,fill=(255,255,0))

    # save image
    img.save('SCREENSHOT.PNG')

# --------------------------------------------------------------------------- #
# forge a screenshot for a RIGOL DP832 power supply - not needed anymore      #
# left in the code to provide an example how a screenshot can be made from    #
# raw data by painting it in a canvas area                                    #
# --------------------------------------------------------------------------- #
def GetRigolDP832DeviceScreenShot(instr):

    # collect the status of all channels
    statusList      = []
    setVoltageList  = []
    setCurrentList  = []
    msrVoltageList  = []
    msrCurrentList  = []
    msrPowerList    = []
    for i in range(3):
      statusList.append(instr.query('OUTP? CH' + str(i+1),delay=0.2).rstrip('\n').rstrip('\r')) 
      result = instr.query('APPL? CH' + str(i+1),delay=0.2).rstrip('\n').rstrip('\r').split(',')
      setVoltageList.append(float(result[1]))
      setCurrentList.append(float(result[2]))
      result = instr.query('MEAS:ALL? CH' + str(i+1),delay=0.2).rstrip('\n').rstrip('\r').split(',')
      msrVoltageList.append(float(result[0]))
      msrCurrentList.append(float(result[1]))
      msrPowerList.append(float(result[2]))

    # OK, now we need to create a bitmap with some fitting heuristics
    fontSize  = 64
    maxLen    = 20
    noOfLines = 7
    imgSizeX  = int(maxLen * fontSize * 0.75) + 20
    imgSizeY  = int(noOfLines * fontSize * 1.3)
    textFont  = ImageFont.truetype(get_file_inside_exe('PythonScreenShotFont.ttf'),fontSize)
    
    # create image and draw space, set origin    
    img       = Image.new('RGB', (imgSizeX,imgSizeY), color = (73, 109, 137))
    drawSpace = ImageDraw.Draw(img)
    dOriginX  = 20
    dOriginY  = 20
    dBlockShift = 5
    
    # write the text, adjust line spacing
    for i in range(3):
        drawSpace.text((dOriginX + int(i*dBlockShift*fontSize),dOriginY)             ,' CH' + str(i+1)                          ,font=textFont,fill=(255,255,0))
        drawSpace.text((dOriginX + int(i*dBlockShift*fontSize),dOriginY + 1*fontSize),' ' + statusList[i]                       ,font=textFont,fill=(255,255,0))
        drawSpace.text((dOriginX + int(i*dBlockShift*fontSize),dOriginY + 2*fontSize +30),str(round(setVoltageList[i],3)) + 'V' ,font=textFont,fill=(255,255,0))
        drawSpace.text((dOriginX + int(i*dBlockShift*fontSize),dOriginY + 3*fontSize +30),str(round(setCurrentList[i],3)) + 'A' ,font=textFont,fill=(255,255,0))
        drawSpace.text((dOriginX + int(i*dBlockShift*fontSize),dOriginY + 4*fontSize +60),str(round(msrVoltageList[i],3)) + 'V' ,font=textFont,fill=(255,255,0))
        drawSpace.text((dOriginX + int(i*dBlockShift*fontSize),dOriginY + 5*fontSize +60),str(round(msrCurrentList[i],3)) + 'A' ,font=textFont,fill=(255,255,0))
        drawSpace.text((dOriginX + int(i*dBlockShift*fontSize),dOriginY + 6*fontSize +90),str(round(msrPowerList[i],3))   + 'W' ,font=textFont,fill=(255,255,0))
    # save image
    img.save('SCREENSHOT.PNG')

# --------------------------------------------------------------------------- #
# forge a screenshot for a Keysight U2004A Power Sensor                       #
# --------------------------------------------------------------------------- #
def GetKeysightU2004ADeviceScreenShot(instr):

    # this is a special part full of bugs and timeouts.
    try:
        instr.write('*CLS')
        instr.write(':INIT:CONT ON')
        time.sleep(1)        
        result = float(instr.query(':FETCH?',delay=1))
    except:
        # try again. this behaviour could be due to an autocalibration 
        try:
            instr.write('*CLS')
            instr.write(':INIT:CONT ON')
            time.sleep(1)
            result = float(instr.query(':FETCH?',delay=1))
        except:
            pass

    # OK, now we need to create a bitmap with some fitting heuristics
    fontSize  = 64
    maxLen    = 12
    noOfLines = 1
    imgSizeX  = int(maxLen * fontSize * 0.75) + 20
    imgSizeY  = int(noOfLines * fontSize * 1.3)
    textFont  = ImageFont.truetype(get_file_inside_exe('PythonScreenShotFont.ttf'),fontSize)
    
    # create image and draw space, set origin    
    img       = Image.new('RGB', (imgSizeX,imgSizeY), color = (73, 109, 137))
    drawSpace = ImageDraw.Draw(img)
    dOriginX  = 20
    dOriginY  = 20
    
    # write the text
    drawSpace.text((dOriginX,dOriginY),str(round(result,5)) + ' dBm',font=textFont,fill=(255,255,0))
    
    # save image
    img.save('SCREENSHOT.PNG')

# =========================================================================== #
# VISA routines go here                                                       #
# =========================================================================== #

# --------------------------------------------------------------------------- #
# get all VISA resources responding to a *IDN? query                          #
# --------------------------------------------------------------------------- #
def GetVisaSCPIResources():

    # enumerate all resources VISA finds
    rm                  = pyvisa.ResourceManager()
    resourceList        = rm.list_resources()
    availableVisaIdList = []
    availableNameList   = []
    seen_resources = set()  # Track seen resources to prevent duplicates

    # go thru this list and ask an *IDN? to see what instrument it is
    for i in range(len(resourceList)):
        resourceReply = ''
        try:
            if (resourceList[i][:4] == 'ASRL'):         # serial resource
                instrument          = rm.open_resource(resourceList[i],
                                                        timeout=2000,
                                                        access_mode=1)
                # instrument.lock_excl()
                resourceReply       = instrument.query('*IDN?').upper()
            else:
                instrument          = rm.open_resource(resourceList[i])
                resourceReply       = instrument.query('*IDN?').upper()
            
            # Only add if we haven't seen this device before
            if (resourceReply != '' and resourceReply not in seen_resources):
                seen_resources.add(resourceReply)
                availableVisaIdList.append(resourceList[i])
                availableNameList.append(resourceReply)
        except:
            pass
            
    return availableVisaIdList, availableNameList

# --------------------------------------------------------------------------- #
# send a SCPI command                                                         #
# --------------------------------------------------------------------------- #
def SendScpiCommand(visaId,commandString):

    # first connect to the instrument
    instr = rm.open_resource(visaId,chunk_size=DEFAULT_CHUNK_SIZE,timeout=DEFAULT_TIMEOUT)

    try:
        instr.write(commandString)
        return 'OK'
    except:
        return 'SCPI Error'

# --------------------------------------------------------------------------- #
# send a SCPI query                                                           #
# --------------------------------------------------------------------------- #
def SendScpiQuery(visaId,commandString):

    # first connect to the instrument
    instr = rm.open_resource(visaId,chunk_size=DEFAULT_CHUNK_SIZE,timeout=DEFAULT_TIMEOUT)

    try:
        result = instr.query(commandString,delay=0.5)
        return result
    except:
        return 'SCPI Error'

# *************************************************************************** #
# GUI code starts here                                                        #
# *************************************************************************** #
class PythonScreenShot(QWidget):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.version_manager = VersionManager()
        self.nameList = []
        self.visaIdList = []
        self.timer = None
        self.interval = 1000
        
        # Load UI
        loader = QUiLoader()
        ui_file = QFile(get_file_inside_exe("mainwindow.ui"))
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file)
        ui_file.close()
        
        # Set up main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.ui)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ui.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Configure screenshot label
        self.ui.screenshotLabel.setMinimumSize(200, 200)
        self.ui.screenshotLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ui.screenshotLabel.setAlignment(Qt.AlignCenter)
        
        # Make sure the screenshot frame expands
        if hasattr(self.ui, 'screenshotFrame'):
            self.ui.screenshotFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set minimum window size
        self.setMinimumSize(800, 600)
        
        # Initialize UI elements
        self.initUI()

    def resizeEvent(self, event):
        """Handle main window resize events"""
        super().resizeEvent(event)
        self.updateScreenshot()

    def updateScreenshot(self):
        """Update the screenshot display"""
        try:
            if not hasattr(self, 'screenshotPixMap') or self.screenshotPixMap is None:
                return

            # Get the available space in the label
            available_size = self.ui.screenshotLabel.size()
            if available_size.width() <= 0 or available_size.height() <= 0:
                return

            # Calculate the scaled size maintaining aspect ratio
            pixmap_size = self.screenshotPixMap.size()
            scaled_size = pixmap_size.scaled(
                available_size.width(),
                available_size.height(),
                Qt.KeepAspectRatio
            )

            # Create a new pixmap with the background color
            result_pixmap = QPixmap(available_size)
            result_pixmap.fill(Qt.white)

            # Calculate position to center the image
            x = (available_size.width() - scaled_size.width()) // 2
            y = (available_size.height() - scaled_size.height()) // 2

            # Draw the scaled image onto the background
            painter = QPainter(result_pixmap)
            painter.drawPixmap(
                x, y,
                scaled_size.width(),
                scaled_size.height(),
                self.screenshotPixMap
            )
            painter.end()

            # Set the final pixmap
            self.ui.screenshotLabel.setPixmap(result_pixmap)
            logging.debug(f"Updated screenshot to size: {scaled_size.width()}x{scaled_size.height()}")

        except Exception as e:
            logging.error(f"Error updating screenshot: {str(e)}", exc_info=True)

    def initUI(self):
        """Initialize the UI"""
        # Set version information
        self.setWindowTitle(self.version_manager.window_title)
        self.ui.headerTopZ.setText(self.version_manager.version_string)
        
        # Connect signals
        self.ui.doFindButton.clicked.connect(self.doFind)
        self.ui.doRefreshButton.clicked.connect(self.doSetRefresh)
        self.ui.doAutoRefreshButton.clicked.connect(self.doSetAutoRefresh)
        self.ui.doSaveButton.clicked.connect(self.doSave)
        self.ui.doSendClearButton.clicked.connect(self.doSendClear)
        self.ui.doSendResetButton.clicked.connect(self.doSendReset)
        self.ui.doGetLastErrorButton.clicked.connect(self.doSendGetLastError)
        self.ui.doRunButton.clicked.connect(self.doRun)
        self.ui.doSendCommandButton.clicked.connect(self.doSendCommand)
        
        # Initialize the UI state
        self.ui.instrTable.setColumnCount(4)
        self.ui.instrTable.setHorizontalHeaderLabels(['Name','Description','Manufacturer','VISA ID'])
        self.ui.instrTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ui.instrTable.setSelectionMode(QTableWidget.SingleSelection)
        self.ui.instrTable.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Load the SCPI dino image
        dino_path = get_file_inside_exe('SCPILogoDinosaur.png')
        self.scpiDinoPixMap = QPixmap(dino_path)
        if not self.scpiDinoPixMap.isNull():
            self.ui.scpiDinoLabel.setPixmap(self.scpiDinoPixMap)
            logging.info(f"Loaded SCPI dino image from {dino_path}")
        else:
            logging.error(f"Failed to load SCPI dino image from {dino_path}")
        
        # Initialize screenshot label with white background
        pixMap = QPixmap(1024, 800)
        pixMap.fill(Qt.white)
        self.ui.screenshotLabel.setPixmap(pixMap)
        
        # Set up resizing behavior
        self.ui.screenshotLabel.setScaledContents(True)
        
        self.show()

    def doFind(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.ui.doAutoRefreshButton.setChecked(False)
        try:
            self.ui.instrTable.clear()
            self.ui.instrTable.setHorizontalHeaderLabels(['Name','Description','Manufacturer','VISA ID'])
            self.visaIdList, self.nameList = GetVisaSCPIResources()
            self.ui.instrTable.setRowCount(len(self.nameList))
            for i in range(len(self.nameList)):
                nameListComps = self.nameList[i].split(',')
                mfgName       = nameListComps[0].strip()
                instrName     = nameListComps[1].strip()
                serialNo      = nameListComps[2].strip()
                versionText   = nameListComps[3].strip()
                instrType     = InstrumentManager().get_instrument_type(instrName)
                self.ui.instrTable.setItem(i,0,QTableWidgetItem(instrName))
                self.ui.instrTable.setItem(i,1,QTableWidgetItem(instrType))
                self.ui.instrTable.setItem(i,2,QTableWidgetItem(mfgName))
                self.ui.instrTable.setItem(i,3,QTableWidgetItem(self.visaIdList[i]))
            QApplication.restoreOverrideCursor()
        except:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("No Instruments  found.")
            msg.setInformativeText('See Log for More information')
            msg.setWindowTitle("Error")
            msg.exec()
        QApplication.restoreOverrideCursor()
        return    
   
    def doSetRefresh(self):
        itemList = self.ui.instrTable.selectedItems()
        if len(itemList) == 0:
            self.ui.doAutoRefreshButton.setChecked(False)
            return
        instrName = itemList[0].text().strip()
        instrType = itemList[1].text().strip()
        visaId    = itemList[3].text().strip()
        if instrType == '':
            # complain
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.imgFileName = GetScreenShot(instrType,visaId)
            self.screenshotPixMap = QPixmap(self.imgFileName)
            self.updateScreenshot()
            QApplication.restoreOverrideCursor()
        except:
            self.ui.doAutoRefreshButton.setChecked(False)
            QApplication.restoreOverrideCursor()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("SCPI Error")
            msg.setInformativeText('See Log for More information')
            msg.setWindowTitle("Error")
            msg.exec()
        return

    def doSendClear(self):
        itemList = self.ui.instrTable.selectedItems()
        if len(itemList) == 0:
            self.ui.doAutoRefreshButton.setChecked(False)
            return
        instrName = itemList[0].text().strip()
        instrType = itemList[1].text().strip()
        visaId    = itemList[3].text().strip()
        if instrType == '':
            # complain
            return
        self.ui.doAutoRefreshButton.setChecked(False)
        InstrumentCommunicator.send_command(visaId,'*CLS')
        self.ui.labelScpiReply.setText('')
        return

    def doSendReset(self):
        itemList = self.ui.instrTable.selectedItems()
        if len(itemList) == 0:
            self.ui.doAutoRefreshButton.setChecked(False)
            return
        instrName = itemList[0].text().strip()
        instrType = itemList[1].text().strip()
        visaId    = itemList[3].text().strip()
        if instrType == '':
            # complain
            return
        self.ui.doAutoRefreshButton.setChecked(False)
        InstrumentCommunicator.send_command(visaId,'*RST')
        self.ui.labelScpiReply.setText('')
        return

    def doRun(self):
        """Execute screenshot capture"""
        try:
            itemList = self.ui.instrTable.selectedItems()
            if len(itemList) == 0:
                logging.warning("No instrument selected")
                self.ui.doAutoRefreshButton.setChecked(False)
                return
            
            instrName = itemList[0].text().strip()
            visaId = itemList[3].text().strip()  # VISA ID is in column 3
            logging.info(f"Running screenshot for instrument: {instrName} ({visaId})")
            
            instrument_manager = InstrumentManager()
            instrType = instrument_manager.get_instrument_type(instrName)
            
            if not instrType:
                logging.error(f"No instrument type found for: {instrName}")
                raise Exception(f"Unknown instrument type for: {instrName}")
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            logging.info(f"Getting screenshot for type: {instrType}")
            
            self.imgFileName = GetScreenShot(instrType, visaId)
            if not self.imgFileName:
                raise Exception("Failed to get screenshot")
                
            logging.info(f"Loading screenshot from: {self.imgFileName}")
            self.screenshotPixMap = QPixmap(self.imgFileName)
            if self.screenshotPixMap.isNull():
                raise Exception("Failed to load screenshot image")
                
            self.updateScreenshot()
            QApplication.restoreOverrideCursor()
            
        except Exception as e:
            logging.error(f"Screenshot capture failed: {str(e)}", exc_info=True)
            self.ui.doAutoRefreshButton.setChecked(False)
            QApplication.restoreOverrideCursor()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("SCPI Error")
            msg.setInformativeText(f'Error: {str(e)}\nSee screenshot.log for more information')
            msg.setWindowTitle("Error")
            msg.exec()
        return

    def doSendGetLastError(self):
        itemList = self.ui.instrTable.selectedItems()
        if len(itemList) == 0:
            self.ui.doAutoRefreshButton.setChecked(False)
            return
        instrName = itemList[0].text().strip()
        instrType = itemList[1].text().strip()
        visaId    = itemList[3].text().strip()
        if instrType == '':
            # complain
            return
        self.ui.doAutoRefreshButton.setChecked(False)
        result = InstrumentCommunicator.send_query(visaId,':SYST:ERR?')
        self.ui.labelScpiReply.setText(result)
        return

    def doSendCommand(self):
        #print("sending command")
        itemList = self.ui.instrTable.selectedItems()
        if len(itemList) == 0:
            self.ui.doAutoRefreshButton.setChecked(False)
            return
        instrName = itemList[0].text().strip()
        instrType = itemList[1].text().strip()
        visaId    = itemList[3].text().strip()
        if instrType == '':
            # complain
            return
        self.ui.doAutoRefreshButton.setChecked(False)
        cmdText = self.ui.scpiCommandEntry.text().strip()
        #print(cmdText)
        if (len(cmdText) > 0):
            cmdTextParts = cmdText.split(' ')
            if cmdTextParts[0].endswith('?'):
                result = InstrumentCommunicator.send_query(visaId,cmdText)
                #print(result)
                self.ui.labelScpiReply.setText(result)
            else:
                result = InstrumentCommunicator.send_command(visaId,cmdText)
                #print(result)
        return

    def doSetAutoRefresh(self):
        self.interval = min(10000.,max(200.,int(self.ui.autoRefPeriodEntry.text())))
        if self.ui.doAutoRefreshButton.isChecked():
            self.timer = QTimer()
            # self.timer.setSingleShot(True)
            self.timer.setInterval(int(self.interval))
            self.timer.timeout.connect(self.sendRefMsg)
            self.timer.start()            
        else:
            self.timer.stop()
        return

    def sendRefMsg(self):
        self.doSetRefresh()
        return

    def doSave(self):
        options = QFileDialog.Options()
        newFileName, selectedFilter = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot as ...",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;BMP Files (*.bmp)",
            options=options
        )
        if newFileName and self.imgFileName:
            # Load the image using QPixmap
            pixmap = QPixmap(self.imgFileName)
            
            # Ensure the file has the correct extension based on the selected filter
            if selectedFilter == "PNG Files (*.png)" and not newFileName.lower().endswith('.png'):
                newFileName += '.png'
            elif selectedFilter == "JPEG Files (*.jpg)" and not newFileName.lower().endswith(('.jpg', '.jpeg')):
                newFileName += '.jpg'
            elif selectedFilter == "BMP Files (*.bmp)" and not newFileName.lower().endswith('.bmp'):
                newFileName += '.bmp'
            
            # Convert to the desired format
            if newFileName.lower().endswith(('.jpg', '.jpeg')):
                # For JPEG, we need to handle transparency by creating a white background
                image = QImage(pixmap.size(), QImage.Format_RGB32)
                image.fill(Qt.white)
                painter = QPainter(image)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                image.save(newFileName, "JPEG", 95)  # 95 is the quality
            else:
                # For PNG and BMP, we can save directly
                pixmap.save(newFileName, quality=100)
        return



# *************************************************************************** #
# main program code starts here                                               #
# *************************************************************************** #       
if __name__ == '__main__':
    
    app     = QApplication(sys.argv)
    app.setStyle('Windows')
    inst    = PythonScreenShot()
    sys.exit(app.exec())