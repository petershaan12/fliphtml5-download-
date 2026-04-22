# FLIPHTML5 Downloader

A simple Python tool to download page images from FlipHTML5 publications and convert them into a PDF.

This project is designed to work with both older and newer FlipHTML5 structures, including modern page assets served as `.webp`.

## Features

- Downloads page images from FlipHTML5 publications
- Supports modern image formats such as `.webp`
- Converts downloaded pages into a single PDF
- Handles mixed image formats: `.webp`, `.jpg`, `.jpeg`, `.png`
- Does not rely on only one legacy config path
- Includes three modes:
  - `download` — download page images only
  - `pdf` — convert an existing image folder into PDF
  - `all` — download pages and convert them to PDF in one step

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## How to get the book ID

Use the FlipHTML5 publication code as the `bookID`.

For example, from this URL:

```text
https://online.fliphtml5.com/zgfij/shiq/
```

the `bookID` is:

```text
zgfij/shiq
```

## Usage

### 1. Download images

```bash
python main.py download zgfij/shiq 1 10
```

Options:

- `-n, --folderName` — output folder name
- `-t, --threads` — number of download threads

Example:

```bash
python main.py download zgfij/shiq 1 20 -n my-book -t 12
```

### 2. Convert downloaded images to PDF

```bash
python main.py pdf my-book 1 10
```

Options:

- `-o, --output` — output PDF file name or path

Example:

```bash
python main.py pdf my-book 1 20 -o my-book.pdf
```

### 3. Download and convert to PDF in one command

```bash
python main.py all zgfij/shiq 1 10
```

Options:

- `-n, --folderName` — output folder name
- `-t, --threads` — number of download threads
- `-o, --output` — output PDF file name or path

Example:

```bash
python main.py all zgfij/shiq 1 20 -n my-book -o my-book.pdf
```

## Notes

- Downloaded pages are saved using page numbers such as `1.webp`, `2.webp`, and so on.
- If a publication uses mixed image formats, PDF conversion will still work.
- Generated PDFs and downloaded images are ignored by Git via `.gitignore`.
