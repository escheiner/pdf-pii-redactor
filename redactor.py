"""
uv venv

# activating a venv in windows
.venv\Scripts\activate

# activating a venv in linux
source .venv/bin/activate

uv pip install package_name

"""

import fitz
import re
from pathlib import Path
import sys 
import spacy
import fitz  # PyMuPDF


ADDRESS_PATTERN = re.compile(r'\d+\s+\b(?:[A-Za-z]+\s){1,3}(Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Boulevard|Blvd|Drive|Dr|Court|Ct)\b')
APT_REGEX = re.compile(r'(apt|bldg|dept|fl|hngr|lot|pier|rm|ste|slip|trlr|unit|#)\.? *[a-z0-9-]+\b', re.IGNORECASE)
PO_BOX_REGEX = re.compile(r'P\.? ?O\.? *Box +\d+', re.IGNORECASE)
ROAD_REGEX = re.compile(r'(street|st|road|rd|avenue|ave|drive|dr|loop|court|ct|circle|cir|lane|ln|boulevard|blvd|way)\.?\b', re.IGNORECASE)
CREDIT_CARD_NUMBER_REGEX = re.compile(r'\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}|\d{4}[ -]?\d{6}[ -]?\d{4}\d?', re.IGNORECASE)
STREET_ADDRESS_REGEX = re.compile(r'(\d+\s*(\w+ ){1,2}' + ROAD_REGEX.pattern + r'(\s+' + APT_REGEX.pattern + r')?)|(' + PO_BOX_REGEX.pattern + r')', re.IGNORECASE)
ZIPCODE_REGEX = re.compile(r'\b\d{5}\b(-\d{4})?', re.IGNORECASE)
PHONE_NUMBER_REGEX = re.compile(r'(\(?\+?[0-9]{1,2}\)?[-. ]?)?(\(?[0-9]{3}\)?|[0-9]{3})[-. ]?([0-9]{3}[-. ]?[0-9]{4}|\b[A-Z0-9]{7}\b)', re.IGNORECASE)
IP_ADDRESS_REGEX = re.compile(r'(\d{1,3}(\.\d{1,3}){3}|[0-9A-F]{4}(:[0-9A-F]{4}){5}(::|(:0000)+))', re.IGNORECASE)
SSN_REGEX = re.compile(r'\b\d{3}[ -.]\d{2}[ -.]\d{4}\b', re.IGNORECASE)
EMAIL_REGEX = re.compile(r'([a-z0-9_\-.+]+)@\w+(\.\w+)*', re.IGNORECASE)
URL_REGEX = re.compile(r'([^\s:/?#]+):\/\/([^/?#\s]*)([^?#\s]*)(\?([^#\s]*))?(#([^\s]*))?', re.IGNORECASE)


# Function to mask PII with 'x' based on the length of the match
def mask_pii(text):
    regexes = [
        APT_REGEX, PO_BOX_REGEX, CREDIT_CARD_NUMBER_REGEX, STREET_ADDRESS_REGEX, ZIPCODE_REGEX, 
        PHONE_NUMBER_REGEX, IP_ADDRESS_REGEX, SSN_REGEX, EMAIL_REGEX, URL_REGEX
    ]
    
    # Function to replace the matched pattern with 'x' of the same length
    def mask_match(match):
        return 'x' * len(match.group())
    
    # Apply all regexes to the text
    for regex in regexes:
        text = re.sub(regex, mask_match, text)
    
    return text


nlp = spacy.load("en_core_web_md")

# python -m spacy download en_core_web_md

def replace_names_and_addresses(text: str) -> str:
    # Process the text using spaCy
    doc = nlp(text)

    # Create a list to hold the modified text
    modified_text = []

    # Keep track of the index in the original text
    last_index = 0

    # Loop through entities recognized by spaCy
    found = False
    for ent in doc.ents:
        # Append the text before the entity
        modified_text.append(text[last_index:ent.start_char])

        # Replace names (PERSON), locations (LOC), and geopolitical entities (GPE) with 'x' of matching length
        if ent.label_ in ["PERSON", "LOC"]:
            found = True
            # Replace with 'x' characters matching the entity length
            modified_text.append('x' * len(ent.text))
        else:
            # Keep the entity as is if it's not PERSON, GPE, or LOC
            modified_text.append(ent.text)

        # Update the last index to after this entity
        last_index = ent.end_char

    # Append any remaining text after the last entity
    modified_text.append(text[last_index:])

    # Join the modified text into a string
    modified_text = "".join(modified_text)

    # Apply regex-based address redaction on the modified text
    redacted_text = re.sub(ADDRESS_PATTERN, lambda match: 'x' * len(match.group()), modified_text)
    if not found:
        return mask_pii(text)
    return mask_pii(redacted_text)



def extract_text_dict_from_pdf(pdf_path):
    """
    Extract text dict from all pages in a PDF.
    
    Args:
        pdf_path (str): Path to the PDF file to extract text from.
        
    Returns:
        list: A list of text dictionaries, one for each page.
    """
    doc = fitz.open(pdf_path)
    text_dict_list = []
    
    for page_num in range(doc.page_count):
        page = doc[page_num]  # Get the page
        # Extract detailed text info as a dictionary
        text_dict = page.get_text("dict")
        text_dict_list.append(text_dict)
    
    doc.close()
    return text_dict_list


def convert_color(color):
    """
    Convert an integer color value to a tuple in the range 0 to 1 for RGB.
    
    Args:
        color (int): The color in 0xRRGGBB or 0xAARRGGBB format.
    
    Returns:
        tuple: A 3-tuple (R, G, B) with values between 0 and 1.
    """
    if isinstance(color, int):
        # Convert the integer to RGB (ignoring alpha if present)
        r = ((color >> 16) & 255) / 255
        g = ((color >> 8) & 255) / 255
        b = (color & 255) / 255
        return (r, g, b)
    # Default to black if color is not valid
    return (0, 0, 0)


def recreate_pdf_from_text_dict(text_dict_list, output_pdf_path):
    """
    Recreate a PDF from a list of text dictionaries.
    
    Args:
        text_dict_list (list): A list of text dictionaries, one for each page.
        output_pdf_path (str): The path to save the recreated PDF.
    """
    # Create a new PDF document
    new_doc = fitz.open()
    
    for text_dict in text_dict_list:
        # Create a new blank page with the same dimensions as the original
        page = new_doc.new_page(width=text_dict['width'], height=text_dict['height'])
        
        # Iterate over text blocks in the text_dict
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    # Extract text, position, and font details
                    text = replace_names_and_addresses(span["text"])
                    x = span["bbox"][0]
                    y = span["bbox"][1]
                    font = span.get("font", "Times-Roman")  # Fallback to Times-Roman if no font
                    size = span.get("size", 12)
                    color = span.get("color", 0)  # Default to black
                    
                    # Convert color to an RGB tuple
                    rgb_color = convert_color(color)
                    
                    # Try to use the original font; fallback to default if an error occurs
                    try:
                        page.insert_text((x, y), text, fontsize=size, fontname=font, color=rgb_color)
                    except Exception:
                        # Fallback to a default font if the specific font is not available
                        page.insert_text((x, y), text, fontsize=size, fontname="Times-Roman", color=(0, 0, 0))
    
    # Save the recreated PDF
    new_doc.save(output_pdf_path)
    new_doc.close()


def recreate_pdf_from_existing(pdf_path, output_pdf_path):
    """
    Extract text from an existing PDF and recreate it as a new PDF.
    
    Args:
        pdf_path (str): Path to the existing PDF file to read.
        output_pdf_path (str): Path to save the recreated PDF.
    """
    # Step 1: Extract text dicts from the original PDF
    text_dict_list = extract_text_dict_from_pdf(pdf_path)
    
    # Step 2: Recreate a new PDF using the extracted text dictionaries
    recreate_pdf_from_text_dict(text_dict_list, output_pdf_path)

# Usage Example:
# Assuming you have a multi-page PDF file "input.pdf"
# Call the function to read the PDF and recreate it




if __name__ == '__main__':
    input_pdf_file = sys.argv[1]
    output_pdf_file = sys.argv[1].replace(".pdf", "-recreate.pdf")
    print(output_pdf_file)
    recreate_pdf_from_existing(input_pdf_file, output_pdf_file)
    print("Done rec and produced")

# Exception: need font file or buffer


# conda install -c conda-forge spacy


