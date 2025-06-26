# MVT GUI

A graphical user interface for the [Mobile Verification Toolkit (MVT)](https://github.com/mvt-project/mvt), which helps with conducting forensics of mobile devices to detect potential compromise.

## Overview

This GUI provides a user-friendly interface to MVT's command-line tools, making it easier to perform mobile device forensic analysis without having to remember complex command-line arguments. **NEW**: Now includes comprehensive PDF report generation for professional security analysis documentation.

![MVT GUI Screenshot](screenshot.png)

## Features

- **iOS Analysis**:
  - Decrypt iOS backups
  - Extract backup keys
  - Check iOS backups for signs of compromise
  - Analyze iOS filesystem dumps
  - Check for IOCs (Indicators of Compromise)
  - **NEW**: Generate professional PDF security reports

- **Android Analysis**:
  - Download APKs from connected devices
  - Check Android devices via ADB
  - Analyze Android bug reports
  - Check Android backups
  - Analyze AndroidQF acquisitions
  - Check for IOCs
  - **NEW**: Generate professional PDF security reports

- **PDF Report Generation** ✨:
  - Executive summary with security assessment
  - Device information and scan metadata
  - Security findings with IOC matches highlighted
  - Application analysis (App Store vs sideloaded apps)
  - Network activity analysis with suspicious process detection
  - Timeline of security events
  - Prioritized recommendations based on findings
  - Professional formatting suitable for technical documentation

- **Utilities**:
  - Download/update IOC databases
  - Check MVT version information

## Requirements

- Python 3.6 or newer
- Mobile Verification Toolkit (MVT)
- PyQt5
- **NEW**: ReportLab and Matplotlib (for PDF generation)

## Installation

1. First, ensure MVT is installed:
   ```
   pip3 install mvt
   ```

2. Install all dependencies:
   ```
   pip3 install -r requirements.txt
   ```
   
   Or install individually:
   ```
   pip3 install PyQt5 reportlab matplotlib
   ```

3. Download the MVT GUI:
   ```
   git clone https://github.com/yourusername/mvt-gui.git
   cd mvt-gui
   ```

4. Run the application:
   ```
   python3 mvt_gui.py
   ```

## Usage

### iOS Analysis

1. **Decrypt iOS Backup**:
   - Enter the backup path and destination
   - Provide the backup password if required
   - Click "Decrypt iOS Backup"

2. **Check iOS Backup**:
   - Select the backup path
   - Choose output location for results
   - Enable/disable fast mode and hash generation
   - Click "Check iOS Backup"

3. **Generate PDF Report** ✨:
   - After running any analysis that produces results
   - Click "📄 Generate PDF Report"
   - Professional report will be created in the output directory

### Android Analysis

1. **Connect to Device via ADB**:
   - Enter device serial (optional)
   - Click "Check Device via ADB"

2. **Download APKs**:
   - Set output path
   - Choose whether to download system APKs
   - Click "Download APKs"

3. **Generate PDF Report** ✨:
   - After running any analysis that produces results
   - Click "📄 Generate PDF Report"
   - Professional report will be created in the output directory

### PDF Report Features

The generated PDF reports include:

- **Executive Summary**: High-level security assessment with color-coded alerts
- **Device Information**: Complete device metadata and scan details
- **Security Findings**: Detailed analysis of IOC matches and suspicious activities
- **Application Analysis**: Breakdown of installed apps with security risk assessment
- **Network Analysis**: Process-level network activity with anomaly detection
- **Timeline**: Chronological view of security events
- **Recommendations**: Prioritized action items based on findings

### Demo Mode

Try the PDF generation feature with sample data:
```
python3 demo_pdf_generation.py
```

### Viewing Results

- Results will be displayed in the output console
- Detailed reports are saved to the selected output directory
- **NEW**: PDF reports provide comprehensive, shareable security analysis

## Dependencies

The application requires these Python packages:

- `mvt>=2.5.0` - Mobile Verification Toolkit
- `PyQt5>=5.15.4` - GUI framework
- `reportlab>=4.0.0` - PDF generation
- `matplotlib>=3.5.0` - Charts and visualizations

## Troubleshooting

- **MVT Not Found**: Ensure MVT is installed and in your PATH
- **ADB Connection Issues**: Verify USB debugging is enabled on your Android device
- **Permission Errors**: Make sure you have the necessary permissions to read/write to the selected directories
- **PDF Generation Errors**: Ensure reportlab and matplotlib are installed correctly
- **Missing PDF Button**: Install PDF dependencies with `pip install reportlab matplotlib`

## File Structure

```
mvt-gui/
├── mvt_gui.py                 # Main GUI application
├── mvt_pdf_generator.py       # PDF report generation module
├── demo_pdf_generation.py     # Demo script with sample data
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── CHANGELOG.md              # Version history
```

## License

This project is governed by the same license as MVT (MVT License 1.1).

## Credits

This GUI was created to simplify the use of the [Mobile Verification Toolkit](https://github.com/mvt-project/mvt) by Amnesty International Security Lab.

PDF report generation adds professional documentation capabilities for security analysis workflows.
