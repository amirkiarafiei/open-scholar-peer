#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "markitdown",
# ]
# ///
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_pdf.py <pdf_path> [output_path]", file=sys.stderr)
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: file not found at '{pdf_path}'", file=sys.stderr)
        sys.exit(1)
        
    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(pdf_path)
        
        if len(sys.argv) >= 3:
            out_path = sys.argv[2]
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(result.text_content)
        else:
            print(result.text_content)
        sys.exit(0)
    except Exception as e:
        print(f"Error converting PDF: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
