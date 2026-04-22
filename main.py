import argparse
import re
import threading
from collections import OrderedDict
from pathlib import Path
from queue import Queue
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image


IMAGE_EXTENSIONS = (".webp", ".jpg", ".jpeg", ".png")
DISCOVERY_PATHS = (
    "",
    "mobile/javascript/config.js",
    "javascript/config.js",
    "files/basic-html/index.html",
)


def normalize_book_id(value: str) -> str:
    return value.strip().strip("/")


def build_headers(book_id: str) -> dict:
    referer = f"https://online.fliphtml5.com/{book_id}/"
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": referer,
        "Accept": "*/*",
    }


def unique_preserve_order(values):
    return list(OrderedDict.fromkeys(values))


def infer_extension(url: str) -> str:
    path = urlparse(url).path.lower()
    suffix = Path(path).suffix
    return suffix if suffix in IMAGE_EXTENSIONS else ".img"


def extract_image_urls(text: str, base_url: str):
    text = text.replace("\\/", "/")
    patterns = [
        r"https://[^\s\"']+/files/large/[^\s\"']+?(?:\?.*?)?(?=[\"'])",
        r"/[^\s\"']*/files/large/[^\s\"']+?(?:\?.*?)?(?=[\"'])",
        r"files/large/[^\s\"']+?(?:\?.*?)?(?=[\"'])",
        r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*/files/large/[^\s\"']+?(?:\?.*?)?(?=[\"'])",
    ]

    found = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            lowered = match.lower()
            if any(lowered.endswith(ext) or f"{ext}?" in lowered for ext in IMAGE_EXTENSIONS):
                found.append(urljoin(base_url, match.lstrip("/")))

    cleaned = []
    for url in unique_preserve_order(found):
        parsed = urlparse(url)
        if "/files/large/" not in parsed.path:
            continue
        if Path(parsed.path).suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        cleaned.append(url)
    return cleaned


def get_pages(session: requests.Session, book_id: str):
    print("[*] Discovering page image list...")
    base_url = f"https://online.fliphtml5.com/{book_id}/"
    attempted = []

    for relative_path in DISCOVERY_PATHS:
        target = urljoin(base_url, relative_path)
        attempted.append(target)
        try:
            response = session.get(target, timeout=20)
            if response.status_code != 200:
                continue
        except requests.RequestException:
            continue

        pages = extract_image_urls(response.text, base_url)
        if pages:
            print(f"[+] Found {len(pages)} page image URLs from {target}")
            return pages

    joined_attempts = "\n    - ".join(attempted)
    raise RuntimeError(
        "Gagal nemu daftar halaman. Endpoint lama config.js kemungkinan sudah berubah. "
        f"Sudah dicoba:\n    - {joined_attempts}"
    )


def download_image(session: requests.Session, folder: Path, pages, page_number: int, print_lock: threading.Lock):
    try:
        source_url = pages[page_number - 1]
    except IndexError:
        with print_lock:
            print(f"[-] Page {page_number} di luar range daftar halaman ({len(pages)}).")
        return

    extension = infer_extension(source_url)
    output_path = folder / f"{page_number}{extension}"

    if output_path.exists() and output_path.stat().st_size > 0:
        with print_lock:
            print(f"[=] Skip page {page_number} (sudah ada)")
        return

    try:
        response = session.get(source_url, timeout=30)
        response.raise_for_status()
        output_path.write_bytes(response.content)
        with print_lock:
            print(f"[+] Downloaded page {page_number} -> {output_path.name}")
    except requests.RequestException as exc:
        with print_lock:
            print(f"[-] Error page {page_number}: {exc}")


def download_book(book_id: str, start: int, end: int, folder_name: str | None, threads: int):
    book_id = normalize_book_id(book_id)
    folder = Path(folder_name if folder_name else book_id.replace("/", "-"))
    folder.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(build_headers(book_id))
    pages = get_pages(session, book_id)

    if start < 1:
        raise ValueError("start harus >= 1")
    if end < start:
        raise ValueError("end harus >= start")

    q = Queue()
    print_lock = threading.Lock()

    def worker():
        while True:
            page_number = q.get()
            try:
                download_image(session, folder, pages, page_number, print_lock)
            finally:
                q.task_done()

    for _ in range(max(1, threads)):
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    for page_number in range(start, end + 1):
        q.put(page_number)

    q.join()
    print(f"[+] DONE download -> {folder}")
    return folder


def find_image_for_page(folder: Path, page_number: int) -> Path:
    for extension in IMAGE_EXTENSIONS:
        candidate = folder / f"{page_number}{extension}"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"File gambar untuk halaman {page_number} tidak ketemu.")


def image_to_pdf_page(image_path: Path) -> Image.Image:
    image = Image.open(image_path)
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, "WHITE")
        alpha = image.getchannel("A") if "A" in image.getbands() else None
        background.paste(image.convert("RGBA"), mask=alpha)
        image.close()
        return background
    converted = image.convert("RGB")
    image.close()
    return converted


def convert_to_pdf(folder_name: str, start: int, end: int, output: str | None = None):
    folder = Path(folder_name).resolve()
    if not folder.exists():
        raise FileNotFoundError(f"Folder tidak ketemu: {folder}")
    if end < start:
        raise ValueError("end harus >= start")

    image_paths = [find_image_for_page(folder, page_number) for page_number in range(start, end + 1)]
    pdf_path = Path(output).resolve() if output else folder.with_suffix(".pdf")

    print("[*] Converting images to PDF...")
    pdf_pages = [image_to_pdf_page(path) for path in image_paths]
    first_page, rest_pages = pdf_pages[0], pdf_pages[1:]
    first_page.save(pdf_path, save_all=True, append_images=rest_pages, format="PDF", resolution=100.0)

    for page in pdf_pages:
        page.close()

    print(f"[+] Finished PDF: {pdf_path}")
    return pdf_path


def download_and_convert(book_id: str, start: int, end: int, folder_name: str | None, threads: int, output: str | None):
    folder = download_book(book_id, start, end, folder_name, threads)
    return convert_to_pdf(str(folder), start, end, output)


def build_parser():
    parser = argparse.ArgumentParser(description="FlipHTML5 downloader + WEBP/JPG/PNG to PDF converter.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download gambar halaman")
    download_parser.add_argument("bookID", help="Contoh: zgfij/shiq")
    download_parser.add_argument("start", type=int, help="Halaman mulai")
    download_parser.add_argument("end", type=int, help="Halaman akhir")
    download_parser.add_argument("-n", "--folderName", help="Nama folder output")
    download_parser.add_argument("-t", "--threads", type=int, default=10, help="Jumlah thread")

    pdf_parser = subparsers.add_parser("pdf", help="Convert folder gambar ke PDF")
    pdf_parser.add_argument("folderName", help="Folder hasil download")
    pdf_parser.add_argument("start", type=int, help="Halaman awal")
    pdf_parser.add_argument("end", type=int, help="Halaman akhir")
    pdf_parser.add_argument("-o", "--output", help="Nama file PDF output")

    all_parser = subparsers.add_parser("all", help="Download lalu langsung convert ke PDF")
    all_parser.add_argument("bookID", help="Contoh: zgfij/shiq")
    all_parser.add_argument("start", type=int, help="Halaman mulai")
    all_parser.add_argument("end", type=int, help="Halaman akhir")
    all_parser.add_argument("-n", "--folderName", help="Nama folder output")
    all_parser.add_argument("-t", "--threads", type=int, default=10, help="Jumlah thread")
    all_parser.add_argument("-o", "--output", help="Nama file PDF output")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "download":
        download_book(args.bookID, args.start, args.end, args.folderName, args.threads)
    elif args.command == "pdf":
        convert_to_pdf(args.folderName, args.start, args.end, args.output)
    elif args.command == "all":
        download_and_convert(args.bookID, args.start, args.end, args.folderName, args.threads, args.output)


if __name__ == "__main__":
    main()
