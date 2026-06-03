"""Test script to generate sample HTML/PDF reports.

This script tests the report generation functionality with real database data.
Requires: .env file with database credentials

Usage:
    python scripts/test_report_generation.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.report_generator import (
    _create_mpa_effectiveness_report,
    _create_temporal_trends_report,
    _create_community_structure_report,
    _create_data_quality_report
)


def test_mpa_report():
    """Generate MPA Effectiveness Report for Cabo Pulmo."""
    print("\n" + "="*80)
    print("Generating MPA Effectiveness Report (Cabo Pulmo)...")
    print("="*80)
    
    try:
        report = _create_mpa_effectiveness_report(region="Cabo Pulmo")
        
        # Generate HTML
        html = report.generate_html()
        output_path = PROJECT_ROOT / "outputs" / "mpa_effectiveness_cabo_pulmo.html"
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(html, encoding='utf-8')
        print(f"✓ HTML saved: {output_path}")
        print(f"  Size: {len(html):,} bytes")
        print(f"  Figures: {len(report.figures)}")
        
        # Try PDF generation
        try:
            pdf_bytes = report.generate_pdf()
            pdf_path = PROJECT_ROOT / "outputs" / "mpa_effectiveness_cabo_pulmo.pdf"
            pdf_path.write_bytes(pdf_bytes)
            print(f"✓ PDF saved: {pdf_path}")
            print(f"  Size: {len(pdf_bytes):,} bytes")
        except ImportError:
            print("⚠ PDF generation skipped (WeasyPrint not installed)")
        except Exception as e:
            print(f"⚠ PDF generation failed: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_temporal_report():
    """Generate Temporal Trends Report."""
    print("\n" + "="*80)
    print("Generating Temporal Trends Report (Biomass)...")
    print("="*80)
    
    try:
        report = _create_temporal_trends_report(metric="biomass")
        
        # Generate HTML
        html = report.generate_html()
        output_path = PROJECT_ROOT / "outputs" / "temporal_trends_biomass.html"
        output_path.write_text(html, encoding='utf-8')
        print(f"✓ HTML saved: {output_path}")
        print(f"  Size: {len(html):,} bytes")
        print(f"  Figures: {len(report.figures)}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_community_report():
    """Generate Community Structure Report."""
    print("\n" + "="*80)
    print("Generating Community Structure Report (La Paz)...")
    print("="*80)
    
    try:
        report = _create_community_structure_report(region="La Paz")
        
        # Generate HTML
        html = report.generate_html()
        output_path = PROJECT_ROOT / "outputs" / "community_structure_la_paz.html"
        output_path.write_text(html, encoding='utf-8')
        print(f"✓ HTML saved: {output_path}")
        print(f"  Size: {len(html):,} bytes")
        print(f"  Figures: {len(report.figures)}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_report():
    """Generate Data Quality Audit Report."""
    print("\n" + "="*80)
    print("Generating Data Quality Audit Report...")
    print("="*80)
    
    try:
        report = _create_data_quality_report()
        
        # Generate HTML
        html = report.generate_html()
        output_path = PROJECT_ROOT / "outputs" / "data_quality_audit.html"
        output_path.write_text(html, encoding='utf-8')
        print(f"✓ HTML saved: {output_path}")
        print(f"  Size: {len(html):,} bytes")
        print(f"  Figures: {len(report.figures)}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all report generation tests."""
    print("\n" + "="*80)
    print("LTEM Report Generation Test Suite")
    print("="*80)
    
    # Check for .env file
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        print("\n✗ ERROR: .env file not found!")
        print("  Please create .env with database credentials:")
        print("  LTEM_DB_HOST=your_host")
        print("  LTEM_DB_USER=your_user")
        print("  LTEM_DB_PASSWORD=your_password")
        print("  LTEM_DB_NAME=ecological_monitoring")
        sys.exit(1)
    
    results = {
        "MPA Effectiveness": test_mpa_report(),
        "Temporal Trends": test_temporal_report(),
        "Community Structure": test_community_report(),
        "Data Quality": test_quality_report()
    }
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} reports generated successfully")
    
    if passed == total:
        print("\n✓ All reports generated successfully!")
        print(f"  Check outputs/ directory for HTML files")
    else:
        print(f"\n⚠ {total - passed} report(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
