from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from typing import List
import fitz  # PyMuPDF
from pathlib import Path
import re
import difflib # comparing text
from difflib import Differ
from reportlab.lib.pagesizes import letter  # creating PDFs
from reportlab.pdfgen import canvas
from reportlab.lib import colors


app = FastAPI()

def create_pdf(file_name, highlighted_text, page_width=500, page_height=750, line_height=14):
    c = canvas.Canvas(file_name, pagesize=letter)
    x_start = 40  # Left margin
    y_start = page_height  # Start height for text
    current_y = y_start  # Track the current Y position on the page
    current_line = ""  # Accumulate words for wrapping

    words = []  # Split words for wrapping

    for line in highlighted_text.split("<br>"):
        # Detect styles based on <span> tags
        if '<span style="color:red;">' in line:
            text = line.replace('<span style="color:red;">', "").replace("</span>", "")
            color = colors.red  # Set text color to red
        elif '<span style="color:green;">' in line:
            text = line.replace('<span style="color:green;">', "").replace("</span>", "")
            color = colors.green  # Set text color to green
        else:
            text = line  # Default text
            color = colors.black  # Reset to black for normal text

        # Split the text into words for wrapping
        words = text.split(" ")

        for word in words:
            # Measure the line width and check if the word fits
            if c.stringWidth(current_line + word, "Helvetica", 12) < page_width:
                current_line += word + " "  # Add the word to the current line
            else:
                # If the word doesn't fit, draw the current line
                c.setFillColor(color)
                c.drawString(x_start, current_y, current_line.strip())
                current_line = word + " "  # Start a new line
                current_y -= line_height  # Move cursor to the next line

                # Check if we've reached the end of the page
                if current_y < line_height:
                    c.showPage()  # Create a new page
                    c.setFont("Helvetica", 12)  # Reset font
                    current_y = y_start  # Reset cursor to top of the new page

        # Draw any remaining words in the current line
        if current_line.strip():
            c.setFillColor(color)
            c.drawString(x_start, current_y, current_line.strip())
            current_line = ""  # Reset the current line
            current_y -= line_height

            # Check if we've reached the end of the page
            if current_y < line_height:
                c.showPage()
                c.setFont("Helvetica", 12)
                current_y = y_start

    c.save()  # Save the PDF

    

def highlight_differences(text1, text2):
    
    differ = Differ()
    diff = list(differ.compare(text1.splitlines(), text2.splitlines()))
    highlighted_html = ""

    for line in diff:
       
        if line.startswith("- "):  # Deleted text
            highlighted_html += f'<span style="color:red;">{line[2:]}</span><br>'
        elif line.startswith("+ "):  # Added text
            highlighted_html += f'<span style="color:green;">{line[2:]}</span><br>'
        else:
            highlighted_html += f"{line[2:]}<br>"

    return highlighted_html


def preprocess_text(text: str) -> str:
    
    text = text.replace('\u00A0', ' ')  
    # Replace non-breaking space with regular space
    
    # Remove any characters that are not part of standard printable text
    text = ''.join(c for c in text if c.isprintable())
    
    # Replace multiple spaces, tabs, or newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # leading and trailing spaces
    text = text.strip()
    
    return text



def extract_text_from_pdf(file_data):
    # Open PDF file from binary data
    doc = fitz.open(stream=file_data, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text






@app.get("/", response_class=HTMLResponse)
def home():
    current_directory = Path(__file__).parent
    html_file_path = current_directory / "templates" / "upload_page.html"
    with open(html_file_path, "r", encoding="utf-8") as html_file:
        html_content = html_file.read()

    return HTMLResponse(content=html_content, status_code=200)

@app.post("/upload-pdf/")
async def upload_pdf(files: List[UploadFile] = File(...)):
    if len(files) != 2:
        return {"error": "Please upload exactly 2 PDF files."}
    
    file1 = files[0]
    file2 = files[1]

    try:
        
        data1 = await file1.read()  # Reading the content of the first file
        data2 = await file2.read()  # Reading the content of the second file

        pdf1_text = extract_text_from_pdf(data1)
        pdf2_text = extract_text_from_pdf(data2)

        highlighted_html = highlight_differences(pdf1_text, pdf2_text)
        create_pdf("output.pdf", highlighted_html)
        
        print("message PDF generated successfully!")
        return FileResponse("output.pdf", media_type="application/pdf", filename="comparison_result.pdf")

    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
   

