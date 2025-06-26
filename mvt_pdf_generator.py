#!/usr/bin/env python3
"""
MVT PDF Report Generator
A comprehensive PDF report generator for Mobile Verification Toolkit (MVT) scan results.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.lib.validators import Auto
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from io import BytesIO
    import base64
except ImportError as e:
    print(f"Required dependencies not installed: {e}")
    print("Please install with: pip install reportlab matplotlib")
    raise

logger = logging.getLogger("MVT-PDF-Generator")

class MVTReportGenerator:
    """Professional PDF report generator for MVT scan results."""
    
    def __init__(self, output_dir: str, device_type: str = "Unknown"):
        """Initialize the report generator.
        
        Args:
            output_dir: Directory containing MVT scan results
            device_type: Type of device analyzed (iOS/Android)
        """
        self.output_dir = Path(output_dir)
        self.device_type = device_type
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.scan_data = {}
        self.detected_issues = []
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        # Title style
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Title'],
                fontSize=24,
                textColor=colors.darkblue,
                spaceAfter=30,
                alignment=TA_CENTER
            ))
        
        # Section heading
        if 'SectionHeading' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeading',
                parent=self.styles['Heading1'],
                fontSize=16,
                textColor=colors.darkblue,
                spaceBefore=20,
                spaceAfter=12,
                borderWidth=1,
                borderPadding=5,
                borderColor=colors.lightgrey,
                backColor=colors.lightgrey
            ))
        
        # Subsection heading
        if 'SubHeading' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SubHeading',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.darkgreen,
                spaceBefore=15,
                spaceAfter=8
            ))
        
        # Alert style for security issues
        if 'Alert' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Alert',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.red,
                backColor=colors.mistyrose,
                borderWidth=1,
                borderColor=colors.red,
                borderPadding=8,
                spaceBefore=10,
                spaceAfter=10
            ))
        
        # Success style for clean results
        if 'Success' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Success',
                parent=self.styles['Normal'],
                fontSize=12,
                textColor=colors.darkgreen,
                backColor=colors.lightgreen,
                borderWidth=1,
                borderColor=colors.darkgreen,
                borderPadding=8,
                spaceBefore=10,
                spaceAfter=10
            ))
        
        # Code style for technical details
        if 'CustomCode' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomCode',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                backColor=colors.lightgrey,
                fontName='Courier',
                spaceBefore=5,
                spaceAfter=5
            ))

    def _safe_numeric(self, value, default=0):
        """Safely convert a value to a numeric type, handling None and invalid values.
        
        Args:
            value: The value to convert
            default: Default value to return if conversion fails
            
        Returns:
            Numeric value or default
        """
        if value is None:
            return default
        
        try:
            # Try to convert to float first
            return float(value)
        except (ValueError, TypeError):
            return default

    def load_scan_data(self) -> bool:
        """Load and parse MVT scan result files.
        
        Returns:
            True if data was successfully loaded, False otherwise
        """
        try:
            logger.info(f"Loading scan data from {self.output_dir}")
            
            # Find all JSON files in the output directory
            json_files = list(self.output_dir.glob("*.json"))
            
            if not json_files:
                logger.warning("No JSON files found in output directory")
                return False
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Store data by filename (without extension)
                    key = json_file.stem
                    self.scan_data[key] = data
                    
                    # Check for detected issues (files ending with _detected)
                    if key.endswith('_detected') and data:
                        self.detected_issues.extend(data)
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse {json_file}: {e}")
                except Exception as e:
                    logger.warning(f"Error reading {json_file}: {e}")
            
            logger.info(f"Loaded {len(self.scan_data)} data files")
            logger.info(f"Found {len(self.detected_issues)} security issues")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load scan data: {e}")
            return False

    def _parse_device_info(self) -> Dict[str, str]:
        """Extract device information from scan data."""
        device_info = {}
        
        # Extract information from info.json (scan metadata)
        if 'info' in self.scan_data:
            info_data = self.scan_data['info']
            if isinstance(info_data, dict):
                device_info.update({
                    'Scan Target Path': info_data.get('target_path', 'Unknown'),
                    'MVT Version': info_data.get('mvt_version', 'Unknown'),
                    'Analysis Date': info_data.get('date', 'Unknown'),
                    'IOC Files Used': str(len(info_data.get('ioc_files', []))),
                    'Hash Files Used': str(len(info_data.get('hashes', [])))
                })
        
        # Check backup_info for iOS - using correct field names from actual data
        if 'backup_info' in self.scan_data:
            backup_data = self.scan_data['backup_info']
            if isinstance(backup_data, dict):
                device_info.update({
                    'Device Name': backup_data.get('Device Name', 'Unknown'),
                    'Product Name': backup_data.get('Product Name', 'Unknown'),
                    'Product Type': backup_data.get('Product Type', 'Unknown'),
                    'Product Version': backup_data.get('Product Version', 'Unknown'),
                    'Build Version': backup_data.get('Build Version', 'Unknown'),
                    'Serial Number': backup_data.get('Serial Number', 'Unknown'),
                    'Phone Number': backup_data.get('Phone Number', 'Unknown'),
                    'IMEI': backup_data.get('IMEI', 'Unknown'),
                    'MEID': backup_data.get('MEID', 'Unknown'),
                    'ICCID': backup_data.get('ICCID', 'Unknown'),
                    'Last Backup Date': backup_data.get('Last Backup Date', 'Unknown'),
                    'Target Identifier': backup_data.get('Target Identifier', 'Unknown')
                })
                
                # Add app count from backup info if available
                if 'Installed Applications' in backup_data:
                    installed_apps = backup_data['Installed Applications']
                    device_info['Total Apps (Backup)'] = str(len(installed_apps))
        
        # Add comprehensive application analysis
        if 'applications' in self.scan_data and isinstance(self.scan_data['applications'], list):
            apps = self.scan_data['applications']
            device_info['Total Apps (Detailed)'] = str(len(apps))
            
            # Count app store vs sideloaded
            appstore_apps = sum(1 for app in apps if not app.get('sideLoadedDeviceBasedVPP', False))
            sideloaded_apps = len(apps) - appstore_apps
            device_info['App Store Apps'] = str(appstore_apps)
            device_info['Sideloaded Apps'] = str(sideloaded_apps)
        
        # Add network activity summary
        if 'datausage' in self.scan_data and isinstance(self.scan_data['datausage'], list):
            data_usage = self.scan_data['datausage']
            device_info['Network Processes'] = str(len(data_usage))
            
            # Calculate total data usage
            total_wifi_out = sum(self._safe_numeric(proc.get('wifi_out', 0)) for proc in data_usage)
            total_wwan_out = sum(self._safe_numeric(proc.get('wwan_out', 0)) for proc in data_usage)
            total_data_sent = total_wifi_out + total_wwan_out
            device_info['Total Data Sent (bytes)'] = f"{int(total_data_sent):,}"
        
        # Add filesystem information
        if 'filesystem' in self.scan_data and isinstance(self.scan_data['filesystem'], list):
            filesystem = self.scan_data['filesystem']
            device_info['Filesystem Entries'] = str(len(filesystem))
        
        # Add TCC permissions count
        if 'tcc' in self.scan_data and isinstance(self.scan_data['tcc'], list):
            tcc_data = self.scan_data['tcc']
            device_info['Privacy Permissions'] = str(len(tcc_data))
        
        # Add location clients count
        if 'locationd_clients' in self.scan_data and isinstance(self.scan_data['locationd_clients'], list):
            location_data = self.scan_data['locationd_clients']
            device_info['Location Clients'] = str(len(location_data))
        
        # Add browser data
        if 'webkit_resource_load_statistics' in self.scan_data:
            webkit_data = self.scan_data['webkit_resource_load_statistics']
            if isinstance(webkit_data, list):
                device_info['Browser Tracking Domains'] = str(len(webkit_data))
        
        # Add scan metadata
        device_info['Report Generated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        device_info['Device Type'] = self.device_type
        device_info['Total Data Sources'] = str(len(self.scan_data))
        
        return device_info

    def _create_executive_summary(self) -> List:
        """Create executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeading']))
        
        # Security assessment
        total_issues = len(self.detected_issues)
        if total_issues > 0:
            summary_text = f"""
            <b>SECURITY ALERT:</b> This forensic analysis has identified <b>{total_issues}</b> 
            potential security issues that require immediate attention. These findings indicate 
            possible indicators of compromise (IOCs) or suspicious activities on the device.
            """
            elements.append(Paragraph(summary_text, self.styles['Alert']))
        else:
            summary_text = """
            <b>CLEAN SCAN:</b> No immediate security threats or indicators of compromise 
            were detected during this analysis. However, this does not guarantee the device 
            is completely free from sophisticated or unknown threats.
            """
            elements.append(Paragraph(summary_text, self.styles['Success']))
        
        # Analysis scope with more details
        data_sources = list(self.scan_data.keys())
        app_count = 0
        if 'applications' in self.scan_data and isinstance(self.scan_data['applications'], list):
            app_count = len(self.scan_data['applications'])
        
        network_count = 0
        if 'datausage' in self.scan_data and isinstance(self.scan_data['datausage'], list):
            network_count = len(self.scan_data['datausage'])
        
        scope_text = f"""
        This Mobile Verification Toolkit (MVT) analysis examined <b>{len(self.scan_data)}</b> 
        different data sources from the {self.device_type} device, including {app_count} applications, 
        {network_count} network processes, system logs, browser history, privacy permissions, 
        location tracking data, and messaging records. Data sources analyzed: {', '.join(data_sources[:8])}
        {f' and {len(data_sources)-8} others' if len(data_sources) > 8 else ''}.
        """
        elements.append(Paragraph(scope_text, self.styles['Normal']))
        
        # Key findings summary
        elements.append(Paragraph("Key Analysis Areas:", self.styles['SubHeading']))
        
        analysis_areas = []
        if 'applications' in self.scan_data:
            apps_count = len(self.scan_data['applications']) if isinstance(self.scan_data['applications'], list) else 0
            analysis_areas.append(f"Applications: {apps_count} analyzed")
        
        if 'sms' in self.scan_data:
            sms_count = len(self.scan_data['sms']) if isinstance(self.scan_data['sms'], list) else 0
            analysis_areas.append(f"SMS Messages: {sms_count} examined")
        
        if 'safari_history' in self.scan_data or 'chrome_history' in self.scan_data:
            analysis_areas.append("Browser History: Analyzed for malicious URLs")
        
        if 'netusage' in self.scan_data or 'datausage' in self.scan_data:
            analysis_areas.append("Network Activity: Process-level traffic analysis")
        
        for area in analysis_areas:
            elements.append(Paragraph(f"• {area}", self.styles['Normal']))
        
        return elements

    def _create_device_info_section(self) -> List:
        """Create device information section."""
        elements = []
        
        elements.append(Paragraph("Device Information", self.styles['SectionHeading']))
        
        device_info = self._parse_device_info()
        
        # Create table with device information
        table_data = [['Property', 'Value']]
        for key, value in device_info.items():
            table_data.append([key, str(value)])
        
        table = Table(table_data, colWidths=[2.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(table)
        
        return elements

    def _create_security_findings_section(self) -> List:
        """Create security findings section."""
        elements = []
        
        elements.append(Paragraph("Security Findings", self.styles['SectionHeading']))
        
        if not self.detected_issues:
            elements.append(Paragraph(
                "✓ No indicators of compromise (IOCs) were detected in this analysis.",
                self.styles['Success']
            ))
            elements.append(Paragraph(
                "Note: This does not guarantee the absence of sophisticated or unknown threats. "
                "Regular security assessments and updates are recommended.",
                self.styles['Normal']
            ))
        else:
            elements.append(Paragraph(
                f"⚠ {len(self.detected_issues)} potential security issues detected:",
                self.styles['Alert']
            ))
            
            # Group findings by type
            findings_by_type = {}
            for issue in self.detected_issues:
                issue_type = issue.get('module', 'Unknown')
                if issue_type not in findings_by_type:
                    findings_by_type[issue_type] = []
                findings_by_type[issue_type].append(issue)
            
            for issue_type, issues in findings_by_type.items():
                elements.append(Paragraph(f"{issue_type.title()} Issues ({len(issues)}):", 
                                        self.styles['SubHeading']))
                
                for issue in issues[:5]:  # Limit to first 5 per type
                    issue_text = self._format_security_issue(issue)
                    elements.append(Paragraph(f"• {issue_text}", self.styles['Normal']))
                
                if len(issues) > 5:
                    elements.append(Paragraph(
                        f"... and {len(issues) - 5} more {issue_type} issues",
                        self.styles['Normal']
                    ))
        
        return elements

    def _format_security_issue(self, issue: Dict) -> str:
        """Format a security issue for display."""
        timestamp = issue.get('timestamp', 'Unknown time')
        if isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        details = []
        
        # Add relevant fields based on issue type
        if 'url' in issue:
            details.append(f"URL: {issue['url']}")
        if 'domain' in issue:
            details.append(f"Domain: {issue['domain']}")
        if 'process' in issue:
            details.append(f"Process: {issue['process']}")
        if 'bundle_id' in issue:
            details.append(f"App: {issue['bundle_id']}")
        if 'matched_indicator' in issue:
            details.append(f"IOC: {issue['matched_indicator']}")
        
        detail_str = " | ".join(details) if details else "See raw data for details"
        return f"[{timestamp}] {detail_str}"

    def _create_detailed_applications_section(self) -> List:
        """Create detailed applications analysis section."""
        elements = []
        
        elements.append(Paragraph("Installed Applications Analysis", self.styles['SectionHeading']))
        
        # Get data from backup_info (simpler list) and applications.json (detailed info)
        backup_apps = []
        detailed_apps = []
        
        if 'backup_info' in self.scan_data and 'Installed Applications' in self.scan_data['backup_info']:
            backup_apps = self.scan_data['backup_info']['Installed Applications']
            
        if 'applications' in self.scan_data and isinstance(self.scan_data['applications'], list):
            detailed_apps = self.scan_data['applications']
        
        # Use the more comprehensive data source
        apps_to_analyze = detailed_apps if detailed_apps else []
        total_apps = len(backup_apps) if backup_apps else len(detailed_apps)
        
        elements.append(Paragraph(f"Total Applications Found: <b>{total_apps}</b>", self.styles['Normal']))
        
        if detailed_apps:
            # Analyze app sources and categories
            appstore_apps = [app for app in detailed_apps if not app.get('sideLoadedDeviceBasedVPP', False)]
            sideloaded_apps = [app for app in detailed_apps if app.get('sideLoadedDeviceBasedVPP', False)]
            
            # Category analysis
            categories = {}
            for app in detailed_apps:
                genre = app.get('genre', 'Unknown')
                categories[genre] = categories.get(genre, 0) + 1
            
            # Source analysis
            summary_text = f"""
            App Store Applications: <b>{len(appstore_apps)}</b><br/>
            Sideloaded Applications: <b>{len(sideloaded_apps)}</b><br/>
            Most Common Category: <b>{max(categories.items(), key=lambda x: x[1])[0] if categories else 'Unknown'}</b>
            """
            elements.append(Paragraph(summary_text, self.styles['Normal']))
            
            if sideloaded_apps:
                elements.append(Paragraph(
                    f"⚠ {len(sideloaded_apps)} sideloaded applications detected - requires security review",
                    self.styles['Alert']
                ))
            
            # Top categories breakdown
            elements.append(Paragraph("Application Categories:", self.styles['SubHeading']))
            sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_categories[:10]:  # Top 10 categories
                elements.append(Paragraph(f"• {category}: {count} apps", self.styles['Normal']))
            
            # High-risk applications (financial, security, etc.)
            high_risk_categories = ['Finance', 'Business', 'Productivity', 'Medical', 'Social Networking']
            high_risk_apps = [app for app in detailed_apps if app.get('genre') in high_risk_categories]
            
            if high_risk_apps:
                elements.append(Paragraph("High-Risk Applications (Finance/Business/Medical):", self.styles['SubHeading']))
                for app in high_risk_apps[:15]:  # Show first 15
                    app_name = app.get('itemName', app.get('name', 'Unknown'))
                    genre = app.get('genre', 'Unknown')
                    version = app.get('bundleShortVersionString', 'Unknown')
                    elements.append(Paragraph(
                        f"• {app_name} ({genre}) - v{version}",
                        self.styles['Normal']
                    ))
                    
                if len(high_risk_apps) > 15:
                    elements.append(Paragraph(
                        f"... and {len(high_risk_apps) - 15} more high-risk applications",
                        self.styles['Normal']
                    ))
            
            # Recently installed apps (last 30 days)
            recent_apps = []
            cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)
            
            for app in detailed_apps:
                purchase_date = app.get('com.apple.iTunesStore.downloadInfo', {}).get('purchaseDate')
                if purchase_date:
                    try:
                        # Parse ISO date
                        purchase_datetime = datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
                        if purchase_datetime.timestamp() > cutoff_date:
                            recent_apps.append((app, purchase_datetime))
                    except:
                        continue
            
            if recent_apps:
                elements.append(Paragraph("Recently Installed Apps (Last 30 Days):", self.styles['SubHeading']))
                recent_apps.sort(key=lambda x: x[1], reverse=True)
                for app, install_date in recent_apps[:10]:
                    app_name = app.get('itemName', app.get('name', 'Unknown'))
                    date_str = install_date.strftime('%Y-%m-%d')
                    elements.append(Paragraph(
                        f"• {app_name} - Installed: {date_str}",
                        self.styles['Normal']
                    ))
        
        else:
            # Fallback to backup apps list
            if backup_apps:
                elements.append(Paragraph("Installed Applications (Bundle IDs):", self.styles['SubHeading']))
                
                # Group similar apps
                app_categories = {
                    'Banking/Finance': [],
                    'Social Media': [],
                    'Google Services': [],
                    'Microsoft Office': [],
                    'Security/VPN': [],
                    'Other': []
                }
                
                for bundle_id in sorted(backup_apps):
                    if any(x in bundle_id.lower() for x in ['bank', 'financial', 'capital', 'mbna', 'cibc', 'amex']):
                        app_categories['Banking/Finance'].append(bundle_id)
                    elif any(x in bundle_id.lower() for x in ['facebook', 'instagram', 'whatsapp', 'messenger', 'linkedin', 'reddit', 'skool']):
                        app_categories['Social Media'].append(bundle_id)
                    elif 'google' in bundle_id.lower():
                        app_categories['Google Services'].append(bundle_id)
                    elif 'microsoft' in bundle_id.lower():
                        app_categories['Microsoft Office'].append(bundle_id)
                    elif any(x in bundle_id.lower() for x in ['vpn', 'proton', 'nord', 'authenticator', 'bitwarden', 'duo']):
                        app_categories['Security/VPN'].append(bundle_id)
                    else:
                        app_categories['Other'].append(bundle_id)
                
                for category, apps in app_categories.items():
                    if apps:
                        elements.append(Paragraph(f"{category} ({len(apps)} apps):", 
                                                ParagraphStyle('Category', parent=self.styles['Normal'], 
                                                             textColor=colors.darkblue, fontName='Helvetica-Bold')))
                        for app in apps[:10]:  # Limit to 10 per category
                            # Clean up bundle ID for display
                            display_name = app.split('.')[-1] if '.' in app else app
                            elements.append(Paragraph(f"  • {display_name} ({app})", self.styles['Normal']))
                        if len(apps) > 10:
                            elements.append(Paragraph(f"  ... and {len(apps) - 10} more", self.styles['Normal']))
        
        return elements

    def _create_privacy_permissions_section(self) -> List:
        """Create TCC privacy permissions analysis section."""
        elements = []
        
        if 'tcc' not in self.scan_data:
            return elements
        
        elements.append(Paragraph("Privacy & Permissions Analysis", self.styles['SectionHeading']))
        
        tcc_data = self.scan_data['tcc']
        if not isinstance(tcc_data, list):
            elements.append(Paragraph("No TCC permission data available.", self.styles['Normal']))
            return elements
        
        # Define sensitive permission types
        sensitive_services = {
            'kTCCServiceCamera': 'Camera Access',
            'kTCCServiceMicrophone': 'Microphone Access',
            'kTCCServiceLocation': 'Location Services',
            'kTCCServicePhotos': 'Photo Library Access',
            'kTCCServiceContactsLimited': 'Contacts Access (Limited)',
            'kTCCServiceContactsFull': 'Contacts Access (Full)',
            'kTCCServiceCalendar': 'Calendar Access',
            'kTCCServiceReminders': 'Reminders Access',
            'kTCCServiceFaceID': 'Face ID Authentication',
            'kTCCServiceSiri': 'Siri Access',
            'kTCCServiceMotion': 'Motion & Fitness',
            'kTCCServiceBluetoothPeripheral': 'Bluetooth Access',
            'kTCCServiceFileProviderPresence': 'File Provider Access',
            'kTCCServiceSystemPolicyDesktopFolder': 'Desktop Folder Access',
            'kTCCServiceSystemPolicyDocumentsFolder': 'Documents Folder Access',
            'kTCCServiceSystemPolicyDownloadsFolder': 'Downloads Folder Access'
        }
        
        # Analyze permissions by service type
        permissions_by_service = {}
        for entry in tcc_data:
            service = entry.get('service', 'Unknown')
            client = entry.get('client', 'Unknown')
            auth_value = entry.get('auth_value', 'Unknown')
            
            if service not in permissions_by_service:
                permissions_by_service[service] = {'allowed': [], 'denied': []}
            
            if auth_value == 'allowed':
                permissions_by_service[service]['allowed'].append(client)
            else:
                permissions_by_service[service]['denied'].append(client)
        
        # Report on sensitive permissions
        sensitive_found = False
        for service_key, service_name in sensitive_services.items():
            if service_key in permissions_by_service:
                sensitive_found = True
                allowed_apps = permissions_by_service[service_key]['allowed']
                denied_apps = permissions_by_service[service_key]['denied']
                
                if allowed_apps:
                    elements.append(Paragraph(f"{service_name}:", self.styles['SubHeading']))
                    
                    # Filter out system apps for cleaner reporting
                    user_apps = [app for app in allowed_apps if not app.startswith('com.apple.') or 'third' in app.lower()]
                    system_apps = [app for app in allowed_apps if app.startswith('com.apple.') and 'third' not in app.lower()]
                    
                    if user_apps:
                        elements.append(Paragraph("Third-party applications with access:", self.styles['Normal']))
                        for app in user_apps[:10]:  # Limit display
                            # Clean up bundle ID for display
                            display_name = app.split('.')[-1] if '.' in app else app
                            elements.append(Paragraph(f"  • {display_name}", self.styles['Normal']))
                        if len(user_apps) > 10:
                            elements.append(Paragraph(f"  ... and {len(user_apps) - 10} more apps", self.styles['Normal']))
                    
                    if system_apps:
                        elements.append(Paragraph(f"System applications: {len(system_apps)} apps", self.styles['Normal']))
        
        if not sensitive_found:
            elements.append(Paragraph("No sensitive privacy permissions detected in TCC data.", self.styles['Success']))
        
        # Summary statistics
        total_permissions = len(tcc_data)
        unique_services = len(permissions_by_service)
        
        summary_text = f"""
        Total Permission Entries: <b>{total_permissions}</b><br/>
        Unique Services: <b>{unique_services}</b><br/>
        Sensitive Permissions Found: <b>{len([s for s in sensitive_services.keys() if s in permissions_by_service])}</b>
        """
        elements.append(Paragraph("TCC Database Summary:", self.styles['SubHeading']))
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        
        return elements

    def _create_location_tracking_section(self) -> List:
        """Create location tracking analysis section."""
        elements = []
        
        if 'locationd_clients' not in self.scan_data:
            return elements
        
        elements.append(Paragraph("Location Tracking Analysis", self.styles['SectionHeading']))
        
        location_data = self.scan_data['locationd_clients']
        if not isinstance(location_data, list):
            elements.append(Paragraph("No location client data available.", self.styles['Normal']))
            return elements
        
        # Analyze location clients
        active_clients = []
        background_clients = []
        
        for client in location_data:
            client_name = client.get('BundleId', client.get('Executable', 'Unknown'))
            
            # Check for background location usage
            if client.get('Authorized') and client.get('BundleId'):
                active_clients.append(client_name)
                
                # Check for background app refresh or always-on location
                if any(key in client for key in ['BackgroundAppRefresh', 'LocationServicesEnabled']):
                    background_clients.append(client_name)
        
        elements.append(Paragraph(f"Applications with Location Access: <b>{len(active_clients)}</b>", self.styles['Normal']))
        
        if background_clients:
            elements.append(Paragraph(
                f"⚠ {len(background_clients)} applications may have background location access",
                self.styles['Alert']
            ))
            
            elements.append(Paragraph("Apps with Potential Background Location:", self.styles['SubHeading']))
            for client in background_clients[:10]:
                display_name = client.split('.')[-1] if '.' in client else client
                elements.append(Paragraph(f"• {display_name}", self.styles['Normal']))
        
        # Filter out system apps for user app analysis
        user_location_apps = [app for app in active_clients if not app.startswith('com.apple.')]
        if user_location_apps:
            elements.append(Paragraph("Third-party Apps with Location Access:", self.styles['SubHeading']))
            for app in user_location_apps[:15]:
                display_name = app.split('.')[-1] if '.' in app else app
                elements.append(Paragraph(f"• {display_name}", self.styles['Normal']))
        
        return elements

    def _create_browser_security_section(self) -> List:
        """Create browser security analysis section."""
        elements = []
        
        if 'safari_history' not in self.scan_data and 'webkit_resource_load_statistics' not in self.scan_data:
            return elements
        
        elements.append(Paragraph("Browser Security Analysis", self.styles['SectionHeading']))
        
        # Analyze Safari history
        if 'safari_history' in self.scan_data:
            safari_data = self.scan_data['safari_history']
            if isinstance(safari_data, list) and safari_data:
                elements.append(Paragraph(f"Safari History Entries: <b>{len(safari_data)}</b>", self.styles['Normal']))
                
                # Look for recent activity (last 7 days)
                recent_cutoff = datetime.now().timestamp() - (7 * 24 * 60 * 60)
                recent_entries = []
                
                for entry in safari_data:
                    visit_time = entry.get('visit_time')
                    if visit_time and isinstance(visit_time, (int, float)):
                        if visit_time > recent_cutoff:
                            recent_entries.append(entry)
                
                if recent_entries:
                    elements.append(Paragraph(f"Recent browsing activity (last 7 days): {len(recent_entries)} visits", self.styles['Normal']))
        
        # Analyze WebKit resource load statistics
        if 'webkit_resource_load_statistics' in self.scan_data:
            webkit_data = self.scan_data['webkit_resource_load_statistics']
            if isinstance(webkit_data, list) and webkit_data:
                elements.append(Paragraph(f"WebKit Tracking Data: <b>{len(webkit_data)}</b> domains", self.styles['Normal']))
                
                # Look for high-frequency domains (potential tracking)
                high_frequency_domains = []
                for entry in webkit_data:
                    registrable_domain = entry.get('RegistrableDomain', '')
                    subframe_under_top_frame_origins = entry.get('subframeUnderTopFrameOrigins', [])
                    
                    if len(subframe_under_top_frame_origins) > 10:  # High cross-site activity
                        high_frequency_domains.append(registrable_domain)
                
                if high_frequency_domains:
                    elements.append(Paragraph(
                        f"Domains with high cross-site activity: {len(high_frequency_domains)}",
                        self.styles['Normal']
                    ))
                    
                    elements.append(Paragraph("Top Cross-Site Tracking Domains:", self.styles['SubHeading']))
                    for domain in high_frequency_domains[:10]:
                        elements.append(Paragraph(f"• {domain}", self.styles['Normal']))
        
        return elements

    def _create_configuration_profiles_section(self) -> List:
        """Create configuration profiles analysis section."""
        elements = []
        
        if 'configuration_profiles' not in self.scan_data:
            return elements
        
        elements.append(Paragraph("Configuration Profiles Analysis", self.styles['SectionHeading']))
        
        profiles_data = self.scan_data['configuration_profiles']
        if not isinstance(profiles_data, list):
            elements.append(Paragraph("No configuration profiles data available.", self.styles['Normal']))
            return elements
        
        if not profiles_data:
            elements.append(Paragraph("✓ No configuration profiles installed.", self.styles['Success']))
            return elements
        
        elements.append(Paragraph(f"⚠ {len(profiles_data)} configuration profiles found:", self.styles['Alert']))
        elements.append(Paragraph(
            "Configuration profiles can control device behavior and should be reviewed for security implications.",
            self.styles['Normal']
        ))
        
        for i, profile in enumerate(profiles_data[:10], 1):  # Show first 10
            profile_name = profile.get('payload_display_name', f'Profile {i}')
            profile_id = profile.get('payload_identifier', 'Unknown ID')
            install_date = profile.get('install_date', 'Unknown')
            
            elements.append(Paragraph(
                f"• {profile_name} (ID: {profile_id}) - Installed: {install_date}",
                self.styles['Normal']
            ))
        
        if len(profiles_data) > 10:
            elements.append(Paragraph(f"... and {len(profiles_data) - 10} more profiles", self.styles['Normal']))
        
        return elements

    def _create_applications_section(self) -> List:
        """Create applications analysis section."""
        elements = []
        
        if 'applications' not in self.scan_data:
            return elements
        
        elements.append(Paragraph("Application Analysis", self.styles['SectionHeading']))
        
        apps_data = self.scan_data['applications']
        if not isinstance(apps_data, list):
            elements.append(Paragraph("No application data available.", self.styles['Normal']))
            return elements
        
        total_apps = len(apps_data)
        
        # Count apps by source
        appstore_apps = sum(1 for app in apps_data if app.get('app_store', True))
        sideloaded_apps = total_apps - appstore_apps
        
        summary_text = f"""
        Total applications analyzed: <b>{total_apps}</b><br/>
        App Store applications: <b>{appstore_apps}</b><br/>
        Sideloaded/Unknown source: <b>{sideloaded_apps}</b>
        """
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        
        if sideloaded_apps > 0:
            elements.append(Paragraph(
                f"⚠ {sideloaded_apps} applications from non-App Store sources detected. "
                "These require additional security review.",
                self.styles['Alert']
            ))
        
        # Show sample of non-App Store apps
        if sideloaded_apps > 0:
            elements.append(Paragraph("Non-App Store Applications:", self.styles['SubHeading']))
            
            non_appstore = [app for app in apps_data if not app.get('app_store', True)]
            for app in non_appstore[:10]:  # Show first 10
                app_name = app.get('app_name', 'Unknown')
                bundle_id = app.get('bundle_id', 'Unknown')
                elements.append(Paragraph(
                    f"• {app_name} ({bundle_id})", 
                    self.styles['Normal']
                ))
            
            if len(non_appstore) > 10:
                elements.append(Paragraph(
                    f"... and {len(non_appstore) - 10} more applications",
                    self.styles['Normal']
                ))
        
        return elements

    def _create_network_analysis_section(self) -> List:
        """Create network activity analysis section."""
        elements = []
        
        # Check for network usage data
        network_data = None
        if 'netusage' in self.scan_data:
            network_data = self.scan_data['netusage']
        elif 'datausage' in self.scan_data:
            network_data = self.scan_data['datausage']
        
        if not network_data:
            return elements
        
        elements.append(Paragraph("Network Activity Analysis", self.styles['SectionHeading']))
        
        if not isinstance(network_data, list):
            elements.append(Paragraph("No network usage data available.", self.styles['Normal']))
            return elements
        
        # Analyze network usage patterns
        total_processes = len(network_data)
        suspicious_processes = [
            proc for proc in network_data 
            if not proc.get('bundle_id') or proc.get('bundle_id') == 'UNKNOWN'
        ]
        
        # Calculate total data usage statistics
        total_wifi_out = sum(self._safe_numeric(proc.get('wifi_out', 0)) for proc in network_data)
        total_wwan_out = sum(self._safe_numeric(proc.get('wwan_out', 0)) for proc in network_data)
        total_wifi_in = sum(self._safe_numeric(proc.get('wifi_in', 0)) for proc in network_data)
        total_wwan_in = sum(self._safe_numeric(proc.get('wwan_in', 0)) for proc in network_data)
        
        total_sent = total_wifi_out + total_wwan_out
        total_received = total_wifi_in + total_wwan_in
        
        # Find top data consumers
        data_consumers = []
        for proc in network_data:
            wifi_out = self._safe_numeric(proc.get('wifi_out', 0))
            wwan_out = self._safe_numeric(proc.get('wwan_out', 0))
            wifi_in = self._safe_numeric(proc.get('wifi_in', 0))
            wwan_in = self._safe_numeric(proc.get('wwan_in', 0))
            
            total_usage = wifi_out + wwan_out + wifi_in + wwan_in
            if total_usage > 0:
                data_consumers.append({
                    'name': proc.get('proc_name', 'Unknown'),
                    'bundle_id': proc.get('bundle_id', 'Unknown'),
                    'total_usage': total_usage,
                    'sent': wifi_out + wwan_out,
                    'received': wifi_in + wwan_in
                })
        
        data_consumers.sort(key=lambda x: x['total_usage'], reverse=True)
        
        summary_text = f"""
        Total processes with network activity: <b>{total_processes}</b><br/>
        Total data sent: <b>{int(total_sent):,}</b> bytes ({int(total_sent/(1024*1024)):.1f} MB)<br/>
        Total data received: <b>{int(total_received):,}</b> bytes ({int(total_received/(1024*1024)):.1f} MB)<br/>
        Processes without valid bundle ID: <b>{len(suspicious_processes)}</b>
        """
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        
        # Show top data consumers
        if data_consumers:
            elements.append(Paragraph("Top Network Data Consumers:", self.styles['SubHeading']))
            for consumer in data_consumers[:10]:
                app_name = consumer['name']
                if consumer['bundle_id'] and consumer['bundle_id'] != 'Unknown':
                    # Clean up bundle ID for better display
                    clean_bundle = consumer['bundle_id'].split('.')[-1] if '.' in consumer['bundle_id'] else consumer['bundle_id']
                    app_display = f"{clean_bundle} ({app_name})" if clean_bundle != app_name else app_name
                else:
                    app_display = app_name
                
                usage_mb = consumer['total_usage'] / (1024 * 1024)
                sent_mb = consumer['sent'] / (1024 * 1024)
                received_mb = consumer['received'] / (1024 * 1024)
                
                elements.append(Paragraph(
                    f"• {app_display} - Total: {usage_mb:.1f} MB (Sent: {sent_mb:.1f} MB, Received: {received_mb:.1f} MB)",
                    self.styles['Normal']
                ))
        
        if suspicious_processes:
            elements.append(Paragraph(
                "⚠ Processes without valid bundle IDs detected. These may require investigation:",
                self.styles['Alert']
            ))
            
            for proc in suspicious_processes[:5]:
                proc_name = proc.get('proc_name', proc.get('process', 'Unknown'))
                
                # Safe numeric handling using helper function
                wifi_out = self._safe_numeric(proc.get('wifi_out', 0))
                wwan_out = self._safe_numeric(proc.get('wwan_out', 0))
                wifi_in = self._safe_numeric(proc.get('wifi_in', 0))
                wwan_in = self._safe_numeric(proc.get('wwan_in', 0))
                
                data_sent = wifi_out + wwan_out
                data_received = wifi_in + wwan_in
                
                elements.append(Paragraph(
                    f"• {proc_name} - Sent: {int(data_sent):,} bytes, Received: {int(data_received):,} bytes",
                    self.styles['Normal']
                ))
        
        return elements

    def _create_messaging_analysis_section(self) -> List:
        """Create messaging and communications analysis section."""
        elements = []
        
        # Check for SMS/messaging data
        sms_data = self.scan_data.get('sms', [])
        calls_data = self.scan_data.get('calls', [])
        contacts_data = self.scan_data.get('contacts', [])
        
        if not sms_data and not calls_data and not contacts_data:
            return elements
        
        elements.append(Paragraph("Messaging & Communications Analysis", self.styles['SectionHeading']))
        
        # SMS Analysis
        if sms_data and isinstance(sms_data, list):
            elements.append(Paragraph(f"SMS Messages: <b>{len(sms_data)}</b>", self.styles['Normal']))
            
            # Analyze message patterns
            recent_cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)  # 30 days
            recent_messages = []
            
            for msg in sms_data:
                msg_date = msg.get('date')
                if msg_date:
                    try:
                        if isinstance(msg_date, str):
                            msg_datetime = datetime.fromisoformat(msg_date.replace('Z', '+00:00'))
                        elif isinstance(msg_date, (int, float)):
                            msg_datetime = datetime.fromtimestamp(msg_date)
                        else:
                            continue
                        
                        if msg_datetime.timestamp() > recent_cutoff:
                            recent_messages.append(msg)
                    except:
                        continue
            
            if recent_messages:
                elements.append(Paragraph(f"Recent SMS activity (last 30 days): {len(recent_messages)} messages", self.styles['Normal']))
            
            # Check for any flagged messages
            flagged_messages = [msg for msg in sms_data if msg.get('flagged') or msg.get('suspicious')]
            if flagged_messages:
                elements.append(Paragraph(
                    f"⚠ {len(flagged_messages)} potentially suspicious SMS messages detected",
                    self.styles['Alert']
                ))
        
        # Calls Analysis
        if calls_data and isinstance(calls_data, list):
            elements.append(Paragraph(f"Call Records: <b>{len(calls_data)}</b>", self.styles['Normal']))
            
            # Count call types
            incoming_calls = sum(1 for call in calls_data if call.get('direction') == 'incoming')
            outgoing_calls = sum(1 for call in calls_data if call.get('direction') == 'outgoing')
            
            elements.append(Paragraph(
                f"Incoming calls: {incoming_calls}, Outgoing calls: {outgoing_calls}",
                self.styles['Normal']
            ))
        
        # Contacts Analysis
        if contacts_data and isinstance(contacts_data, list):
            elements.append(Paragraph(f"Contacts: <b>{len(contacts_data)}</b>", self.styles['Normal']))
        
        return elements

    def _create_timeline_section(self) -> List:
        """Create timeline analysis section."""
        elements = []
        
        elements.append(Paragraph("Timeline Analysis", self.styles['SectionHeading']))
        
        # Collect timestamped events from various sources
        timeline_events = []
        
        # Process detected issues
        for issue in self.detected_issues:
            timestamp = issue.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        continue
                elif isinstance(timestamp, (int, float)):
                    timestamp = datetime.fromtimestamp(timestamp)
                
                timeline_events.append({
                    'timestamp': timestamp,
                    'type': 'Security Issue',
                    'description': self._format_security_issue(issue),
                    'severity': 'high'
                })
        
        if not timeline_events:
            elements.append(Paragraph(
                "No significant timeline events to display.",
                self.styles['Normal']
            ))
            return elements
        
        # Sort events by timestamp
        timeline_events.sort(key=lambda x: x['timestamp'])
        
        # Show recent events (last 30 days)
        recent_cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        recent_events = [
            event for event in timeline_events 
            if event['timestamp'].timestamp() > recent_cutoff
        ]
        
        if recent_events:
            elements.append(Paragraph("Recent Security Events (Last 30 Days):", self.styles['SubHeading']))
            
            for event in recent_events[:10]:
                timestamp_str = event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                elements.append(Paragraph(
                    f"[{timestamp_str}] {event['description']}",
                    self.styles['CustomCode']
                ))
        
        return elements

    def _create_recommendations_section(self) -> List:
        """Create recommendations section."""
        elements = []
        
        elements.append(Paragraph("Recommendations", self.styles['SectionHeading']))
        
        recommendations = []
        
        if self.detected_issues:
            recommendations.extend([
                "IMMEDIATE: Investigate all detected security issues flagged in this report",
                "IMMEDIATE: Consider isolating the device from networks until issues are resolved",
                "HIGH: Perform a full factory reset if compromise is confirmed",
                "HIGH: Change all passwords and revoke authentication tokens for accounts used on this device"
            ])
        
        # General security recommendations
        recommendations.extend([
            "Keep the device operating system updated to the latest version",
            "Only install applications from official app stores",
            "Regularly review and remove unused applications",
            "Enable automatic security updates where available",
            "Use strong, unique passwords and enable two-factor authentication",
            "Regularly backup important data to secure, offline storage"
        ])
        
        for i, rec in enumerate(recommendations, 1):
            priority = "IMMEDIATE" if "IMMEDIATE" in rec else "HIGH" if "HIGH" in rec else "MEDIUM"
            color = colors.red if priority == "IMMEDIATE" else colors.orange if priority == "HIGH" else colors.darkgreen
            
            rec_text = rec.replace("IMMEDIATE: ", "").replace("HIGH: ", "").replace("MEDIUM: ", "")
            elements.append(Paragraph(
                f"<b>[{priority}]</b> {rec_text}",
                self.styles['Normal'] if priority == "MEDIUM" else 
                ParagraphStyle('Priority', parent=self.styles['Normal'], textColor=color)
            ))
        
        return elements

    def generate_report(self, output_filename: str = None) -> str:
        """Generate the complete PDF report.
        
        Args:
            output_filename: Optional custom filename for the report
            
        Returns:
            Path to the generated PDF file
        """
        if not self.load_scan_data():
            raise ValueError("Failed to load scan data from output directory")
        
        # Generate filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"MVT_Security_Report_{self.device_type}_{timestamp}.pdf"
        
        # Ensure .pdf extension
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'
        
        output_path = self.output_dir / output_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build document content with error handling
        story = []
        
        try:
            # Title page
            story.append(Paragraph("Mobile Device Security Analysis Report", self.styles['CustomTitle']))
            story.append(Spacer(1, 30))
            
            # Device info box
            device_info = self._parse_device_info()
            device_summary = f"""
            <b>Device Type:</b> {self.device_type}<br/>
            <b>Target Path:</b> {device_info.get('Scan Target Path', 'Unknown')}<br/>
            <b>MVT Version:</b> {device_info.get('MVT Version', 'Unknown')}<br/>
            <b>Analysis Date:</b> {device_info.get('Analysis Date', 'Unknown')}<br/>
            <b>IOC Files Used:</b> {device_info.get('IOC Files Used', '0')}<br/>
            <b>Total Data Sources:</b> {device_info.get('Total Data Sources', '0')}<br/>
            <b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            story.append(Paragraph(device_summary, self.styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Add all sections with individual error handling
            try:
                story.extend(self._create_executive_summary())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating executive summary: {e}")
                story.append(Paragraph(f"Error in executive summary: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_device_info_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating device info section: {e}")
                story.append(Paragraph(f"Error in device info: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_security_findings_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating security findings section: {e}")
                story.append(Paragraph(f"Error in security findings: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_detailed_applications_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating detailed applications section: {e}")
                story.append(Paragraph(f"Error in applications section: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_privacy_permissions_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating privacy permissions section: {e}")
                story.append(Paragraph(f"Error in privacy permissions: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_location_tracking_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating location tracking section: {e}")
                story.append(Paragraph(f"Error in location tracking: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_browser_security_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating browser security section: {e}")
                story.append(Paragraph(f"Error in browser security: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_configuration_profiles_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating configuration profiles section: {e}")
                story.append(Paragraph(f"Error in configuration profiles: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_network_analysis_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating network analysis section: {e}")
                story.append(Paragraph(f"Error in network analysis: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_messaging_analysis_section())
                story.append(Spacer(1, 20))
            except Exception as e:
                logger.warning(f"Error creating messaging analysis section: {e}")
                story.append(Paragraph(f"Error in messaging analysis: {e}", self.styles['Normal']))
            
            try:
                story.extend(self._create_timeline_section())
                story.append(PageBreak())
            except Exception as e:
                logger.warning(f"Error creating timeline section: {e}")
                story.append(Paragraph(f"Error in timeline: {e}", self.styles['Normal']))
                story.append(PageBreak())
            
            try:
                story.extend(self._create_recommendations_section())
            except Exception as e:
                logger.warning(f"Error creating recommendations section: {e}")
                story.append(Paragraph(f"Error in recommendations: {e}", self.styles['Normal']))
            
            # Add footer note
            footer_text = """
            <i>This report was generated by the Mobile Verification Toolkit (MVT) Dashboard. 
            MVT is developed by Amnesty International for consensual forensic analysis. 
            For questions about this report, contact your security team.</i>
            """
            story.append(Spacer(1, 30))
            story.append(Paragraph(footer_text, self.styles['Normal']))
            
        except Exception as e:
            logger.error(f"Error building report content: {e}")
            raise
        
        # Build PDF
        try:
            doc.build(story)
            logger.info(f"Report generated successfully: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise

def generate_mvt_report(output_dir: str, device_type: str = "Unknown", custom_filename: str = None) -> str:
    """Convenience function to generate an MVT report.
    
    Args:
        output_dir: Directory containing MVT scan results
        device_type: Type of device (iOS/Android)
        custom_filename: Optional custom filename
        
    Returns:
        Path to generated PDF report
    """
    generator = MVTReportGenerator(output_dir, device_type)
    return generator.generate_report(custom_filename)

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mvt_pdf_generator.py <output_directory> [device_type] [filename]")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    device_type = sys.argv[2] if len(sys.argv) > 2 else "Unknown"
    filename = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        report_path = generate_mvt_report(output_dir, device_type, filename)
        print(f"Report generated: {report_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 