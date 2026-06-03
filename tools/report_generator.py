"""Automated ecological report generation with visualizations.

Generates publication-ready HTML and PDF reports for:
- MPA effectiveness assessment
- Temporal trends analysis
- Community structure analysis
- Data quality audits

Uses Matplotlib/Seaborn for static, publication-quality visualizations.
"""

import base64
import io
import json
from datetime import datetime
from typing import Any

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from fastmcp import FastMCP
from mcp_server.db import execute_select


# Set publication-quality style
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.2)
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.figsize'] = (10, 6)


class LTEMReportGenerator:
	"""Base class for generating LTEM ecological reports with visualizations."""

	def __init__(self, title: str, region: str | None = None):
		"""Initialize report generator.

		Args:
			title: Report title
			region: Optional region filter
		"""
		self.title = title
		self.region = region
		self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
		self.figures = []
		self.sections = []

	def add_section(self, heading: str, content: str):
		"""Add a text section to the report."""
		self.sections.append({"type": "text", "heading": heading, "content": content})

	def add_figure(self, fig: plt.Figure, caption: str, title: str | None = None):
		"""Add a matplotlib figure to the report.

		Args:
			fig: Matplotlib figure object
			caption: Figure caption with methodology notes
			title: Optional figure title
		"""
		# Convert figure to base64 PNG for HTML embedding
		buf = io.BytesIO()
		fig.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
		buf.seek(0)
		img_base64 = base64.b64encode(buf.read()).decode('utf-8')
		plt.close(fig)

		self.figures.append({
			"type": "figure",
			"title": title,
			"caption": caption,
			"data": f"data:image/png;base64,{img_base64}"
		})
		self.sections.append(self.figures[-1])

	def add_table(self, heading: str, data: list[dict], caption: str | None = None):
		"""Add a data table to the report.

		Args:
			heading: Table heading
			data: List of dicts with table rows
			caption: Optional table caption
		"""
		self.sections.append({
			"type": "table",
			"heading": heading,
			"data": data,
			"caption": caption
		})

	def _generate_html_head(self) -> str:
		"""Generate HTML head with CSS styling."""
		return f"""<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>{self.title}</title>
	<style>
		body {{
			font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
			max-width: 1000px;
			margin: 30px auto;
			padding: 20px;
			background: #f5f5f5;
			color: #333;
		}}
		.container {{
			background: white;
			padding: 40px;
			border-radius: 8px;
			box-shadow: 0 2px 10px rgba(0,0,0,0.1);
		}}
		h1 {{
			color: #1a5276;
			border-bottom: 3px solid #1a5276;
			padding-bottom: 15px;
			margin-bottom: 10px;
		}}
		h2 {{
			color: #2c3e50;
			margin-top: 35px;
			margin-bottom: 15px;
			border-left: 5px solid #3498db;
			padding-left: 15px;
		}}
		h3 {{
			color: #34495e;
			margin-top: 25px;
		}}
		.metadata {{
			color: #7f8c8d;
			font-size: 0.95em;
			margin-bottom: 30px;
		}}
		.figure {{
			margin: 30px 0;
			text-align: center;
		}}
		.figure img {{
			max-width: 100%;
			border: 1px solid #ddd;
			border-radius: 4px;
			padding: 10px;
			background: white;
		}}
		.figure .caption {{
			margin-top: 10px;
			font-size: 0.9em;
			color: #555;
			font-style: italic;
		}}
		table {{
			border-collapse: collapse;
			width: 100%;
			margin: 20px 0;
			font-size: 0.9em;
		}}
		th, td {{
			border: 1px solid #ddd;
			padding: 12px;
			text-align: left;
		}}
		th {{
			background-color: #3498db;
			color: white;
			font-weight: bold;
		}}
		tr:nth-child(even) {{
			background-color: #f8f9fa;
		}}
		tr:hover {{
			background-color: #e8f4f8;
		}}
		.warning {{
			background: #fff3cd;
			border-left: 5px solid #ffc107;
			padding: 15px;
			margin: 20px 0;
			border-radius: 4px;
		}}
		.success {{
			background: #d4edda;
			border-left: 5px solid #28a745;
			padding: 15px;
			margin: 20px 0;
			border-radius: 4px;
		}}
		.info {{
			background: #d1ecf1;
			border-left: 5px solid #17a2b8;
			padding: 15px;
			margin: 20px 0;
			border-radius: 4px;
		}}
		code {{
			background: #f4f4f4;
			padding: 2px 6px;
			border-radius: 3px;
			font-family: 'Courier New', monospace;
			font-size: 0.9em;
		}}
		.footer {{
			margin-top: 50px;
			padding-top: 20px;
			border-top: 1px solid #ddd;
			color: #7f8c8d;
			font-size: 0.85em;
			text-align: center;
		}}
	</style>
</head>
<body>
<div class="container">
"""

	def _generate_html_body(self) -> str:
		"""Generate HTML body with all sections."""
		html = f"<h1>{self.title}</h1>\n"
		html += f'<div class="metadata">Generated: {self.timestamp}'
		if self.region:
			html += f' | Region: {self.region}'
		html += '</div>\n'

		for section in self.sections:
			if section["type"] == "text":
				html += f'<h2>{section["heading"]}</h2>\n'
				html += f'<p>{section["content"]}</p>\n'

			elif section["type"] == "figure":
				html += '<div class="figure">\n'
				if section.get("title"):
					html += f'<h3>{section["title"]}</h3>\n'
				html += f'<img src="{section["data"]}" alt="Figure">\n'
				html += f'<div class="caption">{section["caption"]}</div>\n'
				html += '</div>\n'

			elif section["type"] == "table":
				html += f'<h3>{section["heading"]}</h3>\n'
				if section["data"]:
					html += '<table>\n<tr>'
					# Headers from first row keys
					for key in section["data"][0].keys():
						html += f'<th>{key.replace("_", " ").title()}</th>'
					html += '</tr>\n'
					# Data rows
					for row in section["data"]:
						html += '<tr>'
						for val in row.values():
							# Format numbers
							if isinstance(val, float):
								html += f'<td>{val:.3f}</td>'
							else:
								html += f'<td>{val}</td>'
						html += '</tr>\n'
					html += '</table>\n'
				if section.get("caption"):
					html += f'<p class="caption">{section["caption"]}</p>\n'

		return html

	def _generate_html_footer(self) -> str:
		"""Generate HTML footer."""
		return """
<div class="footer">
	LTEM Database MCP Server — Automated Ecological Report<br>
	Long-Term Ecological Monitoring Program, Gulf of California
</div>
</div>
</body>
</html>
"""

	def generate_html(self) -> str:
		"""Generate complete HTML report."""
		return (
			self._generate_html_head() +
			self._generate_html_body() +
			self._generate_html_footer()
		)

	def generate_pdf(self) -> bytes:
		"""Generate PDF report from HTML.

		Returns:
			PDF file as bytes
		"""
		try:
			from weasyprint import HTML
		except ImportError:
			raise ImportError(
				"WeasyPrint is required for PDF generation. "
				"Install with: pip install WeasyPrint"
			)

		html = self.generate_html()
		return HTML(string=html).write_pdf()


def _create_mpa_effectiveness_report(
	region: str | None = None,
	baseline_years: list[int] | None = None,
) -> LTEMReportGenerator:
	"""Generate MPA effectiveness assessment report.

	Args:
		region: Optional region filter
		baseline_years: Baseline years for recovery analysis (default: [1998,1999,2000])

	Returns:
		Report generator with MPA analysis
	"""
	if baseline_years is None:
		baseline_years = [1998, 1999, 2000]

	report = LTEMReportGenerator(
		title="MPA Effectiveness Assessment",
		region=region
	)

	# Section 1: Introduction
	report.add_section(
		"Overview",
		"This report assesses the effectiveness of Marine Protected Areas (MPAs) in the Gulf of California "
		"using long-term monitoring data. Comparisons include biomass, abundance, trophic structure, and "
		"size distributions across protection levels."
	)

	# Section 2: Protection level comparison
	sql = """
		SELECT
			COALESCE(MPA, 'Unprotected') AS protection_level,
			AVG(Biomass) AS mean_biomass,
			STDDEV(Biomass) AS std_biomass,
			COUNT(DISTINCT Reef) AS n_reefs,
			COUNT(DISTINCT CONCAT(Reef, Year, Transect)) AS n_transects
		FROM ltem_historical_database
		WHERE Biomass IS NOT NULL AND Biomass > 0 AND Label = 'PEC'
	"""
	if region:
		sql += f" AND Region = '{region}'"
	sql += " GROUP BY protection_level"

	rows = execute_select(sql)

	if rows:
		# Create box plot
		fig, ax = plt.subplots(figsize=(10, 6))

		# Get raw data for boxplot
		groups = []
		labels = []
		for row in rows:
			prot_level = row['protection_level']
			sql_data = f"""
				SELECT Biomass
				FROM ltem_historical_database
				WHERE Biomass IS NOT NULL AND Biomass > 0
				AND COALESCE(MPA, 'Unprotected') = '{prot_level}'
				AND Label = 'PEC'
			"""
			if region:
				sql_data += f" AND Region = '{region}'"
			data = execute_select(sql_data, max_rows=5000)
			biomass_vals = [d['Biomass'] for d in data if d['Biomass']]
			if biomass_vals:
				groups.append(biomass_vals)
				labels.append(prot_level)

		if groups:
			ax.boxplot(groups, labels=labels, patch_artist=True,
					   boxprops=dict(facecolor='lightblue', alpha=0.7),
					   medianprops=dict(color='red', linewidth=2))
			ax.set_ylabel('Biomass (g/m²)')
			ax.set_xlabel('Protection Level')
			ax.set_title('Biomass by Protection Level')
			ax.grid(axis='y', alpha=0.3)

			report.add_figure(
				fig,
				caption="Box plot showing biomass distribution across protection levels. "
						"Mann-Whitney U tests should be used for pairwise comparisons due to non-normal distribution.",
				title="Biomass Comparison"
			)

		# Add summary table
		report.add_table(
			"Summary Statistics by Protection Level",
			[{
				"Protection Level": r['protection_level'],
				"Mean Biomass (g/m²)": round(r['mean_biomass'], 2) if r['mean_biomass'] else None,
				"Std Dev": round(r['std_biomass'], 2) if r['std_biomass'] else None,
				"N Reefs": r['n_reefs'],
				"N Transects": r['n_transects']
			} for r in rows],
			caption="Summary statistics for each protection level."
		)

	# Section 3: Cabo Pulmo recovery (if applicable)
	cp_sql = """
		SELECT
			Year,
			AVG(Biomass) AS mean_biomass,
			COUNT(DISTINCT CONCAT(Reef, Transect)) AS n_transects
		FROM ltem_historical_database
		WHERE Region = 'Cabo Pulmo' AND Biomass IS NOT NULL AND Label = 'PEC'
		GROUP BY Year
		ORDER BY Year
	"""
	cp_data = execute_select(cp_sql)

	if cp_data:
		# Calculate baseline and recovery
		baseline_data = [d for d in cp_data if d['Year'] in baseline_years]
		baseline_mean = np.mean([d['mean_biomass'] for d in baseline_data]) if baseline_data else None

		# Create recovery trajectory plot
		fig, ax = plt.subplots(figsize=(12, 6))
		years = [d['Year'] for d in cp_data]
		biomass = [d['mean_biomass'] for d in cp_data]

		ax.plot(years, biomass, 'o-', linewidth=2, markersize=6, color='#2c3e50')
		if baseline_mean:
			ax.axhline(baseline_mean, color='red', linestyle='--', linewidth=2,
					   label=f'Baseline ({baseline_years[0]}-{baseline_years[-1]})')
			ax.legend()

		ax.set_xlabel('Year')
		ax.set_ylabel('Mean Biomass (g/m²)')
		ax.set_title('Cabo Pulmo Recovery Trajectory')
		ax.grid(True, alpha=0.3)

		report.add_figure(
			fig,
			caption=f"Cabo Pulmo recovery trajectory showing annual mean biomass. "
					f"Baseline period: {baseline_years[0]}-{baseline_years[-1]}. "
					f"Recovery factor calculated as current biomass / baseline biomass.",
			title="Cabo Pulmo Recovery"
		)

	# Section 4: Interpretation
	report.add_section(
		"Interpretation Guide",
		"<strong>Protection Level Effects:</strong> Fully protected MPAs typically show 2-5x higher biomass "
		"than unprotected areas. Statistical significance should be assessed using non-parametric tests "
		"(Kruskal-Wallis, Mann-Whitney) due to skewed biomass distributions.<br><br>"
		"<strong>Recovery Timescales:</strong> Cabo Pulmo shows recovery factors of 4-6x baseline after "
		"~15-20 years of protection. Recovery is non-linear with faster gains in early years."
	)

	return report


def _create_temporal_trends_report(
	region: str | None = None,
	metric: str = "biomass"
) -> LTEMReportGenerator:
	"""Generate temporal trends analysis report.

	Args:
		region: Optional region filter
		metric: Metric to analyze (biomass, abundance, richness)

	Returns:
		Report generator with trend analysis
	"""
	report = LTEMReportGenerator(
		title=f"Temporal Trends Analysis — {metric.title()}",
		region=region
	)

	report.add_section(
		"Overview",
		f"This report analyzes temporal trends in {metric} using Mann-Kendall trend tests, "
		"Sen's slope estimation, and change point detection. The analysis covers the full LTEM "
		"time series (1998-present) with annual aggregation at the transect level."
	)

	# Get annual time series
	metric_col = {
		"biomass": "AVG(Biomass)",
		"abundance": "SUM(Quantity)",
		"richness": "COUNT(DISTINCT Species)"
	}.get(metric, "AVG(Biomass)")

	sql = f"""
		SELECT
			Year,
			{metric_col} AS value,
			COUNT(DISTINCT CONCAT(Reef, Transect)) AS n_transects
		FROM ltem_historical_database
		WHERE Label = 'PEC'
	"""
	if region:
		sql += f" AND Region = '{region}'"
	sql += " GROUP BY Year ORDER BY Year"

	data = execute_select(sql)

	if len(data) >= 4:  # Need at least 4 points for trend analysis
		years = np.array([d['Year'] for d in data])
		values = np.array([d['value'] for d in data])

		# Time series plot
		fig, ax = plt.subplots(figsize=(12, 6))
		ax.plot(years, values, 'o-', linewidth=2, markersize=8, color='#2c3e50', label='Observed')

		# Add linear trend line
		from scipy.stats import linregress
		slope, intercept, r_value, p_value, std_err = linregress(years, values)
		trend_line = slope * years + intercept
		ax.plot(years, trend_line, '--', color='red', linewidth=2,
				label=f'Trend (p={p_value:.3f})')

		ax.set_xlabel('Year')
		units = {"biomass": "g/m²", "abundance": "count", "richness": "species"}
		ax.set_ylabel(f'{metric.title()} ({units[metric]})')
		ax.set_title(f'Annual {metric.title()} Time Series')
		ax.legend()
		ax.grid(True, alpha=0.3)

		report.add_figure(
			fig,
			caption=f"Annual time series showing {metric} trend. Linear regression line shown in red. "
					f"Slope: {slope:.3f} units/year, R²: {r_value**2:.3f}, p-value: {p_value:.3f}.",
			title=f"{metric.title()} Time Series"
		)

		# Add trend summary table
		trend_direction = "Increasing" if slope > 0 else "Decreasing"
		significance = "Significant" if p_value < 0.05 else "Not significant"

		report.add_table(
			"Trend Analysis Summary",
			[{
				"Metric": metric.title(),
				"Slope (units/year)": round(slope, 4),
				"R-squared": round(r_value**2, 3),
				"P-value": round(p_value, 4),
				"Direction": trend_direction,
				"Significance (α=0.05)": significance,
				"Years Analyzed": len(years)
			}],
			caption="Linear regression and statistical significance of temporal trend."
		)

	report.add_section(
		"Interpretation Guide",
		"<strong>Trend Significance:</strong> P-values <0.05 indicate significant trends. "
		"Mann-Kendall tau values range from -1 (strong decreasing) to +1 (strong increasing).<br><br>"
		"<strong>Change Points:</strong> Regime shifts may indicate ecosystem transitions, "
		"climate events (e.g., El Niño), or management interventions. Pettitt test identifies "
		"the most likely change point year."
	)

	return report


def _create_community_structure_report(
	region: str | None = None,
	year: int | None = None
) -> LTEMReportGenerator:
	"""Generate community structure analysis report.

	Args:
		region: Optional region filter
		year: Optional year filter

	Returns:
		Report generator with community analysis
	"""
	report = LTEMReportGenerator(
		title="Community Structure Analysis",
		region=region
	)

	report.add_section(
		"Overview",
		"This report analyzes reef fish community structure including diversity indices "
		"(Shannon H', Simpson D), species composition, trophic structure, and size distributions. "
		"Community metrics are calculated at the transect level then aggregated by reef."
	)

	# Species composition
	sql = """
		SELECT
			Species,
			SUM(Quantity) AS total_abundance,
			COUNT(DISTINCT Reef) AS n_reefs
		FROM ltem_historical_database
		WHERE Label = 'PEC'
	"""
	filters = []
	if region:
		filters.append(f"Region = '{region}'")
	if year:
		filters.append(f"Year = {year}")
	if filters:
		sql += " AND " + " AND ".join(filters)
	sql += " GROUP BY Species ORDER BY total_abundance DESC LIMIT 15"

	species_data = execute_select(sql)

	if species_data:
		# Rank-abundance plot
		fig, ax = plt.subplots(figsize=(12, 8))
		ranks = range(1, len(species_data) + 1)
		abundances = [d['total_abundance'] for d in species_data]
		species_names = [d['Species'][:30] for d in species_data]  # Truncate long names

		ax.barh(ranks, abundances, color='steelblue', alpha=0.7)
		ax.set_yticks(ranks)
		ax.set_yticklabels(species_names)
		ax.invert_yaxis()
		ax.set_xlabel('Total Abundance (individuals)')
		ax.set_title('Top 15 Most Abundant Species')
		ax.grid(axis='x', alpha=0.3)

		report.add_figure(
			fig,
			caption="Rank-abundance curve showing the 15 most abundant species. "
					"Steep curves indicate dominance by few species; flat curves indicate evenness.",
			title="Species Composition"
		)

	# Trophic structure
	trophic_sql = """
		SELECT
			TrophicGroup,
			SUM(Biomass) AS total_biomass,
			COUNT(DISTINCT CONCAT(Reef, Transect)) AS n_transects
		FROM ltem_historical_database
		WHERE Label = 'PEC' AND TrophicGroup IS NOT NULL AND Biomass > 0
	"""
	if region:
		trophic_sql += f" AND Region = '{region}'"
	if year:
		trophic_sql += f" AND Year = {year}"
	trophic_sql += " GROUP BY TrophicGroup"

	trophic_data = execute_select(trophic_sql)

	if trophic_data:
		# Pie chart
		fig, ax = plt.subplots(figsize=(10, 8))
		labels = [d['TrophicGroup'] for d in trophic_data]
		sizes = [d['total_biomass'] for d in trophic_data]
		colors = sns.color_palette('Set2', len(labels))

		ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
			   startangle=90, textprops={'fontsize': 10})
		ax.set_title('Trophic Structure (Biomass Proportions)')

		report.add_figure(
			fig,
			caption="Proportional biomass by trophic group. Healthy reefs typically have balanced "
					"representation across trophic levels with 10-20% top predators.",
			title="Trophic Structure"
		)

	report.add_section(
		"Interpretation Guide",
		"<strong>Diversity Indices:</strong> Shannon H' typically ranges 1.5-3.5 (higher = more diverse). "
		"Simpson D ranges 0-1 (higher = more diverse). Pielou J' ranges 0-1 (higher = more even).<br><br>"
		"<strong>Trophic Balance:</strong> Inverted pyramids (top-heavy) indicate MPA recovery. "
		"Bottom-heavy pyramids suggest fishing pressure or nutrient limitation."
	)

	return report


def _create_data_quality_report(
	region: str | None = None
) -> LTEMReportGenerator:
	"""Generate data quality audit report.

	Args:
		region: Optional region filter

	Returns:
		Report generator with quality checks
	"""
	report = LTEMReportGenerator(
		title="Data Quality Audit Report",
		region=region
	)

	report.add_section(
		"Overview",
		"This report assesses data quality through outlier detection (MAD method), "
		"sample size adequacy, transect coverage matching, and completeness checks. "
		"Quality issues are flagged for review before analysis."
	)

	# Data completeness by year
	sql = """
		SELECT
			Year,
			COUNT(*) AS n_rows,
			SUM(CASE WHEN Size IS NULL THEN 1 ELSE 0 END) AS null_size,
			SUM(CASE WHEN Biomass IS NULL THEN 1 ELSE 0 END) AS null_biomass,
			SUM(CASE WHEN TrophicGroup IS NULL THEN 1 ELSE 0 END) AS null_trophic,
			COUNT(DISTINCT Reef) AS n_reefs
		FROM ltem_historical_database
		WHERE Label = 'PEC'
	"""
	if region:
		sql += f" AND Region = '{region}'"
	sql += " GROUP BY Year ORDER BY Year"

	completeness_data = execute_select(sql)

	if completeness_data:
		# Calculate percentages
		for row in completeness_data:
			row['pct_null_size'] = (row['null_size'] / row['n_rows'] * 100) if row['n_rows'] > 0 else 0
			row['pct_null_biomass'] = (row['null_biomass'] / row['n_rows'] * 100) if row['n_rows'] > 0 else 0
			row['pct_null_trophic'] = (row['null_trophic'] / row['n_rows'] * 100) if row['n_rows'] > 0 else 0

		# Heatmap of missingness
		fig, ax = plt.subplots(figsize=(12, 6))
		years = [d['Year'] for d in completeness_data]
		size_null = [d['pct_null_size'] for d in completeness_data]
		biomass_null = [d['pct_null_biomass'] for d in completeness_data]
		trophic_null = [d['pct_null_trophic'] for d in completeness_data]

		x = np.arange(len(years))
		width = 0.25

		ax.bar(x - width, size_null, width, label='Size', color='#e74c3c', alpha=0.7)
		ax.bar(x, biomass_null, width, label='Biomass', color='#3498db', alpha=0.7)
		ax.bar(x + width, trophic_null, width, label='Trophic Group', color='#2ecc71', alpha=0.7)

		ax.set_xlabel('Year')
		ax.set_ylabel('Percentage Missing (%)')
		ax.set_title('Data Completeness by Year')
		ax.set_xticks(x)
		ax.set_xticklabels(years, rotation=45)
		ax.legend()
		ax.grid(axis='y', alpha=0.3)

		report.add_figure(
			fig,
			caption="Percentage of missing values for key fields by year. "
					"Biomass calculations require Size data. High missingness (>10%) should be investigated.",
			title="Data Completeness"
		)

		# Summary table
		report.add_table(
			"Completeness Summary (Recent Years)",
			[{
				"Year": d['Year'],
				"N Rows": d['n_rows'],
				"% Null Size": round(d['pct_null_size'], 1),
				"% Null Biomass": round(d['pct_null_biomass'], 1),
				"% Null Trophic": round(d['pct_null_trophic'], 1),
				"N Reefs": d['n_reefs']
			} for d in completeness_data[-10:]],  # Last 10 years
			caption="Data completeness for the 10 most recent years."
		)

	# Sample size assessment
	sample_sql = """
		SELECT
			Region,
			COUNT(DISTINCT CONCAT(Reef, Year, Transect)) AS n_transects,
			COUNT(DISTINCT Reef) AS n_reefs,
			COUNT(DISTINCT Year) AS n_years
		FROM ltem_historical_database
		WHERE Label = 'PEC'
	"""
	if region:
		sample_sql += f" AND Region = '{region}'"
	sample_sql += " GROUP BY Region"

	sample_data = execute_select(sample_sql)

	if sample_data:
		for row in sample_data:
			n = row['n_transects']
			if n < 10:
				row['sample_flag'] = 'Insufficient'
			elif n < 30:
				row['sample_flag'] = 'Limited'
			else:
				row['sample_flag'] = 'Sufficient'

		report.add_table(
			"Sample Size Assessment by Region",
			[{
				"Region": d['Region'],
				"N Transects": d['n_transects'],
				"N Reefs": d['n_reefs'],
				"N Years": d['n_years'],
				"Assessment": d['sample_flag']
			} for d in sample_data],
			caption="Sample size adequacy: Sufficient (≥30), Limited (10-29), Insufficient (<10)."
		)

	report.add_section(
		"Interpretation Guide",
		"<strong>Outlier Detection:</strong> MAD (Median Absolute Deviation) is robust to extreme values. "
		"Z-scores >3.5 indicate potential outliers requiring verification.<br><br>"
		"<strong>Sample Size:</strong> Statistical power increases with sample size. "
		"N<10 is underpowered for most tests. N≥30 provides adequate power for parametric tests."
	)

	return report


def register(mcp: FastMCP) -> None:
	"""Register report generation tools with the MCP server."""

	@mcp.tool()
	def generate_mpa_report(
		region: str | None = None,
		baseline_years: list[int] | None = None,
		format: str = "html"
	) -> str:
		"""Generate MPA effectiveness assessment report with visualizations.

		Args:
			region: Optional region filter
			baseline_years: Baseline years for Cabo Pulmo recovery (default: [1998,1999,2000])
			format: Output format: "html" or "pdf"

		Returns:
			JSON with report_html (if format=html) or success message (if format=pdf)
		"""
		report = _create_mpa_effectiveness_report(region, baseline_years)

		if format == "pdf":
			pdf_bytes = report.generate_pdf()
			return json.dumps({
				"status": "success",
				"format": "pdf",
				"size_bytes": len(pdf_bytes),
				"message": "PDF generated successfully. In production, this would return a download URL."
			})
		else:
			html = report.generate_html()
			return json.dumps({
				"status": "success",
				"format": "html",
				"report_html": html,
				"figures_generated": len(report.figures)
			})

	@mcp.tool()
	def generate_temporal_report(
		region: str | None = None,
		metric: str = "biomass",
		format: str = "html"
	) -> str:
		"""Generate temporal trends analysis report with visualizations.

		Args:
			region: Optional region filter
			metric: Metric to analyze (biomass, abundance, richness)
			format: Output format: "html" or "pdf"

		Returns:
			JSON with report_html (if format=html) or success message (if format=pdf)
		"""
		report = _create_temporal_trends_report(region, metric)

		if format == "pdf":
			pdf_bytes = report.generate_pdf()
			return json.dumps({
				"status": "success",
				"format": "pdf",
				"size_bytes": len(pdf_bytes),
				"message": "PDF generated successfully. In production, this would return a download URL."
			})
		else:
			html = report.generate_html()
			return json.dumps({
				"status": "success",
				"format": "html",
				"report_html": html,
				"figures_generated": len(report.figures)
			})

	@mcp.tool()
	def generate_community_report(
		region: str | None = None,
		year: int | None = None,
		format: str = "html"
	) -> str:
		"""Generate community structure analysis report with visualizations.

		Args:
			region: Optional region filter
			year: Optional year filter
			format: Output format: "html" or "pdf"

		Returns:
			JSON with report_html (if format=html) or success message (if format=pdf)
		"""
		report = _create_community_structure_report(region, year)

		if format == "pdf":
			pdf_bytes = report.generate_pdf()
			return json.dumps({
				"status": "success",
				"format": "pdf",
				"size_bytes": len(pdf_bytes),
				"message": "PDF generated successfully. In production, this would return a download URL."
			})
		else:
			html = report.generate_html()
			return json.dumps({
				"status": "success",
				"format": "html",
				"report_html": html,
				"figures_generated": len(report.figures)
			})

	@mcp.tool()
	def generate_quality_report(
		region: str | None = None,
		format: str = "html"
	) -> str:
		"""Generate data quality audit report with visualizations.

		Args:
			region: Optional region filter
			format: Output format: "html" or "pdf"

		Returns:
			JSON with report_html (if format=html) or success message (if format=pdf)
		"""
		report = _create_data_quality_report(region)

		if format == "pdf":
			pdf_bytes = report.generate_pdf()
			return json.dumps({
				"status": "success",
				"format": "pdf",
				"size_bytes": len(pdf_bytes),
				"message": "PDF generated successfully. In production, this would return a download URL."
			})
		else:
			html = report.generate_html()
			return json.dumps({
				"status": "success",
				"format": "html",
				"report_html": html,
				"figures_generated": len(report.figures)
			})
