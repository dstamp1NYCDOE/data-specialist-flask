import os
import requests
import pandas as pd
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory for glossaries
GLOSSARIES_DIR = os.path.join("app", "scripts", "testing", "regents", "enl_glossaries", "glossaries")
GLOSSARIES_CSV = os.path.join(GLOSSARIES_DIR, "glossaries.csv")


def load_glossaries_config():
    """Load the glossaries configuration from CSV."""
    try:
        df = pd.read_csv(GLOSSARIES_CSV)
        return df
    except FileNotFoundError:
        logger.error(f"Glossaries CSV not found at {GLOSSARIES_CSV}")
        return pd.DataFrame(columns=["exam", "language", "url"])


def get_glossary_filename(exam, language):
    """Generate standardized filename for a glossary PDF."""
    return f"{exam}_{language}.pdf"


def get_glossary_path(exam, language):
    """Get full path for a glossary PDF."""
    filename = get_glossary_filename(exam, language)
    return os.path.join(GLOSSARIES_DIR, filename)


def download_glossary(exam, language, url):
    """
    Download a glossary PDF from URL and save with standardized naming.
    
    Args:
        exam: Name of the exam
        language: Language of the glossary
        url: URL to download from
    
    Returns:
        str: Path to downloaded file, or None if download failed
    """
    os.makedirs(GLOSSARIES_DIR, exist_ok=True)
    filepath = get_glossary_path(exam, language)
    
    # Skip if already downloaded
    if os.path.exists(filepath):
        logger.info(f"✓ {exam}_{language} already exists")
        return filepath
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        logger.info(f"✓ Downloaded {exam}_{language}")
        return filepath
    except Exception as e:
        logger.error(f"✗ Error downloading {exam}_{language}: {e}")
        return None


def download_all_glossaries():
    """
    Download all glossaries from the CSV configuration.
    
    Returns:
        dict: Summary of download results
    """
    config_df = load_glossaries_config()
    
    if config_df.empty:
        logger.warning("No glossaries configured in CSV")
        return {"success": 0, "failed": 0, "skipped": 0}
    
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    for _, row in config_df.iterrows():
        exam = row['exam']
        language = row['language']
        url = row['url']
        
        filepath = get_glossary_path(exam, language)
        
        if os.path.exists(filepath):
            results["skipped"] += 1
            logger.info(f"Skipped {exam}_{language} (already exists)")
        else:
            result = download_glossary(exam, language, url)
            if result:
                results["success"] += 1
            else:
                results["failed"] += 1
    
    logger.info(f"Download complete: {results['success']} success, "
                f"{results['failed']} failed, {results['skipped']} skipped")
    return results


def create_watermark(text, position='header'):
    """
    Create a watermark PDF overlay with the given text.
    
    Args:
        text: Text to display
        position: 'header', 'footer', or 'both'
    
    Returns:
        PdfReader: PDF with watermark
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set up text style
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 9)
    
    # Add header
    if position in ['header', 'both']:
        c.drawCentredString(width / 2, height - 30, text)
    
    # Add footer
    if position in ['footer', 'both']:
        c.drawCentredString(width / 2, 30, text)
    
    c.save()
    buffer.seek(0)
    return PdfReader(buffer)


def create_blank_page():
    """Create a blank PDF page."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.showPage()
    c.save()
    buffer.seek(0)
    return PdfReader(buffer)


def create_error_page(student_info, missing_glossaries):
    """
    Create an error page listing missing glossaries.
    
    Args:
        student_info: Dict with 'last_name', 'first_name', 'student_id'
        missing_glossaries: List of tuples (exam, language)
    
    Returns:
        PdfReader: PDF with error page
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 1 * inch, "GLOSSARIES NOT AVAILABLE")
    
    # Student info
    c.setFont("Helvetica", 12)
    student_text = f"Student: {student_info['last_name']}, {student_info['first_name']} ({student_info['student_id']})"
    c.drawCentredString(width / 2, height - 1.5 * inch, student_text)
    
    # Missing glossaries header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1 * inch, height - 2.5 * inch, "The following glossaries could not be included:")
    
    # List missing glossaries
    c.setFont("Helvetica", 10)
    y_position = height - 3 * inch
    for exam, language in missing_glossaries:
        c.drawString(1.5 * inch, y_position, f"• {exam} ({language})")
        y_position -= 0.3 * inch
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return PdfReader(buffer)


def add_watermark_to_pdf(pdf_path, watermark_text, position='header'):
    """
    Add watermark to all pages of a PDF.
    
    Args:
        pdf_path: Path to input PDF
        watermark_text: Text for watermark
        position: 'header', 'footer', or 'both'
    
    Returns:
        BytesIO: Watermarked PDF in memory
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    watermark = create_watermark(watermark_text, position)
    watermark_page = watermark.pages[0]
    
    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)
    
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def combine_glossaries(glossary_list, student_info, watermark_position='header', 
                      ensure_even_pages=True):
    """
    Combine multiple glossaries into one PDF with watermarking.
    
    Args:
        glossary_list: List of tuples (exam, language)
        student_info: Dict with 'last_name', 'first_name', 'student_id'
        watermark_position: 'header', 'footer', or 'both'
        ensure_even_pages: If True, add blank pages for double-sided printing
    
    Returns:
        BytesIO: Combined PDF, or None if no glossaries available
    """
    merger = PdfMerger()
    watermark_text = f"{student_info['last_name']}, {student_info['first_name']} ({student_info['student_id']})"
    blank_page_reader = create_blank_page() if ensure_even_pages else None
    
    available_glossaries = []
    missing_glossaries = []
    
    # Check which glossaries exist
    for exam, language in glossary_list:
        pdf_path = get_glossary_path(exam, language)
        if os.path.exists(pdf_path):
            available_glossaries.append((exam, language, pdf_path))
        else:
            missing_glossaries.append((exam, language))
            logger.warning(f"Missing glossary: {exam} ({language}) for student {student_info['student_id']}")
    
    # If no glossaries available at all, return None
    if not available_glossaries:
        logger.error(f"No glossaries available for student {student_info['student_id']}")
        return None
    
    # Add error page if some glossaries are missing
    if missing_glossaries:
        error_page = create_error_page(student_info, missing_glossaries)
        merger.append(error_page)
        logger.info(f"Added error page for {len(missing_glossaries)} missing glossaries")
    
    # Add each available glossary with watermark
    for exam, language, pdf_path in available_glossaries:
        try:
            # Watermark the PDF
            watermarked_pdf = add_watermark_to_pdf(pdf_path, watermark_text, watermark_position)
            
            # Check page count
            reader = PdfReader(watermarked_pdf)
            page_count = len(reader.pages)
            
            # Add to merger
            watermarked_pdf.seek(0)  # Reset buffer position
            merger.append(watermarked_pdf)
            logger.info(f"Added {exam}_{language} ({page_count} pages)")
            
            # Add blank page if odd number of pages
            if ensure_even_pages and page_count % 2 == 1:
                merger.append(blank_page_reader, pages=(0, 1))
                logger.info(f"  → Added blank page for double-sided printing")
            
        except Exception as e:
            logger.error(f"Error adding {exam}_{language}: {e}")
    
    # Write to BytesIO
    output = BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    
    return output


def glossary_exists(exam, language):
    """Check if a glossary PDF exists for given exam and language."""
    return os.path.exists(get_glossary_path(exam, language))