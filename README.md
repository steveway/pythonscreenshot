# Python Screenshot

A GUI application to capture screenshots from various SCPI instruments. The application supports multiple instrument types and can be configured via YAML files.

## Copyright

Copyright (C) 2020-2024 DL1DWG  
License: GNU General Public License v3  
Author: DL1DWG

## Description

PythonScreenShot is a tool that allows you to make screenshots from SCPI resources. It provides a graphical user interface for easy interaction with various instrument types.

## Features

- Support for multiple instrument types including:
  - Batronix Magnova Oscilloscopes
  - Siglent Spectrum Analysers
  - Various SCPI-compatible instruments
- Configurable via YAML files for easy instrument configuration
- Modern GUI interface with:
  - Improved layout and scaling
  - Responsive image handling
  - Better user experience
- Automatic resource discovery
- Customizable screenshot capture settings
- Code improvements:
  - Refactored codebase for better maintainability
  - Enhanced error handling
  - Improved performance

## Changelog

| Date       | Changes                                                       | Author |
|------------|---------------------------------------------------------------|--------|
| 2020-04-24 | Initial release                                               | DIWG   |
| 2020-04-26 | Added DL3021A support                                         | DIWG   |
| 2020-04-28 | Added DP832 support (Thanks Peter Dreisiebner!)               | DIWG   |
| 2020-05-01 | Added RUN Button                                              | DIWG   |
| 2020-06-02 | Added additional instruments                                  | DIWG   |
| 2020-06-29 | Added Keysight DSOX1102                                       | JWU    |
| 2020-06-29 | Added all Keysight DSOS and DSOX1000 models                   | DIWG   |
| 2020-06-29 | Converted hardcoded dictionary to CSV loadable dataframe      | DIWG   |
| 2024-11-20 | Added YAML configuration support                              | Stefan Murawski  |
| 2024-11-20 | Improved GUI layout and image scaling                         | Stefan Murawski  |
| 2024-11-20 | Added support for Batronix Magnova Oscilloscopes              | Stefan Murawski  |
| 2024-11-20 | Added support for Siglent Spectrum Analysers                  | Stefan Murawski  |
| 2024-11-20 | General code refactoring and improvements                     | Stefan Murawski  |

## Compilation

The project includes a dedicated build script (`build.py`) that handles the Nuitka compilation process. To build the application:

```bash
python build.py
```

The build script:
- Automatically includes all necessary data files (YAML configs, UI files, CSV files)
- Configures proper PySide6 and Qt plugin inclusion
- Sets up Windows metadata and icons
- Optimizes the build for size and performance
- Creates a standalone executable in the `dist` directory

The resulting executable will be named `PythonScreenShot_v{version}` based on the version information in `version.yaml`.

## Dependencies

- PySide6
- PyVISA
- Pillow (PIL)
- PyYAML
- NumPy

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
