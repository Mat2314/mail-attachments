""" Module reads PDF file and detects the given word in the given file."""

# Import libraries
from PIL import Image
import pytesseract
import sys
from pdf2image import convert_from_path
import os
import shutil
import time
import multiprocessing
import hashlib
from dotenv import load_dotenv

load_dotenv()

class InvoiceDetection(object):
    ERROR_LOGS_PATH = "./error_logs.txt"
    
    def __init__(self):
        self.image_counter = 0
        self.REQUIRED_FILE_EXTENSION = os.getenv("REQUIRED_FILE_EXTENSION", ".pdf")
    
    def convert_pdf_to_image(self, path_to_pdf:str):
        # Store all the pages of the PDF in a variable
        # See if it is possible to access the PDF
        # Some files might require password access, then raise an exception
        try:
            pages = convert_from_path(path_to_pdf, 500)
        except Exception as e:
            raise Exception(f"Could not convert PDF to image -> {e}")
            
        self.image_counter = 1
        
        # Create PDF file hash and name a tmp directory containing this hash to make sure 
        # That the directory is unique and processes will not interrupt each other
        pdf_file_hash = self.calculate_file_hash(path_to_pdf)
        pdf_directory_name = "_".join(["tmp", pdf_file_hash, "/"])
        self._create_directory_if_not_exists(pdf_directory_name)
        
        # Iterate through all the pages stored above
        for page in pages:
            # Declaring filename for each page of PDF as JPG
            # For each page, filename will be:
            # PDF page n -> page_n.jpg
            # etc.
            # The snippet of code thanks to: https://www.geeksforgeeks.org/python-reading-contents-of-pdf-using-ocr-optical-character-recognition/
            filename = pdf_directory_name + "page_"+str(self.image_counter)+".jpg"
            
            # Save the image of the page in system
            page.save(filename, 'JPEG')
            # os.chmod(filename, 0o666)

            # Increment the counter to update filename
            self.image_counter += 1
        
        return pdf_directory_name
    
    def calculate_file_hash(self, filepath: str):
        sha256_hash = hashlib.sha256()
        with open(filepath,"rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096),b""):
                sha256_hash.update(byte_block)
            
        return sha256_hash.hexdigest()

    def extract_text_from_images(self, directory_with_images: str):
        """Read the image and extract the text from it"""
        # Variable to get count of total number of pages
        filelimit = self.image_counter - 1
        extracted_text = ""

        # Iterate from 1 to total number of pages
        for i in range(1, filelimit + 1):
            filename = directory_with_images + "page_"+str(i)+".jpg"
                
            # Recognize the text as string in image using pytesserct
            text = str(((pytesseract.image_to_string(Image.open(filename)))))
            # Replace unwanted characters from the extracted text
            text = text.replace('-\n', '')
            
            # Add extracted text to the whole extracted text variable
            extracted_text = "\n".join([extracted_text, text])
        
            # Remove created page
            os.remove(filename)

        # Remove the directory
        os.rmdir(directory_with_images)
        return extracted_text
    
    def _create_directory_if_not_exists(self, path_to_directory: str):
        if not os.path.isdir(path_to_directory):
            os.mkdir(path_to_directory)
            # os.chmod(path_to_directory, 0o777)
    
    def _log_errors(self, subject: str, message):
        """Save PDF erros into a file to inspect errors later on."""
        header = "".join([5*'-', subject, " ", 5*'-', "\n"])
        
        with open(self.ERROR_LOGS_PATH, "a") as error_file:
            error_file.write(header)
            error_file.write(message)
            error_file.write("\n\n")
    
    def detect_data_from_pdf(self, browsed_string: str, path_to_pdf: str, save_files_to: str = "attachments/detected"):
        """Method is looking for a browsed_string in given pdf file. 
        When it is found, program moves the PDF file to given catalogue in path save_files_to.

        Args:
            browsed_string (str): Searched string in PDF file
            path_to_pdf (str): path to PDF to be analyzed
            save_files_to (str): path to directory where to move the PDF if the browsed_string was detected
        """
        # import wdb; wdb.set_trace();
        # save_files_to = os.path.dirname(os.path.realpath(__file__)) + f"/{save_files_to}"
        self._create_directory_if_not_exists(save_files_to)
        
        try:
            # Convert PDF to image and extract text from this image (or images)
            path_to_tmp_pdf_directory = self.convert_pdf_to_image(path_to_pdf)
        except Exception as e:
            # Log an error and do not proceed with file analysis
            self._log_errors("PDF conversion error", str(e))
            return
            
        extracted_text = self.extract_text_from_images(path_to_tmp_pdf_directory)
        
        # If the browsed string is present in extracted text move PDF file to given directory
        if browsed_string.lower() in extracted_text.lower():
            shutil.move(path_to_pdf, save_files_to)
        
    def multiprocessing_detect_data_from_pdf(self, browsed_string: str, save_files_to: str = "attachments/detected", catalogue_with_pdfs: str = "attachments/"):
        """Method uses multiprocessing to increase the performance of detecting data in PDF files."""
        # List arguments for each PDF file to proceed with the analysis
        listed_arguments = []
        
        catalogue_with_pdfs = os.path.dirname(os.path.realpath(__file__)) + f"/{catalogue_with_pdfs}"
        save_files_to = os.path.dirname(os.path.realpath(__file__)) + f"/{save_files_to}"
        self._create_directory_if_not_exists(save_files_to)
        
        # Go through all the files and create list of tuples as arguments for each PDF file
        for filename in os.listdir(catalogue_with_pdfs):
            if os.path.isfile(f"{catalogue_with_pdfs}{filename}") and filename.endswith(self.REQUIRED_FILE_EXTENSION):
                listed_arguments.append(
                    (browsed_string, f"{catalogue_with_pdfs}{filename}", save_files_to)
                )
        
        with multiprocessing.Pool() as pool:
            pool.starmap(self.detect_data_from_pdf, listed_arguments)

def measure_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        
        print(f"Executed in: {end-start}s")
    return wrapper

@measure_time
def check_performance():
    """Test execution performance by analyzing all the files from attachments/ catalogue"""
    catalogue = "attachments/"
    attachments = os.listdir(catalogue)
    
    invoice_detector = InvoiceDetection()
    for attachment in attachments:
        invoice_detector.detect_data_from_pdf("invoice", f"{catalogue}{attachment}")

@measure_time
def check_multiprocessing_performance():
    invoice_detector = InvoiceDetection()
    invoice_detector.multiprocessing_detect_data_from_pdf("invoice")

if __name__ == '__main__':
    # invoice_detector = InvoiceDetection()
    # invoice_detector.detect_data_from_pdf("faktura", "...")
    # check_performance()
    
    check_multiprocessing_performance()