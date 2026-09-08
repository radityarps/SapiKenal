#!/usr/bin/env python3
"""
collect_local_cattle_dataset.py

Skrip pengumpul dataset citra jenis sapi lokal Indonesia dan sapi target SapiKenal.
Dirancang untuk mengumpulkan citra BERSIH dan BEBAS NOISE untuk pelatihan model computer vision.

Peningkatan Filter & Kebersihan:
1. Query Spesifik Peternakan (Jantan, Betina, Kandang, Padang Rumput, Bibit).
2. Negative Keywords Kuat: Memblokir kata kunci makanan (soto, sate, daging, resep),
   kegiatan budaya non-peternakan (karapan, joki, pacu jawi), dan grafis (kartun, logo, infografis).
3. Domain Blacklist: Memblokir situs stock photo ber-watermark (AntaraFoto, Dreamstime, Shutterstock, Alamy)
   dan thumbnail video (ytimg).
4. Heuristik Citra Otomatis:
   - Memfilter aspek rasio ekstrem (banner horizontal atau infografis vertikal).
   - Memfilter banner/bar solid pada bagian atas/bawah (thumbnail YouTube / watermark bar).
   - Resolusi minimum >= 250x250 px.
   - Konversi bersih ke RGB JPEG dengan optimasi ukuran.
"""

import argparse
import hashlib
import html
import os
import re
import sys
import time
import urllib.parse
from io import BytesIO
from typing import Dict, List, Set, Tuple

try:
    import requests
    from PIL import Image, ImageStat
except ImportError:
    print("[ERROR] Pustaka yang dibutuhkan belum terpasang.")
    print("Silakan jalankan: pip install pillow requests")
    sys.exit(1)

# Kata kunci negatif umum untuk membuang makanan, lomba/joki, teks, dan grafis
GLOBAL_NEGATIVES = (
    "-sate -soto -resep -kuliner -daging -masakan -rawon -gulai -rendang "
    "-karapan -pacu -joki -lomba -juara "
    "-kartun -vektor -logo -banner -thumbnail -infografis -drawing -clipart -illustration "
    "-truk -pasar"
)

# Daftar kata kunci pencarian yang difokuskan pada morfologi tubuh sapi nyata
DEFAULT_BREED_QUERIES: Dict[str, List[str]] = {
    # 1. Sapi Bali (Target SapiKenal)
    "bali": [
        f"sapi bali jantan {GLOBAL_NEGATIVES}",
        f"sapi bali betina {GLOBAL_NEGATIVES}",
        f"bibit sapi bali {GLOBAL_NEGATIVES}",
        f"sapi bali di kandang {GLOBAL_NEGATIVES}",
        f"sapi bali padang rumput {GLOBAL_NEGATIVES}",
        f"bali cattle bull farm -meat -recipe -cartoon",
        f"bali cattle cow pasture -meat -recipe -cartoon",
        f"bos javanicus domesticus pasture -skull -fossil",
    ],
    # 2. Sapi Madura
    "madura": [
        f"sapi madura jantan {GLOBAL_NEGATIVES}",
        f"sapi madura betina {GLOBAL_NEGATIVES}",
        f"bibit sapi madura {GLOBAL_NEGATIVES}",
        f"sapi madura di kandang {GLOBAL_NEGATIVES}",
        f"sapi madura padang rumput {GLOBAL_NEGATIVES}",
        f"pedet sapi madura {GLOBAL_NEGATIVES}",
        f"madura cattle breed farm -racing -jockey -meat -recipe",
        f"madura bull pasture -racing -jockey -meat",
    ],
    # 3. Sapi Peranakan Ongole (PO)
    "po": [
        f"sapi peranakan ongole jantan {GLOBAL_NEGATIVES}",
        f"sapi peranakan ongole betina {GLOBAL_NEGATIVES}",
        f"sapi po kebumen jantan {GLOBAL_NEGATIVES}",
        f"sapi ongole putih kandang {GLOBAL_NEGATIVES}",
        f"bibit sapi peranakan ongole {GLOBAL_NEGATIVES}",
        f"ongole cattle bull farm -meat -recipe -beef",
        f"ongole cow pasture -meat -recipe -beef",
    ],
    # 4. Sapi Pasundan (Jawa Barat)
    "pasundan": [
        f"sapi pasundan jantan {GLOBAL_NEGATIVES}",
        f"sapi pasundan betina {GLOBAL_NEGATIVES}",
        f"bibit sapi pasundan {GLOBAL_NEGATIVES}",
        f"ternak sapi pasundan di kandang {GLOBAL_NEGATIVES}",
        f"sapi pasundan ciamis pasture {GLOBAL_NEGATIVES}",
    ],
    # 5. Sapi Aceh
    "aceh": [
        f"sapi aceh jantan {GLOBAL_NEGATIVES}",
        f"sapi aceh betina {GLOBAL_NEGATIVES}",
        f"bibit sapi aceh {GLOBAL_NEGATIVES}",
        f"ternak sapi aceh di kandang {GLOBAL_NEGATIVES}",
        f"aceh cattle bull farm -meat -recipe",
    ],
    # 6. Sapi Pesisir (Sumatera Barat)
    "pesisir": [
        f"sapi pesisir sumatera barat kandang {GLOBAL_NEGATIVES}",
        f"sapi pesisir jantan {GLOBAL_NEGATIVES}",
        f"sapi pesisir betina {GLOBAL_NEGATIVES}",
        f"bibit sapi pesisir {GLOBAL_NEGATIVES}",
        f"ternak sapi pesisir padang {GLOBAL_NEGATIVES}",
    ],
    # 7. Sapi Jabres (Jawa Brebes)
    "jabres": [
        f"sapi jabres brebes {GLOBAL_NEGATIVES}",
        f"sapi jawa brebes kandang {GLOBAL_NEGATIVES}",
        f"bibit sapi jabres {GLOBAL_NEGATIVES}",
        f"ternak sapi jabres jantan {GLOBAL_NEGATIVES}",
    ],
    # 8. Sapi Brahman (Target SapiKenal)
    "brahman": [
        f"brahman cattle bull pasture -meat -recipe -beef -cartoon",
        f"brahman cattle cow farm -meat -recipe -beef -cartoon",
        f"sapi brahman jantan {GLOBAL_NEGATIVES}",
        f"sapi brahman betina {GLOBAL_NEGATIVES}",
        f"bibit sapi brahman kandang {GLOBAL_NEGATIVES}",
    ],
    # 9. Sapi Brangus (Target SapiKenal)
    "brangus": [
        f"black brangus cattle bull pasture -meat -recipe -beef -cartoon",
        f"brangus cattle cow farm -meat -recipe -beef -cartoon",
        f"sapi brangus jantan {GLOBAL_NEGATIVES}",
        f"sapi brangus betina {GLOBAL_NEGATIVES}",
    ],
    # 10. Sapi Limusin (Target SapiKenal)
    "limusin": [
        f"limousin cattle bull pasture -meat -recipe -beef -cartoon",
        f"limousin cattle cow farm -meat -recipe -beef -cartoon",
        f"sapi limusin jantan {GLOBAL_NEGATIVES}",
        f"sapi limusin betina {GLOBAL_NEGATIVES}",
        f"bibit sapi limusin kandang {GLOBAL_NEGATIVES}",
    ],
}

# Domain & URL yang diblokir karena watermark pekat, thumbnail teks, atau resep makanan
BLOCKED_URL_PATTERNS = [
    # Situs stock photo ber-watermark
    "antarafoto.com",
    "dreamstime.com",
    "shutterstock.com",
    "alamy.com",
    "gettyimages.com",
    "istockphoto.com",
    "123rf.com",
    "depositphotos.com",
    "freepik.com",
    "vectorstock.com",
    "stock.adobe.com",
    "canva.com",
    # Thumbnail YouTube dengan teks besar
    "ytimg.com",
    "youtube.com",
    # Resep masakan / kuliner
    "cookpad.com",
    "resepkoki",
    "endeus.tv",
    "briliofood",
    "idntimes.com/food",
    "kompas.com/food",
    "detik.com/food",
    "kuliner",
    "makanan",
]

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


def is_url_clean(url: str) -> bool:
    """Memeriksa apakah URL tidak berasal dari domain blacklist."""
    url_lower = url.lower()
    for pattern in BLOCKED_URL_PATTERNS:
        if pattern in url_lower:
            return False
    return True


def compute_image_hash(content: bytes) -> str:
    """Menghitung hash MD5 konten citra untuk mencegah gambar kembar."""
    return hashlib.md5(content).hexdigest()


def check_and_clean_image(content: bytes) -> Tuple[bool, Image.Image, str]:
    """
    Memvalidasi kualitas citra dengan kriteria ketat dataset CV:
    1. Integritas file (Pillow verify).
    2. Dimensi minimum >= 250x250 px.
    3. Aspek rasio normal hewan (0.65 <= w/h <= 1.85) untuk membuang infografis dan banner ultra-lebar.
    4. Banner/Border check: mendeteksi pita solid warna di atas/bawah (thumbnail YouTube / watermark bar).
    """
    try:
        with Image.open(BytesIO(content)) as img:
            img.verify()
    except Exception:
        return False, None, "File korup / format tidak didukung"

    try:
        img_rgb = Image.open(BytesIO(content)).convert("RGB")
    except Exception:
        return False, None, "Gagal konversi ke RGB"

    w, h = img_rgb.size

    # Filter ukuran minimum
    if w < 250 or h < 250:
        return False, None, f"Ukuran terlalu kecil ({w}x{h})"

    # Filter aspek rasio
    aspect_ratio = w / h
    if aspect_ratio < 0.65 or aspect_ratio > 1.85:
        return False, None, f"Aspek rasio tidak proporsional ({aspect_ratio:.2f})"

    # Filter pita solid bawah (banner teks thumbnail YouTube / watermark bar)
    bot_strip = img_rgb.crop((0, int(h * 0.94), w, h)).convert("L")
    stat_bot = ImageStat.Stat(bot_strip)
    if stat_bot.stddev[0] < 8.0:
        return False, None, f"Terdeteksi pita banner bawah solid (stddev={stat_bot.stddev[0]:.2f})"

    # Filter pita solid atas (bingkai poster / banner atas)
    top_strip = img_rgb.crop((0, 0, w, int(h * 0.06))).convert("L")
    stat_top = ImageStat.Stat(top_strip)
    if stat_top.stddev[0] < 8.0:
        return False, None, f"Terdeteksi pita banner atas solid (stddev={stat_top.stddev[0]:.2f})"

    # Resize cerdas jika gambar terlalu raksasa (> 2000px) agar hemat disk tanpa mengurangi detail 224x224
    if max(w, h) > 1920:
        img_rgb.thumbnail((1920, 1920), Image.Resampling.LANCZOS)

    return True, img_rgb, "Valid"


def get_existing_hashes(target_dir: str) -> Set[str]:
    """Membaca hash dari citra yang sudah ada di folder."""
    hashes: Set[str] = set()
    if not os.path.exists(target_dir):
        return hashes

    for filename in os.listdir(target_dir):
        file_path = os.path.join(target_dir, filename)
        if os.path.isfile(file_path) and filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            try:
                with open(file_path, "rb") as f:
                    hashes.add(compute_image_hash(f.read()))
            except Exception:
                continue
    return hashes


def fetch_bing_image_urls(query: str, max_results: int = 150) -> List[str]:
    """
    Mengambil URL citra langsung dari Bing dengan filter khusus foto asli (+filterui:photo-photo).
    """
    urls: List[str] = []
    seen: Set[str] = set()
    page = 0

    while len(urls) < max_results and page < 8:
        offset = page * 35
        params = {
            "q": query,
            "first": offset,
            "count": 35,
            "adlt": "off",
            "qft": "+filterui:photo-photo",
        }
        url = "https://www.bing.com/images/async?" + urllib.parse.urlencode(params)

        try:
            resp = requests.get(url, headers=HTTP_HEADERS, timeout=10)
            if resp.status_code != 200 or not resp.text:
                break

            found = re.findall(r'murl&quot;:&quot;(.*?)&quot;', resp.text)
            if not found:
                break

            added = 0
            for raw_url in found:
                clean_url = html.unescape(raw_url).replace(" ", "%20")
                if (
                    clean_url not in seen
                    and clean_url.startswith("http")
                    and is_url_clean(clean_url)
                ):
                    seen.add(clean_url)
                    urls.append(clean_url)
                    added += 1
                    if len(urls) >= max_results:
                        break

            if added == 0:
                break

            page += 1
            time.sleep(0.3)
        except Exception:
            break

    return urls


def fetch_wikimedia_image_urls(query: str, max_results: int = 50) -> List[str]:
    """Mengambil URL foto berlisensi terbuka dari Wikimedia Commons."""
    urls: List[str] = []
    endpoint = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": min(max_results, 50),
        "prop": "imageinfo",
        "iiprop": "url|mime",
    }
    headers = {
        "User-Agent": "SapiKenalDatasetCollector/2.0 (academic-cv-dataset)"
    }
    try:
        resp = requests.get(endpoint, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for _, page_info in pages.items():
                imageinfo = page_info.get("imageinfo", [])
                if imageinfo:
                    mime = imageinfo[0].get("mime", "")
                    if mime.startswith("image/"):
                        img_url = imageinfo[0].get("url")
                        if img_url and is_url_clean(img_url):
                            urls.append(img_url)
    except Exception:
        pass
    return urls


def download_breed_images(
    breed: str,
    queries: List[str],
    output_dir: str,
    target_count: int,
    request_timeout: int = 8,
    delay: float = 0.25,
) -> int:
    """Mengunduh dan memfilter citra untuk satu jenis sapi hingga target terpenuhi."""
    breed_dir = os.path.join(output_dir, breed)
    os.makedirs(breed_dir, exist_ok=True)

    seen_hashes = get_existing_hashes(breed_dir)
    existing_count = len([f for f in os.listdir(breed_dir) if f.lower().endswith(".jpg")])
    downloaded = existing_count

    print(f"\n=======================================================")
    print(f"[JENIS SAPI] {breed.upper()}")
    print(f"Direktori : {breed_dir}")
    print(f"Kondisi   : {downloaded}/{target_count} citra sudah ada")
    print(f"=======================================================")

    if downloaded >= target_count:
        print(f"Target {target_count} citra untuk jenis '{breed}' sudah terpenuhi.")
        return downloaded

    # 1. Sumber Wikimedia Commons
    for query in queries[:2]:
        if downloaded >= target_count:
            break
        # Bersihkan query dari minus-negative untuk Wikimedia API
        clean_wiki_query = re.sub(r'-\S+', '', query).strip()
        wiki_urls = fetch_wikimedia_image_urls(clean_wiki_query, max_results=30)
        if wiki_urls:
            print(f"-> Wikimedia: Menemukan {len(wiki_urls)} foto untuk '{clean_wiki_query}'...")
            for img_url in wiki_urls:
                if downloaded >= target_count:
                    break
                if _try_process_and_save(img_url, breed, breed_dir, seen_hashes, downloaded, request_timeout):
                    downloaded += 1
                    if downloaded % 10 == 0 or downloaded == target_count:
                        print(f"   [Progress] {downloaded}/{target_count} citra bersih tersimpan.")
                    time.sleep(delay)

    # 2. Sumber Bing Image Search (Photo Filter + Negatives)
    for query in queries:
        if downloaded >= target_count:
            break

        query_preview = query[:50] + "..." if len(query) > 50 else query
        print(f"-> Bing: Mencari '{query_preview}'...")
        bing_urls = fetch_bing_image_urls(query, max_results=80)
        print(f"   Ditemukan {len(bing_urls)} kandidat URL lolos blacklist domain.")

        for img_url in bing_urls:
            if downloaded >= target_count:
                break
            if _try_process_and_save(img_url, breed, breed_dir, seen_hashes, downloaded, request_timeout):
                downloaded += 1
                if downloaded % 10 == 0 or downloaded == target_count:
                    print(f"   [Progress] {downloaded}/{target_count} citra bersih tersimpan.")
                time.sleep(delay)

    print(f"[SELESAI] Jenis sapi '{breed}': {downloaded}/{target_count} citra bersih.")
    return downloaded


def _try_process_and_save(
    img_url: str,
    breed: str,
    breed_dir: str,
    seen_hashes: Set[str],
    current_index: int,
    timeout: int,
) -> bool:
    """Mengunduh, memvalidasi kualitas citra, dan menyimpannya jika lolos semua kriteria."""
    if not is_url_clean(img_url):
        return False

    try:
        resp = requests.get(img_url, headers=HTTP_HEADERS, timeout=timeout)
        if resp.status_code != 200:
            return False

        content = resp.content
        if len(content) < 8192:  # Abaikan file sangat kecil (< 8 KB)
            return False

        content_hash = compute_image_hash(content)
        if content_hash in seen_hashes:
            return False

        is_valid, img_rgb, reason = check_and_clean_image(content)
        if not is_valid:
            # File tidak memenuhi standar kebersihan dataset
            return False

        filename = f"{breed}_{current_index + 1:04d}.jpg"
        save_path = os.path.join(breed_dir, filename)
        img_rgb.save(save_path, "JPEG", quality=92)

        seen_hashes.add(content_hash)
        return True
    except Exception:
        return False


def curate_existing_folder(target_dir: str):
    """
    Fungsi utilitas untuk memindai dan memindahkan citra yang tidak layak dari folder yang sudah ada.
    """
    if not os.path.exists(target_dir):
        print(f"Direktori {target_dir} tidak ditemukan.")
        return

    rejected_dir = os.path.join(target_dir, "rejected")
    os.makedirs(rejected_dir, exist_ok=True)

    files = [f for f in os.listdir(target_dir) if f.lower().endswith(".jpg")]
    print(f"\n[KURASI] Memeriksa {len(files)} file di {target_dir}...")

    rejected_count = 0
    accepted_count = 0

    for filename in sorted(files):
        file_path = os.path.join(target_dir, filename)
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            is_valid, _, reason = check_and_clean_image(content)
            if not is_valid:
                print(f"  [REJECT] {filename} -> {reason}")
                os.rename(file_path, os.path.join(rejected_dir, filename))
                rejected_count += 1
            else:
                accepted_count += 1
        except Exception as e:
            print(f"  [REJECT] {filename} -> Gagal membaca ({e})")
            os.rename(file_path, os.path.join(rejected_dir, filename))
            rejected_count += 1

    print(f"\nHasil Kurasi:")
    print(f" - Lolos (Bersih)   : {accepted_count} citra")
    print(f" - Ditolak (Dipindah ke {rejected_dir}) : {rejected_count} citra")


def main():
    parser = argparse.ArgumentParser(
        description="Pengumpul Dataset Citra Sapi Lokal Bersih untuk Model SapiKenal."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw_cattle_dataset",
        help="Direktori target penyimpanan citra (default: data/raw_cattle_dataset).",
    )
    parser.add_argument(
        "--target-per-breed",
        type=int,
        default=200,
        help="Target jumlah citra per jenis sapi (default: 200).",
    )
    parser.add_argument(
        "--breeds",
        type=str,
        nargs="+",
        default=["bali", "madura", "po", "pasundan", "aceh", "pesisir", "jabres"],
        help="Daftar jenis sapi yang ingin diunduh.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.25,
        help="Jeda waktu (detik) antar unduhan (default: 0.25).",
    )
    parser.add_argument(
        "--clean-only",
        type=str,
        default="",
        help="Jalankan kurasi/pembersihan saja pada folder jenis sapi tertentu (misal: --clean-only data/raw_cattle_dataset/madura).",
    )

    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if args.clean_only:
        target_path = os.path.abspath(args.clean_only)
        curate_existing_folder(target_path)
        return

    output_abs_path = os.path.abspath(os.path.join(project_root, args.output_dir))

    print("================================================================")
    print(" SapiKenal — Pengumpul Dataset Citra Sapi Bersih (Clean Dataset)")
    print("================================================================")
    print(f"Target per jenis : {args.target_per_breed} citra bersih")
    print(f"Jenis sapi       : {', '.join(args.breeds)}")
    print(f"Direktori output : {output_abs_path}")
    print("Filter Aktif     : Domain Blacklist, Aspect Ratio, Banner Detection")
    print("================================================================")

    summary: Dict[str, int] = {}
    for breed in args.breeds:
        breed_key = breed.lower()
        queries = DEFAULT_BREED_QUERIES.get(
            breed_key,
            [f"sapi {breed_key} jantan {GLOBAL_NEGATIVES}", f"sapi {breed_key} betina {GLOBAL_NEGATIVES}"]
        )
        count = download_breed_images(
            breed=breed_key,
            queries=queries,
            output_dir=output_abs_path,
            target_count=args.target_per_breed,
            delay=args.delay,
        )
        summary[breed_key] = count

    print("\n================================================================")
    print(" RINGKASAN KOLEKSI DATASET BERSIH")
    print("================================================================")
    for b, c in summary.items():
        print(f" - {b:<12}: {c}/{args.target_per_breed} citra bersih")
    print(f"\nLokasi dataset: {output_abs_path}")
    print("================================================================")


if __name__ == "__main__":
    main()
