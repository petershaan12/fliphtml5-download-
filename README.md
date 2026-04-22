# FLIPHTML5 Downloader

Tool sederhana buat:

1. download gambar halaman dari FlipHTML5
2. support format modern kayak `.webp`
3. convert hasilnya jadi PDF

Semua fungsi ada di `main.py`.

## Install

Disaranin pakai virtualenv:

```bash
pip install -r requirements.txt
```

## Fitur

- support FlipHTML5 versi lama dan baru
- gak cuma ngandelin `mobile/javascript/config.js`
- bisa parse URL model baru `files/large/*.webp?...`
- support output gambar `.webp`, `.jpg`, `.jpeg`, `.png`
- bisa convert gambar campuran jadi PDF
- ada mode:
  - download
  - pdf
  - all

## Cara pakai

### Download gambar

```bash
python main.py download zgfij/shiq 1 10
```

Opsi:

- `-n, --folderName` nama folder output
- `-t, --threads` jumlah thread download

Contoh:

```bash
python main.py download zgfij/shiq 1 20 -n buku-ku -t 12
```

### Convert gambar ke PDF

```bash
python main.py pdf zgfij-shiq 1 10
```

Opsi:

- `-o, --output` nama/path file PDF

Contoh:

```bash
python main.py pdf buku-ku 1 20 -o hasil.pdf
```

### Download lalu langsung convert ke PDF

```bash
python main.py all zgfij/shiq 1 10
```

Opsi:

- `-n, --folderName` nama folder output
- `-t, --threads` jumlah thread download
- `-o, --output` nama/path file PDF

Contoh:

```bash
python main.py all zgfij/shiq 1 20 -n buku-ku -o buku-ku.pdf
```

## Notes

- file hasil download disimpan pakai nomor halaman, misalnya `1.webp`, `2.webp`, dst
- kalau format halaman campur, converter tetap jalan
- hasil `.pdf` dan file gambar gak ikut ke-track karena udah di-ignore
