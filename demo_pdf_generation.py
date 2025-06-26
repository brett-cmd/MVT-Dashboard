#!/usr/bin/env python3
"""
Demo script for MVT PDF Report Generation
This demonstrates how to generate PDF reports from MVT scan results.
"""

import os
import json
import tempfile
from datetime import datetime
from mvt_pdf_generator import generate_mvt_report

def create_sample_mvt_data(output_dir):
    """Create sample MVT data for demonstration purposes."""
    
    # Sample iOS backup info
    backup_info = {
        "device_name": "John's iPhone",
        "product_type": "iPhone12,1",
        "product_version": "15.6.1",
        "serial_number": "F2LXXX12345",
        "phone_number": "+1234567890",
        "imei": "123456789012345",
        "last_backup_date": "2024-01-15T10:30:00Z"
    }
    
    # Sample applications data
    applications = [
        {
            "app_name": "WhatsApp",
            "bundle_id": "net.whatsapp.WhatsApp",
            "app_store": True,
            "version": "23.1.78"
        },
        {
            "app_name": "Suspicious App",
            "bundle_id": "com.unknown.suspicious",
            "app_store": False,
            "version": "1.0"
        },
        {
            "app_name": "Safari",
            "bundle_id": "com.apple.mobilesafari",
            "app_store": True,
            "version": "15.6"
        }
    ]
    
    # Sample network usage data
    netusage = [
        {
            "process": "WhatsApp",
            "bundle_id": "net.whatsapp.WhatsApp",
            "wifi_in": 1024000,
            "wifi_out": 512000,
            "wwan_in": 256000,
            "wwan_out": 128000,
            "timestamp": "2024-01-15T08:00:00Z"
        },
        {
            "process": "suspicious_process",
            "bundle_id": None,
            "wifi_in": 0,
            "wifi_out": 0,
            "wwan_in": 50000,
            "wwan_out": 25000,
            "timestamp": "2024-01-15T02:30:00Z"
        }
    ]
    
    # Sample SMS data
    sms = [
        {
            "text": "Click this link: https://suspicious-domain.com/malware",
            "phone_number": "+1234567890",
            "timestamp": "2024-01-15T14:30:00Z",
            "is_from_me": False
        },
        {
            "text": "Normal message from friend",
            "phone_number": "+0987654321",
            "timestamp": "2024-01-15T15:00:00Z",
            "is_from_me": False
        }
    ]
    
    # Sample detected issues (IOC matches)
    applications_detected = [
        {
            "module": "Applications",
            "app_name": "Suspicious App",
            "bundle_id": "com.unknown.suspicious",
            "timestamp": "2024-01-15T12:00:00Z",
            "matched_indicator": "Known malicious bundle ID",
            "severity": "high"
        }
    ]
    
    sms_detected = [
        {
            "module": "SMS",
            "text": "Click this link: https://suspicious-domain.com/malware",
            "url": "https://suspicious-domain.com/malware",
            "timestamp": "2024-01-15T14:30:00Z",
            "matched_indicator": "Malicious domain indicator",
            "phone_number": "+1234567890"
        }
    ]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Write sample data files
    data_files = {
        "backup_info.json": backup_info,
        "applications.json": applications,
        "netusage.json": netusage,
        "sms.json": sms,
        "applications_detected.json": applications_detected,
        "sms_detected.json": sms_detected
    }
    
    for filename, data in data_files.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    print(f"Sample MVT data created in: {output_dir}")
    return output_dir

def demo_pdf_generation():
    """Demonstrate PDF generation with sample data."""
    print("MVT PDF Report Generation Demo")
    print("=" * 40)
    
    # Create temporary directory for sample data
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Creating sample data in: {temp_dir}")
        
        # Create sample MVT scan results
        create_sample_mvt_data(temp_dir)
        
        # Generate PDF report for iOS
        print("\nGenerating iOS PDF report...")
        ios_report = generate_mvt_report(temp_dir, "iOS", "demo_ios_security_report.pdf")
        print(f"iOS report generated: {ios_report}")
        
        # Generate PDF report for Android (same data, different device type)
        print("\nGenerating Android PDF report...")
        android_report = generate_mvt_report(temp_dir, "Android", "demo_android_security_report.pdf")
        print(f"Android report generated: {android_report}")
        
        print("\n" + "=" * 40)
        print("Demo completed successfully!")
        print("\nThe generated PDF reports include:")
        print("• Executive summary with security assessment")
        print("• Device information and scan metadata")
        print("• Security findings with IOC matches highlighted")
        print("• Application analysis (App Store vs sideloaded)")
        print("• Network activity analysis")
        print("• Timeline of security events")
        print("• Prioritized recommendations")
        
        print(f"\nReport files:")
        print(f"• iOS Report: {ios_report}")
        print(f"• Android Report: {android_report}")

if __name__ == "__main__":
    try:
        demo_pdf_generation()
    except ImportError as e:
        print(f"Error: Missing dependencies - {e}")
        print("Please install required packages: pip install reportlab matplotlib")
    except Exception as e:
        print(f"Demo failed: {e}") 