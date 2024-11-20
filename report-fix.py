import os
import re
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image

def extract_data_from_text(text):
    """
    Extract the structured data from the raw text.
    """
    data = {
        'Name': '',
        'Patient ID': '',
        'Age': '',
        'Gender': '',
        'Test date': '',
        'Report date': '',
        'ECG Observation': []
    }
    
    # Regular expressions to match the data
    name_match = re.search(r"Name:\s*(.*?)Patient ID:", text)
    patient_id_match = re.search(r"Patient ID:\s*(.*?)Age:", text)
    age_match = re.search(r"Age:\s*(.*?)Gender:", text)
    gender_match = re.search(r"Gender:\s*(.*?)Test date:", text)
    test_date_match = re.search(r"Test date:\s*(.*?)Report date:", text)
    # Fix for report_date: Ensuring we capture the report date without grabbing ECG Observation part
    # Match "Report date:" and capture the date value, stop before "ECG Observation:" or end of string
    report_date_match = re.search(r"Report date:\s*(\S+)(?=\s*ECG\s*Observation:|$)", text)

    # If a match is found, process the Report date
    if report_date_match:
        report_date = report_date_match.group(1).strip()
        print(f"Report date: {report_date}")
        data['Report date'] = report_date
    else:
        print("Report date not found.")
    
    if name_match:
        data['Name'] = name_match.group(1).strip()
    if patient_id_match:
        data['Patient ID'] = patient_id_match.group(1).strip()
    if age_match:
        data['Age'] = age_match.group(1).strip()
    if gender_match:
        data['Gender'] = gender_match.group(1).strip()
    if test_date_match:
        data['Test date'] = test_date_match.group(1).strip()

    print(data['Report date'])

    # Look for the "ECG Observation" section
    ecg_section = ""
    if "ECG Observation:" in text or "ECGObservation:" in text:
        if "ECG Observation:" in text:
            ecg_section = text.split("ECG Observation:")[1].strip()
        else:
            ecg_section = text.split("ECGObservation:")[1].strip()

    # Now we process the ECG section
    if ecg_section:
        # Regex to find observations between 1., 2., 3., etc., and store them
        observations = []

        # Split the ECG section by numbered observations (1., 2., 3., etc.)
        parts = re.split(r'\d+\.\s', ecg_section)

        # Iterate through the split sections and ignore the first (empty) section
        for i, part in enumerate(parts[1:], 1):  # Skip the first element since it will be empty
            if part.strip():  # Only add non-empty parts
                observations.append(f"{i}. {part.strip()}")

        # Store the observations in data
        data['ECG Observation'] = observations

        # Print the formatted observations
        print("Formatted observations: ", data['ECG Observation'])
    else:
        print("No ECG Observation section found.")

    return data

def create_new_page(data, image_path):
    """
    Create a new PDF page with the structured data and append an image at the bottom.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Set initial margin and spacing
    top_margin = 10
    table_height = 50  # Height of the table area
    space_after_table = 5
    ecg_section_height = 5
    observation_section_height = 5
    space_between_lines = 5
    space_after_observations = 15
    image_margin = 30
    
    # Start the drawing from the top margin
    y_position = 750 - top_margin -20  # Start at the top of the page minus the top margin
    
    # Draw the table with data
    c.setFont("Helvetica", 10)
    
    # Table Outline - A single rectangle with 2 rows and 3 columns
    c.rect(40, y_position - 2 * table_height, 520, 2 * table_height)  # Outer border for the table

    # Column Lines (Vertical) to separate the table into 3 columns
    c.line(200, y_position - 2 * table_height, 200, y_position )  # First column separator
    c.line(370, y_position - 2 * table_height, 370, y_position )  # Second column separator

    # Horizontal Line to separate the two rows
    c.line(40, y_position - table_height, 560, y_position - table_height)  # Horizontal separator for rows

    # First Row (Name, Patient ID, Age)
    c.drawString(75, y_position - table_height +20, f"Name: {data['Name']}")
    c.drawString(225, y_position - table_height +20, f"Patient ID: {data['Patient ID']}")
    c.drawString(390, y_position - table_height +20, f"Age: {data['Age']}")

    # Update y_position after drawing the first row
    y_position -= table_height

    # Second Row (Gender, Test date, Report date)
    c.drawString(75, y_position - table_height + 20, f"Gender: {data['Gender']}")
    c.drawString(225, y_position - table_height + 20, f"Test date: {data['Test date']}")
    c.drawString(390, y_position - table_height + 20, f"Report date: {data['Report date']}")

    # Update y_position after drawing the second table
    y_position -= table_height + space_after_table + 20
    
    # Add space before ECG section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y_position, "ECG")
    ecg_text_width = c.stringWidth("ECG", "Helvetica", 12)
    c.line(40, y_position - 2, 40 + ecg_text_width, y_position - 2)  # Underline ECG
    y_position -= ecg_section_height + space_after_table + 20 # Space after ECG
    
    # Add "Observation" section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y_position, "Observation:")
    observation_text_width = c.stringWidth("Observation:", "Helvetica", 12)
    c.line(40, y_position - 2, 45 + observation_text_width, y_position - 2)  # Underline Observation
    y_position -= observation_section_height + space_after_table  # Space after "Observation"
    
    # Print each observation line by line
    c.setFont("Helvetica-Bold", 10)
    for observation in data['ECG Observation']:
        c.drawString(40, y_position - 20, observation)
        y_position -= space_between_lines + 15  # space between observations
    
    # Add space before the image
    y_position -= space_after_observations
    
    # Insert Image (resized to fit page width)
    img = Image.open(image_path)
    img_width, img_height = img.size
    img_aspect_ratio = img_width / img_height
    pdf_width = letter[0]
    img_pdf_width = pdf_width - 80  # margin on both sides
    img_pdf_height = img_pdf_width / img_aspect_ratio
    
    # Draw the image at the correct position
    c.drawImage(image_path, 40, y_position - 200, width=img_pdf_width, height=img_pdf_height)
    
    # Save the page
    c.showPage()
    c.save()
    
    buffer.seek(0)
    new_pdf = PdfReader(buffer)
    
    return new_pdf.pages[0]

def replace_second_page(input_pdf_path, new_page):
    """
    Replace the second page of the input PDF with the new page created from extracted data.
    """
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    
    # Keep the first page as it is
    writer.add_page(reader.pages[0])
    
    # Replace the second page with the newly generated page
    writer.add_page(new_page)
    
    # Add remaining pages if any
    for page_num in range(2, len(reader.pages)):
        writer.add_page(reader.pages[page_num])
    
    # Save the final PDF with the same name
    with open(input_pdf_path, 'wb') as output_file:
        writer.write(output_file)

def process_pdf_files(input_folder, image_path):
    """
    Process all the PDF files in the folder, replacing the second page with the newly formatted one.
    """
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.pdf'):
            input_pdf_path = os.path.join(input_folder, file_name)
            
            # Extract the text from the second page
            reader = PdfReader(input_pdf_path)
            second_page_text = reader.pages[1].extract_text()
            
            # Extract structured data from the second page
            extracted_data = extract_data_from_text(second_page_text)
            
            # Create a new page with the extracted data
            new_page = create_new_page(extracted_data, image_path)
            
            # Replace the second page in the original PDF with the new page
            replace_second_page(input_pdf_path, new_page)
            print(f"Processed {file_name}")

# Example usage
# These are the absolute paths, change it everytime as per our requirement.
input_folder = "E:/Testing/Report-side-cut-fix/Testing/program/input"
image_path = "E:/Testing/Report-side-cut-fix/Testing/program/drnalingmailsign.png"

process_pdf_files(input_folder, image_path)

