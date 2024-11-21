# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/Stefan/Downloads/pythonscreenshotv15/PythonScreenShot.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/Stefan/Downloads/pythonscreenshotv15/LEDCalculatorItalic.ttf', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/PythonScreenShotFont.ttf', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/PythonScreenShotFontBAK.ttf', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/PythonScreenShotInstruments.CSV', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/PythonScreenshotSeparator.PNG', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/SCPILogoDinosaur.ico', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/SCPILogoDinosaur.PNG', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/ScreenShotCourier.ttf', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/ScreenShotLCD.ttf', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/ScreenShotPixel.ttf', '.'), ('C:/Users/Stefan/Downloads/pythonscreenshotv15/ScreenShotTypeWriter.ttf', '.')],
    hiddenimports=['PyQt5'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PythonScreenShot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Stefan\\Downloads\\pythonscreenshotv15\\SCPILogoDinosaur.ico'],
)
