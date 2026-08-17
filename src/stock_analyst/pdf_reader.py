import pdfplumber

def load_pdf_with_markdown_tables(pdf_path: str) -> list[str]:
    full_content = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            full_content.append(f"--- Page {page_num} ---")
            
            # Extract tables on the page
            tables = page.extract_tables()
            
            if tables:
                for table in tables:
                    # Clean out None values and formatting quirks
                    clean_table = [[str(cell or "").strip().replace("\n", " ") for cell in row] for row in table]
                    
                    if not clean_table or not clean_table[0]:
                        continue
                        
                    # Format as Markdown Table
                    header = clean_table[0]
                    markdown_table = "| " + " | ".join(header) + " |\n"
                    markdown_table += "| " + " | ".join(["---"] * len(header)) + " |\n"
                    
                    for row in clean_table[1:]:
                        markdown_table += "| " + " | ".join(row) + " |\n"
                    
                    full_content.append(markdown_table)
            
            # Extract non-table text
            page_text = page.extract_text()
            if page_text:
                full_content.append(page_text)
    return full_content

def merge_pages(pages: list[str]) -> str:
    return "\n\n".join(pages)
