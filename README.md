# Book PDF to Markdown Tool

This is a simple command line tool that can convert book PDF files to Markdown format.

## Features

- Preserves the book's complete chapter and directory structure
- Supports conversion of multi-page PDF files
- Outputs the complete Markdown document structure, including preface/preface/chapter/section, etc.
- Removes header/footer/page number information
- Displays conversion progress bar
- Supports custom output file path

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python pdf2md.py <PDF file path>
```

Specify output file:
```bash
python pdf2md.py <PDF file path> <output file path>
```

## Examples

```bash
python pdf2md.py document.pdf
python pdf2md.py document.pdf output.md
```

## Precautions

- Conversion effect depends on the quality and format of the PDF file
- For scanned PDFs, it is recommended to use OCR tools for processing first
- The converted Markdown file may need to be manually adjusted for formatting
