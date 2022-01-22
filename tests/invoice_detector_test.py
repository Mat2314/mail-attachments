import pytest
import pdfkit
import os
from invoice_detector import InvoiceDetection

@pytest.fixture(name="invoice_detection")
def fixture_invoice_detection():
    invoice_detection = InvoiceDetection()
    return invoice_detection

@pytest.fixture(name="example_pdf_filepath")
def fixture_example_pdf_file():
    # Create an example pdf if it doesn't exist yet
    path_to_pdf = "example.pdf"
    pdfkit.from_string("Hello world!", path_to_pdf)
    
    yield path_to_pdf
    
    os.remove(path_to_pdf)

def test_invoice_detection_initialization(invoice_detection):
    assert invoice_detection

def test_convert_pdf_to_image(invoice_detection, example_pdf_filepath):
    """Check if an image is being generated out of PDF"""
    pytest.skip()
    
    path_to_directory = invoice_detection.convert_pdf_to_image(example_pdf_filepath)
    assert os.path.isfile(path_to_directory + "page_1.jpg")
    
    # Remove temporary image
    os.remove(path_to_directory)

def test_extracted_text_from_image(invoice_detection, example_pdf_filepath):
    """Check if function extracts text form pdf image properly"""
    pytest.skip()
    path_to_image = invoice_detection.convert_pdf_to_image(example_pdf_filepath)
    
    extracted_text = invoice_detection.extract_text_from_images(path_to_image)
    assert "Hello world!" in extracted_text
    
    # Remove temporary image
    # os.remove(path_to_image)
