"""
ShopKart - Data Loader
Loads the Amazon Electronics dataset from CSV, or generates 10,000 realistic
sample products when the CSV file is not present.
"""
import os
import json
import random
import string

import pandas as pd


# ── Helper: clean price strings ────────────────────────────────────────────────
def _clean_price(val):
    """Convert '₹14,990' or '$199.99' to a float."""
    if pd.isna(val) or str(val).strip() in ('', 'nan'):
        return 0.0
    s = str(val).replace('₹', '').replace('$', '').replace(',', '').strip()
    try:
        return round(float(s), 2)
    except ValueError:
        return 0.0


def _clean_rating(val):
    """Convert '4.1' to float."""
    if pd.isna(val):
        return 0.0
    try:
        return round(float(str(val).strip()), 1)
    except ValueError:
        return 0.0


def _clean_count(val):
    """Convert '2,234' to int."""
    if pd.isna(val):
        return 0
    try:
        return int(str(val).replace(',', '').strip())
    except ValueError:
        return 0


# ── Public entry point ─────────────────────────────────────────────────────────
def load_data(app):
    """Detect data source and populate the products table."""
    data_file = app.config.get('DATA_FILE', 'data/amazon.csv')
    if os.path.exists(data_file):
        print(f'   Using CSV: {data_file}')
        _load_from_csv(data_file)
    else:
        print('   CSV not found – generating 10,000 sample products …')
        _generate_sample_data()


# ── Load from Kaggle CSV ───────────────────────────────────────────────────────
def _load_from_csv(filepath):
    """Parse the Amazon Electronics CSV and insert products."""
    from app import db
    from app.models import Product

    try:
        df = pd.read_csv(filepath, encoding='utf-8', on_bad_lines='skip')
        # Normalise column names
        df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df.rename(columns={
            'product_name':    'name',
            'discounted_price': 'price',
        }, inplace=True)

        KNOWN = {'product_id', 'name', 'category', 'price', 'actual_price',
                 'discount_percentage', 'rating', 'rating_count',
                 'about_product', 'img_link', 'product_link'}

        batch, i = [], 0
        for _, row in df.iterrows():
            raw_name = str(row.get('name', row.get('product_name', ''))).strip()
            if not raw_name or raw_name.lower() == 'nan':
                continue

            raw_cat = str(row.get('category', 'Electronics'))
            parts   = raw_cat.split('|')
            main_cat = parts[0].strip()
            sub_cat  = parts[1].strip() if len(parts) > 1 else ''

            price       = _clean_price(row.get('price', 0))
            actual      = _clean_price(row.get('actual_price', price))
            if price == 0.0 and actual > 0:
                price = actual

            rating      = _clean_rating(row.get('rating', 0))
            rating_cnt  = _clean_count(row.get('rating_count', 0))
            about       = str(row.get('about_product', ''))
            about       = '' if about == 'nan' else about[:2000]
            img         = str(row.get('img_link', ''))
            img         = '' if img == 'nan' else img[:1000]
            plink       = str(row.get('product_link', ''))
            plink       = '' if plink == 'nan' else plink[:1000]
            pid         = str(row.get('product_id', f'CSV{i}'))
            disc        = str(row.get('discount_percentage', ''))
            disc        = '' if disc == 'nan' else disc[:20]

            # Extra non-standard columns → JSON
            extra = {c: str(row[c])[:500]
                     for c in df.columns
                     if c not in KNOWN and not pd.isna(row.get(c, ''))}

            batch.append(Product(
                product_id=pid,
                name=raw_name[:500],
                category=main_cat[:200],
                sub_category=sub_cat[:200],
                price=price,
                actual_price=actual,
                discount_percentage=disc,
                rating=rating,
                rating_count=rating_cnt,
                about_product=about,
                img_link=img,
                product_link=plink,
                extra_data=json.dumps(extra) if extra else None,
            ))
            i += 1

            if len(batch) >= 500:
                db.session.bulk_save_objects(batch)
                db.session.commit()
                batch = []
                print(f'   … inserted {i} rows')

        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()

    except Exception as exc:
        print(f'   ⚠  CSV load error: {exc}')
        print('   Falling back to sample data …')
        _generate_sample_data()


# ── Sample data generator ──────────────────────────────────────────────────────
def _generate_sample_data():
    """Insert 10,000 realistic Amazon-style electronics products."""
    from app import db
    from app.models import Product

    CATEGORIES = [
        ('Computers&Accessories', 'Laptops'),
        ('Computers&Accessories', 'Keyboards'),
        ('Computers&Accessories', 'Mice'),
        ('Computers&Accessories', 'Monitors'),
        ('Computers&Accessories', 'USB Hubs'),
        ('Computers&Accessories', 'Webcams'),
        ('Electronics',           'Smartphones'),
        ('Electronics',           'Tablets'),
        ('Electronics',           'Headphones'),
        ('Electronics',           'Bluetooth Speakers'),
        ('Electronics',           'Cameras'),
        ('Electronics',           'Smartwatches'),
        ('Electronics',           'Power Banks'),
        ('HomeTheater',           'Televisions'),
        ('HomeTheater',           'Projectors'),
        ('HomeTheater',           'Soundbars'),
        ('OfficeProducts',        'Printers'),
        ('OfficeProducts',        'Scanners'),
        ('MusicalInstruments',    'Guitar Accessories'),
    ]

    BRANDS = [
        'Sony', 'Samsung', 'Apple', 'LG', 'Bose', 'JBL', 'Lenovo', 'Dell',
        'HP', 'Asus', 'Acer', 'Logitech', 'Corsair', 'Razer', 'Anker',
        'Xiaomi', 'OnePlus', 'Realme', 'boAt', 'Jabra', 'Plantronics',
        'SteelSeries', 'HyperX', 'Sennheiser', 'Audio-Technica',
    ]

    TEMPLATES = {
        'Laptops':           ['{b} IdeaPad {m} 15.6" FHD, Core i5 12th Gen, 16GB RAM, 512GB SSD',
                              '{b} Gaming Laptop {m} RTX 4060, 144Hz Display, 32GB DDR5',
                              '{b} Thin & Light {m} AMD Ryzen 7, 1TB NVMe, Backlit KB'],
        'Keyboards':         ['{b} Mechanical Keyboard {m} RGB, TKL, Cherry MX Switches',
                              '{b} Wireless Keyboard {m} Ergonomic, Multi-device Pairing',
                              '{b} Gaming Keyboard {m} Optical Switches, Anti-Ghosting'],
        'Mice':              ['{b} Wireless Mouse {m} 4000 DPI, Ergonomic, Silent Click',
                              '{b} Gaming Mouse {m} 16000 DPI, RGB, 7 Programmable Buttons'],
        'Monitors':          ['{b} {sz}" IPS Monitor {m} 2K QHD 165Hz 1ms, FreeSync',
                              '{b} {sz}" 4K UHD Monitor {m} USB-C 65W, HDR 600'],
        'USB Hubs':          ['{b} 7-Port USB 3.0 Hub {m} with Power Adapter',
                              '{b} USB-C Hub {m} 10-in-1 HDMI 4K, SD Card Reader'],
        'Webcams':           ['{b} Webcam {m} 1080p 60fps, Auto Light Correction, Ring Light'],
        'Smartphones':       ['{b} {m} Pro 5G 6.7" AMOLED 108MP 5000mAh Battery',
                              '{b} {m} 5G 8GB 256GB 120Hz Super AMOLED'],
        'Tablets':           ['{b} Tab {m} 10.4" FHD 6GB RAM 128GB WiFi',
                              '{b} Pad {m} Pro 11" OLED 120Hz S-Pen Included'],
        'Headphones':        ['{b} WH-{m} Wireless ANC 30hr Battery Hi-Res Audio',
                              '{b} True Wireless Earbuds {m} IPX5 ANC 28hr Total',
                              '{b} Over-Ear {m} Foldable Wired Hi-Fi 40mm Drivers'],
        'Bluetooth Speakers': ['{b} Portable Speaker {m} 360° Sound IPX7 12hr Battery',
                               '{b} Party Speaker {m} 100W LED Lights Bass Boost'],
        'Cameras':           ['{b} Mirrorless Camera {m} 24MP 4K Video 5-Axis IBIS',
                              '{b} DSLR {m} 30.4MP Dual Pixel AF 4K 60fps'],
        'Smartwatches':      ['{b} Smartwatch {m} 1.4" AMOLED SpO2 GPS 7-Day Battery',
                              '{b} Smart Band {m} Heart Rate Sleep Tracking 14-Day'],
        'Power Banks':       ['{b} Power Bank {m} 20000mAh 65W PD Fast Charge 3 Ports'],
        'Televisions':       ['{b} {sz}" 4K UHD Smart TV {m} HDR10+ Dolby Vision',
                              '{b} {sz}" QLED TV {m} 120Hz HDMI 2.1 Google TV'],
        'Projectors':        ['{b} Projector {m} 4K 3000 Lumens Auto Keystone'],
        'Soundbars':         ['{b} Soundbar {m} 400W Dolby Atmos 3.1.2 HDMI ARC'],
        'Printers':          ['{b} Laser Printer {m} Wireless Duplex 34ppm'],
        'Scanners':          ['{b} Document Scanner {m} ADF Duplex 600dpi'],
        'Guitar Accessories': ['{b} Guitar Tuner {m} Clip-on Chromatic All Instruments'],
    }

    PRICE_RANGES = {
        'Laptops':           (28000, 180000),
        'Smartphones':       (8000,  130000),
        'Tablets':           (10000,  85000),
        'Televisions':       (14000, 220000),
        'Cameras':           (22000, 210000),
        'Headphones':        (499,    35000),
        'Bluetooth Speakers': (999,   55000),
        'Keyboards':         (499,    18000),
        'Mice':              (299,    10000),
        'Monitors':          (8000,   65000),
        'Smartwatches':      (999,    45000),
        'Power Banks':       (599,    10000),
        'USB Hubs':          (299,     4000),
        'Webcams':           (999,    15000),
        'Projectors':        (15000, 150000),
        'Soundbars':         (3000,   60000),
        'Printers':          (5000,   50000),
        'Scanners':          (4000,   30000),
        'Guitar Accessories': (199,    3000),
    }

    ABOUTS = [
        'High-performance {sub} designed for professionals and enthusiasts alike. '
        'Built with premium materials and backed by a 1-year manufacturer warranty.',
        'The latest {sub} with cutting-edge technology, intuitive controls, and '
        'exceptional build quality. Perfect for everyday use and creative workflows.',
        'Experience superior performance with the {sub}. Engineered for reliability, '
        'featuring fast connectivity and a sleek, portable form factor.',
        'Compact yet powerful {sub} that delivers outstanding results. '
        'Easy to set up, compatible with all major platforms.',
        'Premium {sub} offering an unmatched combination of features and value. '
        'Ideal for both beginners and experienced users.',
    ]

    batch, count = [], 0
    from app import db
    from app.models import Product

    for i in range(1, 10001):
        cat, sub = random.choice(CATEGORIES)
        brand    = random.choice(BRANDS)
        model    = ''.join(random.choices(string.ascii_uppercase, k=2)) + str(random.randint(100, 9999))
        sz       = random.choice(['32', '43', '50', '55', '65', '75'])

        tpl_list = TEMPLATES.get(sub, ['{b} {sub} {m} – Premium Edition'])
        tpl      = random.choice(tpl_list)
        name     = tpl.format(b=brand, m=model, sz=sz, sub=sub)

        lo, hi      = PRICE_RANGES.get(sub, (499, 50000))
        actual      = round(random.uniform(lo, hi), 2)
        disc_pct    = random.randint(5, 55)
        price       = round(actual * (1 - disc_pct / 100), 2)
        rating      = round(random.uniform(3.2, 5.0), 1)
        rating_cnt  = random.randint(12, 60000)
        about       = random.choice(ABOUTS).format(sub=sub)

        batch.append(Product(
            product_id=f'B{i:010d}',
            name=name[:500],
            category=cat,
            sub_category=sub,
            price=price,
            actual_price=actual,
            discount_percentage=f'{disc_pct}%',
            rating=rating,
            rating_count=rating_cnt,
            about_product=about,
            img_link=f'https://picsum.photos/seed/prod{i}/400/400',
            product_link=f'https://amazon.in/dp/B{i:010d}',
            extra_data=json.dumps({'brand': brand, 'model': model,
                                   'in_stock': random.choice([True, True, True, False]),
                                   'seller': f'{brand} Official Store'}),
        ))
        count += 1

        if len(batch) == 500:
            db.session.bulk_save_objects(batch)
            db.session.commit()
            batch = []
            print(f'   … {count} / 10 000 products inserted')

    if batch:
        db.session.bulk_save_objects(batch)
        db.session.commit()
