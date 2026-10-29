import os
import sys
import shutil
import urllib.request
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal
from database.models import Movie

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
POSTERS_DIR = os.path.join(PROJECT_ROOT, "app", "static", "posters")

KINOPOISK_IDS = {
    "Начало": 447301,
    "Интерстеллар": 258687,
    "Матрица": 301,
    "Темный рыцарь": 111543,
    "Бегущий по лезвию 2049": 589290,
    "Аватар": 251733,
    "Мстители: Финал": 843650,
    "Крестный отец": 325,
    "Крестный отец 2": 327,
    "Криминальное чтиво": 342,
    "Славные парни": 350,
    "Побег из Шоушенка": 326,
    "Бойцовский клуб": 361,
    "Форрест Гамп": 448,
    "Унесённые призраками": 370,
    "Король Лев": 2360,
    "ВАЛЛ-И": 279102,
    "Тайна Коко": 679486,
    "История игрушек": 442,
    "Человек-паук: Через вселенные": 920265,
    "Ла-Ла Ленд": 841081,
    "Амели": 341,
    "Отель «Гранд Будапешт»": 683999,
    "Вечное сияние чистого разума": 5492,
    "Эта дурацкая любовь": 505898,
    "Сияние": 409,
    "Психо": 348,
    "Паразиты": 1043758,
    "Молчание ягнят": 345,
    "Прочь": 961715
}


def download_all():
    os.makedirs(POSTERS_DIR, exist_ok=True)
    db = SessionLocal()

    try:
        movies = db.query(Movie).all()
        success = 0

        for idx, m in enumerate(movies, start=1):
            kpid = KINOPOISK_IDS.get(m.title)
            if not kpid:
                # Try finding by substring or stripped quotes
                clean_m = m.title.replace("«", "").replace("»", "").replace(":", "").strip()
                for t, kid in KINOPOISK_IDS.items():
                    clean_t = t.replace("«", "").replace("»", "").replace(":", "").strip()
                    if clean_m == clean_t:
                        kpid = kid
                        break

            if not kpid:
                print(f"[SKIP] Unknown poster ID for: {m.title}")
                continue

            url = f"https://kinopoiskapiunofficial.tech/images/posters/kp/{kpid}.jpg"
            jpg_file = f"{m.id}.jpg"
            png_file = f"{m.id}.png"
            jpg_dest = os.path.join(POSTERS_DIR, jpg_file)
            png_dest = os.path.join(POSTERS_DIR, png_file)

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()

                if len(data) > 5000:
                    with open(jpg_dest, "wb") as f:
                        f.write(data)

                    # Save optimized PNG copy
                    with Image.open(jpg_dest) as im:
                        im.save(png_dest, "PNG")

                    # Copy by movie index (1.jpg, 2.jpg)
                    shutil.copyfile(jpg_dest, os.path.join(POSTERS_DIR, f"{idx}.jpg"))
                    shutil.copyfile(png_dest, os.path.join(POSTERS_DIR, f"{idx}.png"))

                    # Copy by clean title
                    safe_title = m.title.replace(":", "").replace("/", "_").replace("«", "").replace("»", "").strip()
                    shutil.copyfile(jpg_dest, os.path.join(POSTERS_DIR, f"{safe_title}.jpg"))
                    shutil.copyfile(png_dest, os.path.join(POSTERS_DIR, f"{safe_title}.png"))

                    m.poster_url = f"app/static/posters/{jpg_file}"
                    success += 1
                    print(f"Downloaded: {m.title} ({len(data)} bytes)")
                else:
                    print(f"Warning: {m.title} data too small: {len(data)}")
            except Exception as e:
                print(f"Failed to download {m.title}: {e}")

        db.commit()
        print(f"\nCOMPLETED: {success}/{len(movies)} original posters downloaded!")
    finally:
        db.close()


if __name__ == "__main__":
    download_all()
