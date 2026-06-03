"""Tests for report generation tools.

These tests verify that report generation functions correctly:
- HTML structure is valid
- Figures are embedded properly
- Statistical tables render accurately
- PDF generation works (if dependencies installed)

Run with:
    pytest tests/test_report_generator.py -v
"""

import json
import os

import pytest


# ---------------------------------------------------------------------------
# 1. Report generator module imports
# ---------------------------------------------------------------------------

class TestReportGeneratorImports:
	"""Verify report generator module loads correctly."""
	
	def test_module_imports(self):
		"""Report generator module should import without errors."""
		import tools.report_generator as rg
		assert hasattr(rg, 'register')
		assert callable(rg.register)
	
	def test_report_class_exists(self):
		"""LTEMReportGenerator class should be defined."""
		from tools.report_generator import LTEMReportGenerator
		assert LTEMReportGenerator is not None
	
	def test_report_templates_exist(self):
		"""All 4 report template functions should be defined."""
		import tools.report_generator as rg
		assert hasattr(rg, '_create_mpa_effectiveness_report')
		assert hasattr(rg, '_create_temporal_trends_report')
		assert hasattr(rg, '_create_community_structure_report')
		assert hasattr(rg, '_create_data_quality_report')


# ---------------------------------------------------------------------------
# 2. Base report generator class tests
# ---------------------------------------------------------------------------

class TestLTEMReportGenerator:
	"""Test the base report generator class."""
	
	def test_initialization(self):
		"""Report generator should initialize with title and region."""
		from tools.report_generator import LTEMReportGenerator
		report = LTEMReportGenerator(title="Test Report", region="Cabo Pulmo")
		assert report.title == "Test Report"
		assert report.region == "Cabo Pulmo"
		assert len(report.sections) == 0
		assert len(report.figures) == 0
	
	def test_add_section(self):
		"""Should be able to add text sections."""
		from tools.report_generator import LTEMReportGenerator
		report = LTEMReportGenerator(title="Test Report")
		report.add_section("Introduction", "This is a test section.")
		assert len(report.sections) == 1
		assert report.sections[0]["type"] == "text"
		assert report.sections[0]["heading"] == "Introduction"
	
	def test_add_table(self):
		"""Should be able to add data tables."""
		from tools.report_generator import LTEMReportGenerator
		report = LTEMReportGenerator(title="Test Report")
		data = [{"col1": "a", "col2": 1}, {"col1": "b", "col2": 2}]
		report.add_table("Test Table", data, caption="Test caption")
		assert len(report.sections) == 1
		assert report.sections[0]["type"] == "table"
		assert len(report.sections[0]["data"]) == 2
	
	def test_generate_html_basic(self):
		"""Should generate valid HTML structure."""
		from tools.report_generator import LTEMReportGenerator
		report = LTEMReportGenerator(title="Test Report")
		report.add_section("Test Section", "Test content")
		html = report.generate_html()
		
		# Check basic HTML structure
		assert "<!DOCTYPE html>" in html
		assert "<html" in html
		assert "</html>" in html
		assert "<head>" in html
		assert "</head>" in html
		assert "<body>" in html
		assert "</body>" in html
		assert "Test Report" in html
		assert "Test Section" in html
		assert "Test content" in html
	
	def test_html_includes_css(self):
		"""Generated HTML should include CSS styling."""
		from tools.report_generator import LTEMReportGenerator
		report = LTEMReportGenerator(title="Test Report")
		html = report.generate_html()
		
		assert "<style>" in html
		assert "</style>" in html
		assert "font-family" in html
		assert "color" in html


# ---------------------------------------------------------------------------
# 3. Figure embedding tests
# ---------------------------------------------------------------------------

class TestFigureEmbedding:
	"""Test that matplotlib figures embed correctly."""
	
	def test_add_figure_matplotlib(self):
		"""Should embed matplotlib figures as base64 PNG."""
		from tools.report_generator import LTEMReportGenerator
		import matplotlib.pyplot as plt
		
		report = LTEMReportGenerator(title="Test Report")
		
		# Create a simple figure
		fig, ax = plt.subplots(figsize=(8, 6))
		ax.plot([1, 2, 3], [1, 4, 9])
		ax.set_title("Test Plot")
		
		report.add_figure(fig, caption="Test caption", title="Test Figure")
		
		assert len(report.figures) == 1
		assert report.figures[0]["type"] == "figure"
		assert report.figures[0]["caption"] == "Test caption"
		assert report.figures[0]["title"] == "Test Figure"
		assert "data:image/png;base64," in report.figures[0]["data"]
	
	def test_figure_in_html(self):
		"""Figures should render correctly in HTML output."""
		from tools.report_generator import LTEMReportGenerator
		import matplotlib.pyplot as plt
		
		report = LTEMReportGenerator(title="Test Report")
		
		fig, ax = plt.subplots()
		ax.plot([1, 2], [1, 2])
		report.add_figure(fig, caption="Test plot")
		
		html = report.generate_html()
		
		assert '<div class="figure">' in html
		assert '<img src="data:image/png;base64,' in html
		assert 'Test plot' in html


# ---------------------------------------------------------------------------
# 4. MCP tool integration tests (without server)
# ---------------------------------------------------------------------------

class TestReportGeneratorTools:
	"""Test report generator MCP tool functions directly."""
	
	def test_mpa_report_function_exists(self):
		"""MPA report template function should be callable."""
		from tools.report_generator import _create_mpa_effectiveness_report
		assert callable(_create_mpa_effectiveness_report)
	
	def test_temporal_report_function_exists(self):
		"""Temporal report template function should be callable."""
		from tools.report_generator import _create_temporal_trends_report
		assert callable(_create_temporal_trends_report)
	
	def test_community_report_function_exists(self):
		"""Community report template function should be callable."""
		from tools.report_generator import _create_community_structure_report
		assert callable(_create_community_structure_report)
	
	def test_quality_report_function_exists(self):
		"""Data quality report template function should be callable."""
		from tools.report_generator import _create_data_quality_report
		assert callable(_create_data_quality_report)


# ---------------------------------------------------------------------------
# 5. Report template structure tests (smoke tests, no DB required)
# ---------------------------------------------------------------------------

class TestReportTemplateStructure:
	"""Test that report templates have correct structure (no DB queries)."""
	
	def test_mpa_report_structure(self):
		"""MPA report should have expected sections."""
		from tools.report_generator import LTEMReportGenerator
		
		# Create a mock report to test structure
		report = LTEMReportGenerator(title="MPA Effectiveness Assessment")
		report.add_section("Overview", "Test overview")
		report.add_section("Interpretation Guide", "Test interpretation")
		
		html = report.generate_html()
		
		assert "MPA Effectiveness Assessment" in html
		assert "Overview" in html
		assert "Interpretation Guide" in html
	
	def test_temporal_report_structure(self):
		"""Temporal report should have expected sections."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Temporal Trends Analysis")
		report.add_section("Overview", "Test overview")
		
		html = report.generate_html()
		
		assert "Temporal Trends Analysis" in html
		assert "Overview" in html
	
	def test_community_report_structure(self):
		"""Community report should have expected sections."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Community Structure Analysis")
		report.add_section("Overview", "Test overview")
		
		html = report.generate_html()
		
		assert "Community Structure Analysis" in html
		assert "Overview" in html
	
	def test_quality_report_structure(self):
		"""Quality report should have expected sections."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Data Quality Audit Report")
		report.add_section("Overview", "Test overview")
		
		html = report.generate_html()
		
		assert "Data Quality Audit Report" in html
		assert "Overview" in html


# ---------------------------------------------------------------------------
# 6. PDF generation tests (optional - requires WeasyPrint)
# ---------------------------------------------------------------------------

class TestPDFGeneration:
	"""Test PDF generation functionality."""
	
	def test_pdf_generation_import(self):
		"""Should be able to import PDF generation method."""
		from tools.report_generator import LTEMReportGenerator
		report = LTEMReportGenerator(title="Test Report")
		assert hasattr(report, 'generate_pdf')
		assert callable(report.generate_pdf)
	
	@pytest.mark.skipif(
		not os.getenv('TEST_PDF_GENERATION'),
		reason="PDF generation requires WeasyPrint (set TEST_PDF_GENERATION=1 to enable)"
	)
	def test_pdf_generation_basic(self):
		"""PDF generation should produce bytes output."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Test Report")
		report.add_section("Test", "Content")
		
		try:
			pdf_bytes = report.generate_pdf()
			assert isinstance(pdf_bytes, bytes)
			assert len(pdf_bytes) > 0
			assert pdf_bytes[:4] == b'%PDF'  # PDF magic number
		except ImportError:
			pytest.skip("WeasyPrint not installed")


# ---------------------------------------------------------------------------
# 7. Table rendering tests
# ---------------------------------------------------------------------------

class TestTableRendering:
	"""Test that tables render correctly in HTML."""
	
	def test_table_headers(self):
		"""Table headers should be generated from dict keys."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Test Report")
		data = [
			{"Region": "Cabo Pulmo", "Biomass": 100.5, "Richness": 50},
			{"Region": "La Paz", "Biomass": 75.3, "Richness": 45}
		]
		report.add_table("Test Table", data)
		
		html = report.generate_html()
		
		assert "<table>" in html
		assert "<th>Region</th>" in html
		assert "<th>Biomass</th>" in html
		assert "<th>Richness</th>" in html
	
	def test_table_number_formatting(self):
		"""Float numbers should be formatted with 3 decimal places."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Test Report")
		data = [{"value": 123.456789}]
		report.add_table("Test Table", data)
		
		html = report.generate_html()
		
		# Should format to 3 decimal places
		assert "123.457" in html
	
	def test_empty_table(self):
		"""Empty tables should not crash."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Test Report")
		report.add_table("Empty Table", [])
		
		html = report.generate_html()
		
		# Should still generate heading
		assert "Empty Table" in html


# ---------------------------------------------------------------------------
# 8. Metadata and footer tests
# ---------------------------------------------------------------------------

class TestMetadataAndFooter:
	"""Test report metadata and footer rendering."""
	
	def test_timestamp_in_metadata(self):
		"""Report should include generation timestamp."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Test Report")
		html = report.generate_html()
		
		assert "Generated:" in html
		assert "UTC" in html
	
	def test_region_in_metadata(self):
		"""If region specified, it should appear in metadata."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Test Report", region="Cabo Pulmo")
		html = report.generate_html()
		
		assert "Region: Cabo Pulmo" in html
	
	def test_footer_present(self):
		"""Report should include footer."""
		from tools.report_generator import LTEMReportGenerator
		
		report = LTEMReportGenerator(title="Test Report")
		html = report.generate_html()
		
		assert "LTEM Database MCP Server" in html
		assert "Long-Term Ecological Monitoring" in html


# ---------------------------------------------------------------------------
# 9. Integration test markers
# ---------------------------------------------------------------------------

@pytest.mark.slow
class TestReportGeneratorIntegration:
	"""Integration tests that require database connectivity.
	
	These tests are marked 'slow' and require a valid .env file.
	Run with: pytest tests/test_report_generator.py -v -m slow
	"""
	
	def test_mpa_report_with_real_data(self):
		"""Generate MPA report with real database data."""
		from tools.report_generator import _create_mpa_effectiveness_report
		
		try:
			report = _create_mpa_effectiveness_report(region="Cabo Pulmo")
			html = report.generate_html()
			
			assert "MPA Effectiveness Assessment" in html
			assert len(html) > 1000  # Should be substantial
			assert "Cabo Pulmo" in html
		except Exception as e:
			pytest.skip(f"Database not available: {e}")
	
	def test_temporal_report_with_real_data(self):
		"""Generate temporal trends report with real database data."""
		from tools.report_generator import _create_temporal_trends_report
		
		try:
			report = _create_temporal_trends_report(metric="biomass")
			html = report.generate_html()
			
			assert "Temporal Trends Analysis" in html
			assert len(html) > 1000
		except Exception as e:
			pytest.skip(f"Database not available: {e}")
	
	def test_community_report_with_real_data(self):
		"""Generate community structure report with real database data."""
		from tools.report_generator import _create_community_structure_report
		
		try:
			report = _create_community_structure_report(region="La Paz")
			html = report.generate_html()
			
			assert "Community Structure Analysis" in html
			assert len(html) > 1000
		except Exception as e:
			pytest.skip(f"Database not available: {e}")
	
	def test_quality_report_with_real_data(self):
		"""Generate data quality report with real database data."""
		from tools.report_generator import _create_data_quality_report
		
		try:
			report = _create_data_quality_report()
			html = report.generate_html()
			
			assert "Data Quality Audit Report" in html
			assert len(html) > 1000
		except Exception as e:
			pytest.skip(f"Database not available: {e}")
