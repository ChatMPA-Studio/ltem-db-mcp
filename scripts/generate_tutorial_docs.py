"""Generate HTML and PDF documentation from markdown tutorials.

This script converts all markdown tutorials in docs/user-guides/ to:
- Standalone HTML files with embedded CSS
- PDF files (requires WeasyPrint)

Usage:
    python scripts/generate_tutorial_docs.py
    python scripts/generate_tutorial_docs.py --format html  # HTML only
    python scripts/generate_tutorial_docs.py --format pdf   # PDF only
"""

import argparse
import sys
from pathlib import Path

try:
    import markdown
    from markdown.extensions import fenced_code, tables, toc
except ImportError:
    print("Error: markdown package not installed")
    print("Install with: pip install markdown")
    sys.exit(1)

# WeasyPrint is optional
try:
    from weasyprint import HTML as WeasyHTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError, Exception):
    WEASYPRINT_AVAILABLE = False
    WeasyHTML = None
    CSS = None


# HTML template with embedded CSS
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}

        .container {{
            background: white;
            padding: 60px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 0.5em;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.3em;
        }}

        h2 {{
            font-size: 1.8em;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 0.2em;
        }}

        h3 {{
            font-size: 1.4em;
            margin-top: 1.2em;
            margin-bottom: 0.5em;
            color: #34495e;
        }}

        h4 {{
            font-size: 1.2em;
            margin-top: 1em;
            margin-bottom: 0.5em;
            color: #34495e;
        }}

        p {{
            margin-bottom: 1em;
        }}

        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}

        em {{
            color: #7f8c8d;
        }}

        code {{
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }}

        pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 1.5em 0;
            line-height: 1.4;
        }}

        pre code {{
            background: none;
            color: #ecf0f1;
            padding: 0;
        }}

        ul, ol {{
            margin-bottom: 1em;
            margin-left: 2em;
        }}

        li {{
            margin-bottom: 0.5em;
        }}

        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 1.5em 0;
            color: #7f8c8d;
            font-style: italic;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5em 0;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}

        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 2em 0;
        }}

        .metadata {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 2em;
            font-size: 0.9em;
        }}

        .metadata strong {{
            color: #2c3e50;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""


def extract_title(markdown_text):
    """Extract title from first H1 heading."""
    for line in markdown_text.split('\n'):
        if line.startswith('# '):
            return line[2:].strip()
    return "Tutorial"


def markdown_to_html(md_file):
    """Convert markdown file to HTML string."""
    md_text = md_file.read_text(encoding='utf-8')

    # Extract title
    title = extract_title(md_text)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'fenced_code',
        'tables',
        'toc',
        'nl2br',
        'sane_lists'
    ])
    html_content = md.convert(md_text)

    # Wrap in template
    html = HTML_TEMPLATE.format(title=title, content=html_content)

    return html, title


def generate_html(md_file, output_dir):
    """Generate HTML file from markdown."""
    html, title = markdown_to_html(md_file)

    # Output filename
    html_file = output_dir / f"{md_file.stem}.html"
    html_file.write_text(html, encoding='utf-8')

    print(f"✓ Generated HTML: {html_file.name}")
    return html_file


def generate_pdf(md_file, output_dir):
    """Generate PDF file from markdown."""
    if not WEASYPRINT_AVAILABLE:
        print(f"⚠ Skipping PDF for {md_file.name} (WeasyPrint not installed)")
        return None

    html, title = markdown_to_html(md_file)

    # Output filename
    pdf_file = output_dir / f"{md_file.stem}.pdf"

    try:
        WeasyHTML(string=html).write_pdf(pdf_file)
        print(f"✓ Generated PDF: {pdf_file.name}")
        return pdf_file
    except Exception as e:
        print(f"✗ PDF generation failed for {md_file.name}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate HTML/PDF docs from markdown tutorials")
    parser.add_argument('--format', choices=['html', 'pdf', 'both'], default='both',
                        help='Output format (default: both)')
    parser.add_argument('--output', type=str, default='docs/user-guides/output',
                        help='Output directory (default: docs/user-guides/output)')
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).resolve().parent.parent
    guides_dir = project_root / 'docs' / 'user-guides'
    output_dir = project_root / args.output

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all markdown files (except README.md)
    md_files = sorted([f for f in guides_dir.glob('*.md') if f.name != 'README.md'])

    if not md_files:
        print("No markdown files found in docs/user-guides/")
        return

    print(f"\nFound {len(md_files)} tutorial(s) to convert")
    print(f"Output directory: {output_dir}\n")

    # Generate documentation
    html_count = 0
    pdf_count = 0

    for md_file in md_files:
        print(f"Processing: {md_file.name}")

        if args.format in ['html', 'both']:
            if generate_html(md_file, output_dir):
                html_count += 1

        if args.format in ['pdf', 'both']:
            if generate_pdf(md_file, output_dir):
                pdf_count += 1

        print()

    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    if args.format in ['html', 'both']:
        print(f"HTML files generated: {html_count}")
    if args.format in ['pdf', 'both']:
        if WEASYPRINT_AVAILABLE:
            print(f"PDF files generated: {pdf_count}")
        else:
            print("PDF generation skipped (install WeasyPrint: pip install WeasyPrint)")
    print(f"\nOutput location: {output_dir}")
    print("\n✓ Documentation generation complete!")


if __name__ == "__main__":
    main()
