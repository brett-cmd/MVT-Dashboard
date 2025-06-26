# MVT-Dashboard Application Guide

## Application Overview
MVT-Dashboard is a GUI application built on top of the Mobile Verification Toolkit (MVT) that provides a user-friendly interface for conducting mobile device forensic analysis. It offers buttons and forms to save time and make MVT commands easier to use without remembering complex command-line arguments.

## Entry Point
- **Main launch command**: `python3 run_mvt_gui.py`
- **Entry point file**: `run_mvt_gui.py` - Simple wrapper that imports and runs `mvt_gui.main()`
- **Main application**: `mvt_gui.py` - Contains the full GUI application

## Application Structure

### Core Files
- `run_mvt_gui.py` - Application launcher
- `mvt_gui.py` - Main GUI application with all tabs and functionality  
- `mvt_pdf_generator.py` - PDF report generation module
- `requirements.txt` - Python dependencies
- `setup.py` - Installation script

### Demo/Test Files
- `demo_pdf_generation.py` - Demo script for PDF generation with sample data
- `test_pdf_generation.py` - Test script for PDF functionality

### Dependencies
- `mvt>=2.5.0` - Mobile Verification Toolkit
- `PyQt5>=5.15.4` - GUI framework
- `reportlab>=4.0.0` - PDF generation
- `matplotlib>=3.5.0` - Charts and visualizations

## GUI Structure

The application uses a tabbed interface with three main tabs:

### 1. iOS Analysis Tab (`IOSTab` class)
**Available Operations:**
- **Decrypt iOS Backup** - `mvt-ios decrypt-backup -d <output> [-p <password>] <backup_path>`
- **Extract Backup Key** - `mvt-ios extract-key [-p <password>] <backup_path>`
- **Check iOS Backup** - `mvt-ios check-backup [-o <output>] <backup_path>`
- **Check iOS Filesystem** - `mvt-ios check-fs [-o <output>] <fs_path>`
- **Check Backup with IOCs** - `mvt-ios check-backup --iocs <ioc_path> [--output <output>] <backup_path>`
- **Check File System for IOCs** - `mvt-ios check-fs --iocs <ioc_path> [--output <output>] <fs_path>`

**Configuration Fields:**
- Backup Path (directory browser)
- Output Path (directory browser)
- Backup Password (password field)

### 2. Android Analysis Tab (`AndroidTab` class)
**Available Operations:**
- **Download APKs** - `mvt-android download-apks -o <output> [-s <serial>] [-a]`
- **Check Device via ADB** - `mvt-android check-adb [-s <serial>] [-o <output>] [-n] [-p <password>]`
- **Check Bugreport** - `mvt-android check-bugreport [-o <output>] <bugreport_path>`
- **Check Android Backup** - `mvt-android check-backup [-o <output>] [-n] [-p <password>] <backup_path>`
- **Check AndroidQF** - `mvt-android check-androidqf [-o <output>] [-n] [-p <password>] <androidqf_path>`
- **Check Backup with IOCs** - `mvt-android check-backup --iocs <ioc_path> [--output <output>] [-s <serial>] [-n] [-p <password>] <target_path>`

**Configuration Fields:**
- Target Path (file/directory browser)
- Output Path (directory browser)
- Device Serial (optional)
- Backup Password (password field)
- Options: Download All APKs, Non-interactive Mode

### 3. Utilities Tab (`UtilitiesTab` class)
**Available Operations:**
- **Download/Update IOCs** - Downloads IOCs for both iOS and Android:
  - `mvt-ios download-iocs`
  - `mvt-android download-iocs`
- **Display MVT Version** - Shows version for both platforms:
  - `mvt-ios version`
  - `mvt-android version`
- **Update MVT** - Updates MVT to the latest version:
  - `pip install --upgrade mvt`

## Key Features

### Command Execution
- Uses `CommandRunner` class (QThread) for non-blocking command execution
- Real-time output display with ANSI color code conversion to HTML
- Progress indicators and button state management during operations
- Timestamped console output

### IOC Handling
- Default IOC path: `~/Library/Application Support/mvt/indicators`
- Automatic IOC path inclusion for IOC-enabled operations

### UI Features
- Dark theme styling with modern design
- Tabbed interface for organized functionality
- Real-time console output with syntax highlighting
- Progress bars and status indicators
- Clear console functionality
- File/directory browser integration

### PDF Report Generation
- Professional PDF reports with security analysis
- Executive summaries and detailed findings
- Device information and scan metadata
- Timeline analysis and recommendations
- Uses ReportLab and Matplotlib for generation

## Development Notes

### Styling
- Uses comprehensive dark theme CSS styling (`DARK_THEME` constant)
- Custom icons created programmatically
- Consistent button sizing and spacing

### Error Handling
- MVT installation verification on startup
- Input validation for required fields
- Process return code checking
- Exception handling in command execution

### Security Considerations
- This is a defensive security tool for mobile device forensic analysis
- Designed to detect potential compromise and malicious activity
- Used by security professionals for legitimate forensic purposes

## Usage Patterns

1. **Launch the application**: `python3 run_mvt_gui.py`
2. **Select appropriate tab** based on device type (iOS/Android) or utility needs
3. **Configure paths and options** using the GUI controls
4. **Execute operations** using the provided buttons
5. **Monitor progress** in the real-time console output
6. **Review results** in the output directory and console

The application simplifies MVT usage by providing an intuitive GUI interface while maintaining access to all core MVT functionality for mobile device security analysis.