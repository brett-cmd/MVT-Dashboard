#!/usr/bin/env python3
# MVT GUI - A graphical user interface for Mobile Verification Toolkit
# This is the main application file for the MVT GUI

import os
import sys
import subprocess
import json
import logging
import re
from pathlib import Path
from datetime import datetime
import base64
import shlex

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                                QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                                QFileDialog, QTextEdit, QComboBox, QCheckBox,
                                QMessageBox, QProgressBar, QTableWidget, QTableWidgetItem,
                                QGroupBox, QFormLayout, QLineEdit, QSpinBox, QFrame,
                                QSplitter, QToolButton)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
    from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QPen, QColor
except ImportError:
    print("PyQt5 is required. Please install it with: pip install PyQt5")
    sys.exit(1)

# PDF generation removed per user request
PDF_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MVT-GUI")

# Modern styling constants
DARK_THEME = """
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #363636;
}

QTabBar::tab {
    background-color: #404040;
    color: #ffffff;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #0078d4;
}

QTabBar::tab:hover {
    background-color: #505050;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #555555;
    border-radius: 8px;
    margin-top: 1ex;
    padding-top: 10px;
    background-color: #363636;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: #ffffff;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}

QLineEdit {
    background-color: #404040;
    border: 2px solid #555555;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
    selection-background-color: #0078d4;
}

QLineEdit:focus {
    border-color: #0078d4;
}

QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 4px;
    color: #ffffff;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 10pt;
    selection-background-color: #0078d4;
}

QCheckBox {
    color: #ffffff;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 2px solid #555555;
    background-color: #404040;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

QCheckBox::indicator:checked:hover {
    background-color: #106ebe;
}

QLabel {
    color: #ffffff;
}

QProgressBar {
    border: 1px solid #555555;
    border-radius: 4px;
    text-align: center;
    background-color: #404040;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 3px;
}

QStatusBar {
    background-color: #404040;
    color: #ffffff;
    border-top: 1px solid #555555;
}

QComboBox {
    background-color: #404040;
    border: 2px solid #555555;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}

QComboBox:hover {
    border-color: #0078d4;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}
"""

def convert_ansi_to_html(text):
    """Convert ANSI color codes to HTML formatting for QTextEdit display"""
    # ANSI color code mapping to CSS colors
    ansi_colors = {
        # Standard colors
        '30': '#000000',  # Black
        '31': '#ff5555',  # Red
        '32': '#55ff55',  # Green  
        '33': '#ffff55',  # Yellow
        '34': '#5555ff',  # Blue
        '35': '#ff55ff',  # Magenta
        '36': '#55ffff',  # Cyan
        '37': '#ffffff',  # White
        # Bright colors
        '90': '#555555',  # Bright Black (Gray)
        '91': '#ff7777',  # Bright Red
        '92': '#77ff77',  # Bright Green
        '93': '#ffff77',  # Bright Yellow
        '94': '#7777ff',  # Bright Blue
        '95': '#ff77ff',  # Bright Magenta
        '96': '#77ffff',  # Bright Cyan
        '97': '#ffffff',  # Bright White
    }
    
    # Remove ANSI escape sequences for reset, bold, etc. and convert colors
    # Pattern matches ANSI escape sequences like \033[31m, \033[1;32m, etc.
    ansi_pattern = r'\033\[([\d;]+)m'
    
    def replace_ansi(match):
        codes = match.group(1).split(';')
        styles = []
        
        for code in codes:
            if code == '0':  # Reset
                return '</span>'
            elif code == '1':  # Bold
                styles.append('font-weight: bold')
            elif code in ansi_colors:  # Color codes
                styles.append(f'color: {ansi_colors[code]}')
        
        if styles:
            return f'<span style="{"; ".join(styles)}">'
        return ''
    
    # Convert ANSI codes to HTML
    html_text = re.sub(ansi_pattern, replace_ansi, text)
    
    # Ensure all opened spans are closed at the end
    open_spans = html_text.count('<span') - html_text.count('</span>')
    html_text += '</span>' * open_spans
    
    return html_text

def create_app_icon():
    """Create a simple application icon"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw background circle
    painter.setBrush(QColor(0, 120, 212))  # Microsoft blue
    painter.setPen(QPen(QColor(255, 255, 255), 2))
    painter.drawEllipse(4, 4, 56, 56)
    
    # Draw "MVT" text
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Arial", 14, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "MVT")
    
    painter.end()
    return QIcon(pixmap)

def create_button_icon(text, color="#0078d4"):
    """Create simple colored icons for buttons"""
    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 12, 12)
    painter.end()
    
    return QIcon(pixmap)

class CommandRunner(QThread):
    """Thread for running MVT commands without blocking the UI"""
    output_received = pyqtSignal(str)
    command_finished = pyqtSignal(int)
    
    def __init__(self, command_list, env=None):
        super().__init__()
        self.command_list = command_list
        self.env = env or os.environ.copy()
        
    def run(self):
        try:
            # Use unbuffered output and set proper environment
            env = self.env.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
            env['PYTHONIOENCODING'] = 'utf-8'  # Ensure proper encoding
            env['FORCE_COLOR'] = '1'  # Force color output in commands that support it
            env['TERM'] = 'xterm-256color'  # Set terminal type for color support
            
            process = subprocess.Popen(
                self.command_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=False,
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output in real-time
            output_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    # Keep the line as-is to preserve ANSI color codes, just remove trailing newline
                    line_clean = line.rstrip('\n\r')
                    if line_clean:
                        self.output_received.emit(line_clean)
                        output_lines.append(line_clean)
                process.stdout.close()
            
            # Wait for process completion and get return code
            return_code = process.wait()
            
            self.command_finished.emit(return_code)
            
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            self.output_received.emit(error_msg)
            import traceback
            self.output_received.emit(f"Full traceback: {traceback.format_exc()}")
            self.command_finished.emit(1)

class IOSTab(QWidget):
    """Tab for iOS device analysis"""
    
    def __init__(self):
        super().__init__()
        self.thread = None
        self.initUI()
        
    def initUI(self):
        # Main splitter for better layout
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top section with controls in horizontal layout
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(15)
        top_layout.setContentsMargins(15, 15, 15, 15)
        
        # Left side: iOS Operations Group - taking up about 33% of space
        operations_group = QGroupBox("iOS Operations")
        operations_layout = QVBoxLayout()
        operations_layout.setSpacing(6)
        
        # Create styled buttons
        self.decrypt_backup_btn = QPushButton("Decrypt iOS Backup")
        self.decrypt_backup_btn.setToolTip("Decrypt an encrypted iOS backup using the provided password")
        self.decrypt_backup_btn.setMaximumHeight(30)
        self.decrypt_backup_btn.clicked.connect(self.decrypt_backup)
        operations_layout.addWidget(self.decrypt_backup_btn)
        
        self.extract_key_btn = QPushButton("Extract Backup Key")
        self.extract_key_btn.setToolTip("Extract encryption key from iOS backup")
        self.extract_key_btn.setMaximumHeight(30)
        self.extract_key_btn.clicked.connect(self.extract_key)
        operations_layout.addWidget(self.extract_key_btn)
        
        self.check_backup_btn = QPushButton("Check iOS Backup")
        self.check_backup_btn.setToolTip("Analyze iOS backup for potential indicators of compromise")
        self.check_backup_btn.setMaximumHeight(30)
        self.check_backup_btn.clicked.connect(self.check_backup)
        operations_layout.addWidget(self.check_backup_btn)
        
        self.check_fs_btn = QPushButton("Check iOS Filesystem")
        self.check_fs_btn.setToolTip("Analyze iOS filesystem dump for potential threats")
        self.check_fs_btn.setMaximumHeight(30)
        self.check_fs_btn.clicked.connect(self.check_filesystem)
        operations_layout.addWidget(self.check_fs_btn)
        
        self.check_iocs_btn = QPushButton("Check Backup with IOCs")
        self.check_iocs_btn.setToolTip("Run full backup analysis with IOC checking enabled")
        self.check_iocs_btn.setMaximumHeight(30)
        self.check_iocs_btn.clicked.connect(self.check_iocs)
        operations_layout.addWidget(self.check_iocs_btn)
        
        self.check_fs_iocs_btn = QPushButton("Check File System for IOCs")
        self.check_fs_iocs_btn.setToolTip("Analyze iOS filesystem dump for IOCs and potential threats")
        self.check_fs_iocs_btn.setMaximumHeight(30)
        self.check_fs_iocs_btn.clicked.connect(self.check_fs_iocs)
        operations_layout.addWidget(self.check_fs_iocs_btn)
        
        
        operations_group.setLayout(operations_layout)
        
        # Right side: Options Group - taking up about 67% of space
        options_group = QGroupBox("Configuration")
        options_layout = QFormLayout()
        options_layout.setSpacing(8)
        
        # Backup Path with improved layout
        backup_container = QWidget()
        backup_layout = QHBoxLayout(backup_container)
        backup_layout.setContentsMargins(0, 0, 0, 0)
        
        self.backup_path = QLineEdit()
        self.backup_path.setPlaceholderText("Select iOS backup directory...")
        
        self.browse_backup_btn = QPushButton("Browse")
        self.browse_backup_btn.setMinimumWidth(80)
        self.browse_backup_btn.setMaximumHeight(30)
        self.browse_backup_btn.clicked.connect(lambda: self.browse_path(self.backup_path, True))
        
        backup_layout.addWidget(self.backup_path)
        backup_layout.addWidget(self.browse_backup_btn)
        options_layout.addRow("Backup Path:", backup_container)
        
        # Output Path
        output_container = QWidget()
        output_layout = QHBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output directory...")
        
        self.browse_output_btn = QPushButton("Browse")
        self.browse_output_btn.setMinimumWidth(80)
        self.browse_output_btn.setMaximumHeight(30)
        self.browse_output_btn.clicked.connect(lambda: self.browse_path(self.output_path, True))
        
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.browse_output_btn)
        options_layout.addRow("Output Path:", output_container)
        
        # Password field with better styling
        self.backup_password = QLineEdit()
        self.backup_password.setEchoMode(QLineEdit.Password)
        self.backup_password.setPlaceholderText("Enter backup password (if encrypted)")
        options_layout.addRow("Backup Password:", self.backup_password)
        
        options_group.setLayout(options_layout)
        
        # Add widgets to top layout horizontally with proper stretch factors
        top_layout.addWidget(operations_group, 1)  # 33% of space
        top_layout.addWidget(options_group, 2)     # 67% of space
        
        # Console output with improved styling - larger by default
        console_group = QGroupBox("Output Console")
        console_layout = QVBoxLayout()
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        self.console_output.setMinimumHeight(400)
        # Enable rich text to support HTML formatting for colors
        self.console_output.setAcceptRichText(True)
        
        # Add clear button for console
        console_controls = QWidget()
        console_controls_layout = QHBoxLayout(console_controls)
        console_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.clear_console_btn = QPushButton("Clear")
        self.clear_console_btn.setMinimumWidth(60)
        self.clear_console_btn.clicked.connect(self.clear_console)
        
        console_controls_layout.addStretch()
        console_controls_layout.addWidget(self.clear_console_btn)
        
        console_layout.addWidget(console_controls)
        console_layout.addWidget(self.console_output)
        
        # Progress indicator below console
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMaximumHeight(20)
        console_layout.addWidget(self.progress_bar)
        
        console_group.setLayout(console_layout)
        
        # Add to splitter with much more space for console
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(console_group)
        main_splitter.setSizes([200, 600])
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)
    
    def clear_console(self):
        """Clear the console output"""
        self.console_output.clear()
    
    def update_status(self, message, color="#ffffff"):
        """Update the progress bar text instead of status label"""
        if hasattr(self, 'progress_bar') and self.progress_bar.isVisible():
            self.progress_bar.setFormat(f"{message}")
    
    def show_progress(self, show=True):
        """Show or hide progress indicator"""
        if show:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.progress_bar.setFormat("Operation in progress...")
            # Disable operation buttons
            self.decrypt_backup_btn.setEnabled(False)
            self.extract_key_btn.setEnabled(False)
            self.check_backup_btn.setEnabled(False)
            self.check_fs_btn.setEnabled(False)
            self.check_iocs_btn.setEnabled(False)
            self.check_fs_iocs_btn.setEnabled(False)
        else:
            self.progress_bar.setVisible(False)
            # Re-enable operation buttons
            self.decrypt_backup_btn.setEnabled(True)
            self.extract_key_btn.setEnabled(True)
            self.check_backup_btn.setEnabled(True)
            self.check_fs_btn.setEnabled(True)
            self.check_iocs_btn.setEnabled(True)
            self.check_fs_iocs_btn.setEnabled(True)
    
    def browse_path(self, line_edit, is_dir=False):
        if is_dir:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
            
        if path:
            line_edit.setText(path)
    
    def decrypt_backup(self):
        if not self.backup_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a backup path")
            return
            
        if not self.output_path.text():
            QMessageBox.warning(self, "Input Required", "Please select an output path")
            return
            
        command_list = ["mvt-ios", "decrypt-backup", "-d", self.output_path.text()]
        
        if self.backup_password.text():
            command_list.extend(["-p", self.backup_password.text()]) # No shlex.quote for password
            
        command_list.append(self.backup_path.text())
        
        self.run_command(command_list)
    
    def extract_key(self):
        if not self.backup_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a backup path")
            return
            
        command_list = ["mvt-ios", "extract-key"]
        
        if self.backup_password.text():
            command_list.extend(["-p", self.backup_password.text()]) # No shlex.quote for password
            
        command_list.append(self.backup_path.text())
        
        self.run_command(command_list)
    
    def check_backup(self):
        if not self.backup_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a backup path")
            return
            
        command_list = ["mvt-ios", "check-backup"]
        
        if self.output_path.text():
            command_list.extend(["-o", self.output_path.text()])
            
        command_list.append(self.backup_path.text())
        
        self.run_command(command_list)
    
    def check_filesystem(self):
        if not self.backup_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a filesystem dump path")
            return
            
        command_list = ["mvt-ios", "check-fs"]
        
        if self.output_path.text():
            command_list.extend(["-o", self.output_path.text()])
            
        command_list.append(self.backup_path.text())
        
        self.run_command(command_list)
    
    def check_iocs(self):
        if not self.backup_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a backup path")
            return
            
        command_list = ["mvt-ios", "check-backup"]
        
        # Add --iocs flag with the default path
        ioc_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "mvt", "indicators")
        command_list.extend(["--iocs", ioc_path])
        
        if self.output_path.text():
            command_list.extend(["--output", self.output_path.text()])
        
        command_list.append(self.backup_path.text())
        
        self.run_command(command_list)
    
    def check_fs_iocs(self):
        if not self.backup_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a filesystem dump path")
            return
            
        command_list = ["mvt-ios", "check-fs"]
        
        # Add --iocs flag with the default path
        ioc_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "mvt", "indicators")
        command_list.extend(["--iocs", ioc_path])
        
        if self.output_path.text():
            command_list.extend(["--output", self.output_path.text()])
        
        command_list.append(self.backup_path.text())
        
        self.run_command(command_list)
    
    
    def run_command(self, command_list): # command_list instead of command string
        self.console_output.clear()
        self.console_output.append(f"Executing: {' '.join(command_list)}\n") # Join list for display
        
        self.show_progress(True)
        
        self.thread = CommandRunner(command_list) # Pass list
        self.thread.output_received.connect(self.update_output)
        self.thread.command_finished.connect(self.command_complete)
        self.thread.start()
    
    def update_output(self, text):
        # Add timestamps and formatting, preserve ANSI colors
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Convert ANSI color codes to HTML formatting
        html_text = convert_ansi_to_html(text)
        formatted_text = f'<span style="color: #888888;">[{timestamp}]</span> {html_text}'
        
        # Use insertHtml instead of append to support rich formatting
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(formatted_text + '<br>')
        self.console_output.setTextCursor(cursor)
        
        # Auto scroll to bottom
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        self.console_output.setTextCursor(cursor)
    
    def command_complete(self, return_code):
        self.show_progress(False)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        if return_code == 0:
            success_msg = f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ff55; font-weight: bold;">Command completed successfully!</span>'
            cursor.insertHtml(success_msg)
        else:
            error_msg = f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ff5555; font-weight: bold;">Command failed with return code {return_code}</span>'
            cursor.insertHtml(error_msg)
        
        # Auto scroll to bottom
        cursor.movePosition(cursor.End)
        self.console_output.setTextCursor(cursor)

class AndroidTab(QWidget):
    """Tab for Android device analysis"""
    
    def __init__(self):
        super().__init__()
        self.thread = None
        self.initUI()
        
    def initUI(self):
        # Main splitter for better layout
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top section with controls in horizontal layout
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(15)
        top_layout.setContentsMargins(15, 15, 15, 15)
        
        # Left side: Android Operations Group - taking up about 33% of space
        operations_group = QGroupBox("Android Operations")
        operations_layout = QVBoxLayout()
        operations_layout.setSpacing(6)
        
        # Create styled buttons
        self.download_apks_btn = QPushButton("Download APKs")
        self.download_apks_btn.setToolTip("Download APK files from connected Android device")
        self.download_apks_btn.setMaximumHeight(30)
        self.download_apks_btn.clicked.connect(self.download_apks)
        operations_layout.addWidget(self.download_apks_btn)
        
        self.check_adb_btn = QPushButton("Check Device via ADB")
        self.check_adb_btn.setToolTip("Check connected Android device via ADB for potential threats")
        self.check_adb_btn.setMaximumHeight(30)
        self.check_adb_btn.clicked.connect(self.check_adb)
        operations_layout.addWidget(self.check_adb_btn)
        
        self.check_bugreport_btn = QPushButton("Check Bugreport")
        self.check_bugreport_btn.setToolTip("Analyze Android bugreport for indicators of compromise")
        self.check_bugreport_btn.setMaximumHeight(30)
        self.check_bugreport_btn.clicked.connect(self.check_bugreport)
        operations_layout.addWidget(self.check_bugreport_btn)
        
        self.check_backup_btn = QPushButton("Check Android Backup")
        self.check_backup_btn.setToolTip("Analyze Android backup for potential threats (without specific IOC file focus)")
        self.check_backup_btn.setMaximumHeight(30)
        self.check_backup_btn.clicked.connect(self.check_backup)
        operations_layout.addWidget(self.check_backup_btn)
        
        self.check_androidqf_btn = QPushButton("Check AndroidQF")
        self.check_androidqf_btn.setToolTip("Analyze Android Quick Forensics data")
        self.check_androidqf_btn.setMaximumHeight(30)
        self.check_androidqf_btn.clicked.connect(self.check_androidqf)
        operations_layout.addWidget(self.check_androidqf_btn)
        
        self.check_iocs_btn = QPushButton("Check Backup with IOCs")
        self.check_iocs_btn.setToolTip("Run full backup analysis with IOC checking using default IOC path")
        self.check_iocs_btn.setMaximumHeight(30)
        self.check_iocs_btn.clicked.connect(self.check_iocs)
        operations_layout.addWidget(self.check_iocs_btn)
        
        
        operations_group.setLayout(operations_layout)
        
        # Right side: Options Group - taking up about 67% of space
        options_group = QGroupBox("Configuration")
        options_layout = QFormLayout()
        options_layout.setSpacing(8)
        
        # Target Path
        target_container = QWidget()
        target_layout = QHBoxLayout(target_container)
        target_layout.setContentsMargins(0, 0, 0, 0)
        
        self.target_path = QLineEdit()
        self.target_path.setPlaceholderText("Select target directory or file...")
        
        self.browse_target_btn = QPushButton("Browse")
        self.browse_target_btn.setMinimumWidth(80)
        self.browse_target_btn.setMaximumHeight(30)
        self.browse_target_btn.clicked.connect(lambda: self.browse_path(self.target_path, True))
        
        target_layout.addWidget(self.target_path)
        target_layout.addWidget(self.browse_target_btn)
        options_layout.addRow("Target Path:", target_container)
        
        # Output Path
        output_container = QWidget()
        output_layout = QHBoxLayout(output_container)
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output directory...")
        
        self.browse_output_btn = QPushButton("Browse")
        self.browse_output_btn.setMinimumWidth(80)
        self.browse_output_btn.setMaximumHeight(30)
        self.browse_output_btn.clicked.connect(lambda: self.browse_path(self.output_path, True))
        
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.browse_output_btn)
        options_layout.addRow("Output Path:", output_container)
        
        # Device Serial
        self.serial = QLineEdit()
        self.serial.setPlaceholderText("Device serial number (optional)")
        options_layout.addRow("Device Serial:", self.serial)
        
        # Backup Password
        self.backup_password = QLineEdit()
        self.backup_password.setEchoMode(QLineEdit.Password)
        self.backup_password.setPlaceholderText("Enter backup password (if required)")
        options_layout.addRow("Backup Password:", self.backup_password)
        
        # Options checkboxes
        options_container = QWidget()
        options_checkbox_layout = QHBoxLayout(options_container)
        options_checkbox_layout.setContentsMargins(0, 0, 0, 0)
        
        self.all_apks = QCheckBox("Download All APKs")
        self.all_apks.setToolTip("Download all APKs including system apps (for Download APKs)")
        
        self.non_interactive = QCheckBox("Non-interactive Mode")
        self.non_interactive.setToolTip("Run in non-interactive mode (for applicable commands)")
        
        options_checkbox_layout.addWidget(self.all_apks)
        options_checkbox_layout.addWidget(self.non_interactive)
        options_checkbox_layout.addStretch()
        
        options_layout.addRow("Options:", options_container)
        
        options_group.setLayout(options_layout)
        
        top_layout.addWidget(operations_group, 1)
        top_layout.addWidget(options_group, 2)
        
        console_group = QGroupBox("Output Console")
        console_layout = QVBoxLayout()
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        self.console_output.setMinimumHeight(400)
        # Enable rich text to support HTML formatting for colors
        self.console_output.setAcceptRichText(True)
        
        console_controls = QWidget()
        console_controls_layout = QHBoxLayout(console_controls)
        console_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.clear_console_btn = QPushButton("Clear")
        self.clear_console_btn.setMinimumWidth(60)
        self.clear_console_btn.clicked.connect(self.clear_console)
        
        console_controls_layout.addStretch()
        console_controls_layout.addWidget(self.clear_console_btn)
        
        console_layout.addWidget(console_controls)
        console_layout.addWidget(self.console_output)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMaximumHeight(20)
        console_layout.addWidget(self.progress_bar)
        
        console_group.setLayout(console_layout)
        
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(console_group)
        main_splitter.setSizes([200, 600])
        
        main_layout_wrapper = QVBoxLayout()
        main_layout_wrapper.setContentsMargins(0, 0, 0, 0)
        main_layout_wrapper.addWidget(main_splitter)
        self.setLayout(main_layout_wrapper)
    
    def clear_console(self):
        self.console_output.clear()
    
    def update_status(self, message, color="#ffffff"):
        if hasattr(self, 'progress_bar') and self.progress_bar.isVisible():
            self.progress_bar.setFormat(f"{message}")
    
    def show_progress(self, show=True):
        if show:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat("Operation in progress...")
            self.download_apks_btn.setEnabled(False)
            self.check_adb_btn.setEnabled(False)
            self.check_bugreport_btn.setEnabled(False)
            self.check_backup_btn.setEnabled(False)
            self.check_androidqf_btn.setEnabled(False)
            self.check_iocs_btn.setEnabled(False)
        else:
            self.progress_bar.setVisible(False)
            self.download_apks_btn.setEnabled(True)
            self.check_adb_btn.setEnabled(True)
            self.check_bugreport_btn.setEnabled(True)
            self.check_backup_btn.setEnabled(True)
            self.check_androidqf_btn.setEnabled(True)
            self.check_iocs_btn.setEnabled(True)
    
    def browse_path(self, line_edit, is_dir=False):
        if is_dir:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            line_edit.setText(path)
    
    def download_apks(self):
        if not self.output_path.text():
            QMessageBox.warning(self, "Input Required", "Please select an output path for APKs")
            return
        command_list = ["mvt-android", "download-apks", "-o", self.output_path.text()]
        if self.serial.text():
            command_list.extend(["-s", self.serial.text()])
        if self.all_apks.isChecked():
            command_list.append("-a")
        self.run_command(command_list)
    
    def check_adb(self):
        command_list = ["mvt-android", "check-adb"]
        if self.serial.text():
            command_list.extend(["-s", self.serial.text()])
        if self.output_path.text():
            command_list.extend(["-o", self.output_path.text()])
        if self.non_interactive.isChecked():
            command_list.append("-n")
        if self.backup_password.text():
            command_list.extend(["-p", self.backup_password.text()])
        self.run_command(command_list)
    
    def check_bugreport(self):
        if not self.target_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a bugreport path")
            return
        command_list = ["mvt-android", "check-bugreport"]
        if self.output_path.text():
            command_list.extend(["-o", self.output_path.text()])
        command_list.append(self.target_path.text())
        self.run_command(command_list)
    
    def check_backup(self):
        if not self.target_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a backup path for Android analysis")
            return
        command_list = ["mvt-android", "check-backup"]
        if self.output_path.text():
            command_list.extend(["-o", self.output_path.text()])
        if self.non_interactive.isChecked():
            command_list.append("-n")
        if self.backup_password.text():
            command_list.extend(["-p", self.backup_password.text()])
        command_list.append(self.target_path.text())
        self.run_command(command_list)
    
    def check_androidqf(self):
        if not self.target_path.text():
            QMessageBox.warning(self, "Input Required", "Please select an AndroidQF path")
            return
        command_list = ["mvt-android", "check-androidqf"]
        if self.output_path.text():
            command_list.extend(["-o", self.output_path.text()])
        if self.non_interactive.isChecked():
            command_list.append("-n")
        if self.backup_password.text():
            command_list.extend(["-p", self.backup_password.text()])
        command_list.append(self.target_path.text())
        self.run_command(command_list)
    
    def check_iocs(self):
        if not self.target_path.text():
            QMessageBox.warning(self, "Input Required", "Please select a target path for Android IOC check")
            return
        command_list = ["mvt-android", "check-backup"]
        ioc_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "mvt", "indicators")
        command_list.extend(["--iocs", ioc_path])
        if self.output_path.text():
            command_list.extend(["--output", self.output_path.text()])
        if self.serial.text():
            command_list.extend(["-s", self.serial.text()])
        if self.non_interactive.isChecked():
            command_list.append("-n")
        if self.backup_password.text():
            command_list.extend(["-p", self.backup_password.text()])
        command_list.append(self.target_path.text())
        self.run_command(command_list)
    
    
    def run_command(self, command_list):
        self.console_output.clear()
        self.console_output.append(f"Executing: {' '.join(command_list)}\n")
        self.show_progress(True)
        self.thread = CommandRunner(command_list)
        self.thread.output_received.connect(self.update_output)
        self.thread.command_finished.connect(self.command_complete)
        self.thread.start()
    
    def update_output(self, text):
        # Add timestamps and formatting, preserve ANSI colors
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Convert ANSI color codes to HTML formatting
        html_text = convert_ansi_to_html(text)
        formatted_text = f'<span style="color: #888888;">[{timestamp}]</span> {html_text}'
        
        # Use insertHtml instead of append to support rich formatting
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(formatted_text + '<br>')
        self.console_output.setTextCursor(cursor)
        
        # Auto scroll to bottom
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        self.console_output.setTextCursor(cursor)
    
    def command_complete(self, return_code):
        self.show_progress(False)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        if return_code == 0:
            success_msg = f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ff55; font-weight: bold;">Command completed successfully!</span>'
            cursor.insertHtml(success_msg)
        else:
            error_msg = f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ff5555; font-weight: bold;">Command failed with return code {return_code}</span>'
            cursor.insertHtml(error_msg)
        
        # Auto scroll to bottom
        cursor.movePosition(cursor.End)
        self.console_output.setTextCursor(cursor)

class UtilitiesTab(QWidget):
    """Tab for utilities and common features"""
    
    def __init__(self):
        super().__init__()
        self.thread = None
        self.initUI()
        
    def initUI(self):
        # Main splitter for better layout
        main_splitter = QSplitter(Qt.Vertical)
        
        # Top section with controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setSpacing(15)
        top_layout.setContentsMargins(15, 15, 15, 15)
        
        # Utilities Group
        utilities_group = QGroupBox("Utilities & Tools")
        utilities_layout = QVBoxLayout()
        utilities_layout.setSpacing(8)
        
        # Download IOCs
        self.download_iocs_btn = QPushButton("Download/Update IOCs")
        self.download_iocs_btn.setToolTip("Download latest Indicators of Compromise definitions for both iOS and Android")
        self.download_iocs_btn.clicked.connect(self.download_iocs)
        utilities_layout.addWidget(self.download_iocs_btn)
        
        # Show Version
        self.version_btn = QPushButton("Display MVT Version")
        self.version_btn.setToolTip("Show installed MVT version information for both iOS and Android")
        self.version_btn.clicked.connect(self.show_version)
        utilities_layout.addWidget(self.version_btn)
        
        # Update MVT
        self.update_mvt_btn = QPushButton("Update MVT")
        self.update_mvt_btn.setToolTip("Update Mobile Verification Toolkit to the latest version")
        self.update_mvt_btn.clicked.connect(self.update_mvt)
        utilities_layout.addWidget(self.update_mvt_btn)
        
        utilities_group.setLayout(utilities_layout)
        
        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        
        # Add widgets to top layout
        top_layout.addWidget(utilities_group)
        top_layout.addWidget(self.progress_bar)
        top_layout.addStretch()  # Push everything to top
        
        # Console output with improved styling
        console_group = QGroupBox("Output Console")
        console_layout = QVBoxLayout()
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        # Enable rich text to support HTML formatting for colors
        self.console_output.setAcceptRichText(True)
        
        # Add clear button for console
        console_controls = QWidget()
        console_controls_layout = QHBoxLayout(console_controls)
        console_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.clear_console_btn = QPushButton("Clear")
        self.clear_console_btn.setMinimumWidth(60)
        self.clear_console_btn.clicked.connect(self.clear_console)
        
        console_controls_layout.addStretch()
        console_controls_layout.addWidget(self.clear_console_btn)
        
        console_layout.addWidget(console_controls)
        console_layout.addWidget(self.console_output)
        console_group.setLayout(console_layout)
        
        # Add to splitter
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(console_group)
        main_splitter.setSizes([150, 450])  # Adjusted sizes
        
        # Main layout
        main_layout_wrapper = QVBoxLayout()
        main_layout_wrapper.setContentsMargins(0, 0, 0, 0)
        main_layout_wrapper.addWidget(main_splitter)
        self.setLayout(main_layout_wrapper)
    
    def clear_console(self):
        self.console_output.clear()
    
    def update_status(self, message, color="#ffffff"):
        if hasattr(self, 'progress_bar') and self.progress_bar.isVisible():
            self.progress_bar.setFormat(f"{message}")
    
    def show_progress(self, show=True, message="Operation in progress..."):
        if show:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setFormat(message)
            self.download_iocs_btn.setEnabled(False)
            self.version_btn.setEnabled(False)
            self.update_mvt_btn.setEnabled(False)
        else:
            self.progress_bar.setVisible(False)
            self.download_iocs_btn.setEnabled(True)
            self.version_btn.setEnabled(True)
            self.update_mvt_btn.setEnabled(True)
    
    def download_iocs(self):
        self.console_output.clear()
        cursor = self.console_output.textCursor()
        cursor.insertHtml('<span style="color: #55ffff;">Attempting to download/update IOCs for iOS...</span>')
        self.console_output.setTextCursor(cursor)
        self.show_progress(True, message="Downloading iOS IOCs...")
        self.thread = CommandRunner(["mvt-ios", "download-iocs"])
        self.thread.output_received.connect(self.update_output)
        self.thread.command_finished.connect(self.ios_iocs_downloaded)
        self.thread.start()

    def ios_iocs_downloaded(self, return_code):
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        if return_code == 0:
            success_msg = f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ff55;">iOS IOCs downloaded/updated successfully!</span>'
            cursor.insertHtml(success_msg)
        else:
            error_msg = f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ff5555;">iOS IOCs download/update failed (code: {return_code}).</span>'
            cursor.insertHtml(error_msg)
        
        cursor.insertHtml('<br><br>Attempting to download/update IOCs for Android...')
        self.console_output.setTextCursor(cursor)
        
        self.show_progress(True, message="Downloading Android IOCs...") # Keep progress active
        self.thread_android = CommandRunner(["mvt-android", "download-iocs"])
        self.thread_android.output_received.connect(self.update_output)
        self.thread_android.command_finished.connect(self.android_iocs_downloaded)
        self.thread_android.start()

    def android_iocs_downloaded(self, return_code):
        self.show_progress(False) # Hide progress after second command
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        if return_code == 0:
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ff55;">Android IOCs downloaded/updated successfully!</span>')
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ff55; font-weight: bold;">All IOC download/update attempts finished.</span>')
        else:
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ff5555;">Android IOCs download/update failed (code: {return_code}).</span>')
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ffaa00; font-weight: bold;">All IOC download/update attempts finished, one or more failed.</span>')
        
        self.console_output.setTextCursor(cursor)
        self.scroll_to_bottom()

    def show_version(self):
        self.console_output.clear()
        cursor = self.console_output.textCursor()
        cursor.insertHtml('<span style="color: #55ffff;">Checking MVT iOS version...</span>')
        self.console_output.setTextCursor(cursor)
        self.show_progress(True, message="Checking iOS MVT Version...")
        self.thread = CommandRunner(["mvt-ios", "version"])
        self.thread.output_received.connect(self.update_output)
        self.thread.command_finished.connect(self.ios_version_checked)
        self.thread.start()

    def ios_version_checked(self, return_code):
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        if return_code != 0:
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ff5555;">Failed to get iOS MVT version (code: {return_code}).</span>')
        
        cursor.insertHtml('<br><br>Checking MVT Android version...')
        self.console_output.setTextCursor(cursor)
        
        self.show_progress(True, message="Checking Android MVT Version...") # Keep progress active
        self.thread_android = CommandRunner(["mvt-android", "version"])
        self.thread_android.output_received.connect(self.update_output)
        self.thread_android.command_finished.connect(self.android_version_checked)
        self.thread_android.start()

    def android_version_checked(self, return_code):
        self.show_progress(False)
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        if return_code != 0:
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ff5555;">Failed to get Android MVT version (code: {return_code}).</span>')
        
        cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ff55; font-weight: bold;">Version checks complete.</span>')
        self.console_output.setTextCursor(cursor)
        self.scroll_to_bottom()

    def update_mvt(self):
        """Update MVT to the latest version using pip"""
        self.console_output.clear()
        cursor = self.console_output.textCursor()
        cursor.insertHtml('<span style="color: #55ffff;">Updating Mobile Verification Toolkit to latest version...</span><br>')
        cursor.insertHtml('<span style="color: #ffaa00;">This may take a few minutes depending on your internet connection.</span>')
        self.console_output.setTextCursor(cursor)
        
        self.show_progress(True, message="Updating MVT...")
        
        # Use pip to upgrade MVT
        self.thread = CommandRunner(["pip", "install", "--upgrade", "mvt"])
        self.thread.output_received.connect(self.update_output)
        self.thread.command_finished.connect(self.mvt_update_complete)
        self.thread.start()

    def mvt_update_complete(self, return_code):
        """Handle completion of MVT update"""
        self.show_progress(False)
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        if return_code == 0:
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ff55; font-weight: bold;">MVT updated successfully!</span>')
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ffff;">You may need to restart the application to use the updated version.</span>')
        else:
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ff5555; font-weight: bold;">MVT update failed (return code: {return_code})</span>')
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ffaa00;">Try running as administrator/sudo or check your internet connection.</span>')
        
        self.console_output.setTextCursor(cursor)
        self.scroll_to_bottom()
        
    def run_command(self, command_list): # General run_command, though specific ones are used above
        self.console_output.clear()
        self.console_output.append(f"Executing: {' '.join(command_list)}\n")
        self.show_progress(True)
        self.thread = CommandRunner(command_list)
        self.thread.output_received.connect(self.update_output)
        self.thread.command_finished.connect(self.generic_command_complete) # Use a generic completer
        self.thread.start()

    def generic_command_complete(self, return_code):
        self.show_progress(False)
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        
        if return_code == 0:
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #55ff55; font-weight: bold;">Command completed successfully!</span>')
        else:
            cursor.insertHtml(f'<br><span style="color: #888888;">[{timestamp}]</span> <span style="color: #ff5555; font-weight: bold;">Command failed with return code {return_code}</span>')
        
        self.console_output.setTextCursor(cursor)
        self.scroll_to_bottom()

    def update_output(self, text):
        # Add timestamps and formatting, preserve ANSI colors
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Convert ANSI color codes to HTML formatting
        html_text = convert_ansi_to_html(text)
        formatted_text = f'<span style="color: #888888;">[{timestamp}]</span> {html_text}'
        
        # Use insertHtml instead of append to support rich formatting
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(formatted_text + '<br>')
        self.console_output.setTextCursor(cursor)
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        cursor = self.console_output.textCursor()
        cursor.movePosition(cursor.End)
        self.console_output.setTextCursor(cursor)

class MainWindow(QMainWindow):
    """Main window for the MVT GUI application"""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        # Set window properties
        self.setWindowTitle("Mobile Verification Toolkit - GUI Dashboard")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Set application icon
        app_icon = create_app_icon()
        self.setWindowIcon(app_icon)
        
        # Apply dark theme
        self.setStyleSheet(DARK_THEME)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget for different functionality
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        
        # Initialize tabs
        self.ios_tab = IOSTab()
        self.android_tab = AndroidTab()
        self.utilities_tab = UtilitiesTab()
        
        # Add tabs with simple text
        self.tabs.addTab(self.ios_tab, "iOS Analysis")
        self.tabs.addTab(self.android_tab, "Android Analysis")
        self.tabs.addTab(self.utilities_tab, "Utilities")
        
        main_layout.addWidget(self.tabs)
        
        # Enhanced status bar
        status_bar = self.statusBar()
        status_bar.showMessage("Ready - MVT GUI Dashboard")
        
        # Add status indicators
        self.mvt_status_label = QLabel("Checking MVT...")
        status_bar.addPermanentWidget(self.mvt_status_label)
        
        # Check MVT installation
        self.check_mvt_installation()
    
    def check_mvt_installation(self):
        """Check if MVT is properly installed"""
        try:
            # Try to run mvt-ios version to check if MVT is installed
            process = subprocess.run(
                ["mvt-ios", "version"], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if process.returncode == 0:
                logger.info("MVT is installed and working correctly")
                self.mvt_status_label.setText("MVT Ready")
                self.mvt_status_label.setStyleSheet("color: #00aa00; font-weight: bold;")
                self.statusBar().showMessage("Ready - MVT installation verified")
            else:
                logger.warning("MVT may not be installed correctly")
                self.mvt_status_label.setText("MVT Warning")
                self.mvt_status_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
                self.show_mvt_warning()
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.error("MVT is not installed or not in PATH")
            self.mvt_status_label.setText("MVT Missing")
            self.mvt_status_label.setStyleSheet("color: #ff0000; font-weight: bold;")
            self.show_mvt_warning()
    
    def show_mvt_warning(self):
        """Show warning dialog about MVT installation"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("MVT Installation Check")
        msg.setText("Mobile Verification Toolkit (MVT) Installation Issue")
        msg.setInformativeText(
            "MVT was not found in your system PATH or is not responding correctly.\n\n"
            "Please ensure MVT is installed correctly before using this application.\n\n"
            "Installation instructions:\n"
            "• pip3 install mvt\n"
            "• Restart the terminal/command prompt\n"
            "• Ensure Python and pip are in your PATH"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MVT GUI Dashboard")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("MVT Community")
    
    # Set application icon
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    # Center window on screen
    screen = app.primaryScreen().geometry()
    window_geometry = main_window.frameGeometry()
    window_geometry.moveCenter(screen.center())
    main_window.move(window_geometry.topLeft())
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
