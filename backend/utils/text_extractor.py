import io
import pytesseract
from PIL import Image
from pypdf import PdfReader


class TextExtractor:
    @staticmethod
    def extract_from_file(file_content:bytes, filename:str) -> str:
        """
        Docstring for extract_from_file
        
        :param file_content: Description
        :type file_content: bytes
        :param filename: Description
        :type filename: str
        :return: Description
        :rtype: str

        detects file type and extracts text
        """
        filename = filename.lower()

        if(filename.endswith('.pdf')):
            return TextExtractor.read_pdf(file_content)
        elif(filename.endswith(('.png', '.jpg', '.jpeg', '.tiff',))):
            return TextExtractor.read_image(file_content)
        elif(filename.endswith('.txt')):
            return file_content.decode('utf-8', errors='ignore')
        else:
            raise ValueError("Unsupported file type for text extraction.")
    

    @staticmethod
    def read_pdf(content: bytes) -> str:
        """
        Docstring for read_pdf
        
        :param content: Description
        :type content: bytes
        :return: Description
        :rtype: str

        Reads texts from pdf file
        """

        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)

        text = []
        for page in reader.pages:
            extract = page.extract_text()
            if extract:
                text.append(extract)

        return "\n".join(text)
    
    @staticmethod
    def read_image(content: bytes) -> str:
        """
        Docstring for read_image
        
        :param content: Description
        :type content: bytes
        :return: Description
        :rtype: str

        Reads texts from image file using OCR
        """

        image = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(image)

        return text