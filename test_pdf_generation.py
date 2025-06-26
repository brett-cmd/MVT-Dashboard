#!/usr/bin/env python3
"""
Test script for MVT PDF Report Generation
This script tests PDF generation with real MVT scan results.
"""

import os
import sys
from datetime import datetime
from mvt_pdf_generator import generate_mvt_report

def test_pdf_generation(output_dir):
    """Test PDF generation with real MVT data."""
    
    if not os.path.exists(output_dir):
        print(f"❌ Error: Directory '{output_dir}' does not exist")
        return False
    
    # Check for JSON files
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    if not json_files:
        print(f"❌ Error: No JSON files found in '{output_dir}'")
        print("Please run an MVT scan first to generate data files.")
        return False
    
    print(f"📁 Found {len(json_files)} JSON files in: {output_dir}")
    print("📄 Files found:")
    for json_file in sorted(json_files):
        print(f"   • {json_file}")
    
    # Detect device type based on file names
    device_type = "iOS" if any("backup_info" in f for f in json_files) else "Android"
    print(f"📱 Detected device type: {device_type}")
    
    try:
        print("\n🔄 Generating PDF report...")
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"MVT_Report_{device_type}_{timestamp}.pdf"
        
        report_path = generate_mvt_report(output_dir, device_type, filename)
        
        print(f"✅ Success! PDF report generated:")
        print(f"   📄 {report_path}")
        
        # Get file size
        file_size = os.path.getsize(report_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"   📊 File size: {file_size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating PDF report: {e}")
        
        # Print more detailed error for debugging
        import traceback
        print("\n🔍 Detailed error information:")
        traceback.print_exc()
        
        return False

def main():
    """Main function."""
    print("MVT PDF Report Generation Test")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_pdf_generation.py <mvt_output_directory>")
        print("\nExample:")
        print("  python3 test_pdf_generation.py /Users/brett/Desktop/MVT_output")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    success = test_pdf_generation(output_dir)
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("\nYou can now use the PDF generation feature in the MVT GUI:")
        print("1. Run an MVT scan with output directory")
        print("2. Click the '📄 Generate PDF Report' button")
        print("3. View your professional security report!")
    else:
        print("\n❌ Test failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 