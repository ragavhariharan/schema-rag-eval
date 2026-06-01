import sqlite3

def setup_database():
    print("🛠️  Building local test database...")
    conn = sqlite3.connect('test_catalog.db')
    cursor = conn.cursor()

    # 1. Create the 12K 5u Table (For the Warping/Illuminance tests)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS line_scan_lens_12k5u (
        model_name TEXT,
        tv_distortion_percent REAL,
        relative_illuminance_percent REAL
    )''')
    cursor.executemany('''INSERT INTO line_scan_lens_12k5u VALUES (?, ?, ?)''', [
        ('Lens_12K_A', 0.1, 75.0),
        ('Lens_12K_B', -2.0, 60.0), # High warping (negative)
        ('Lens_12K_C', 0.05, 85.0)  # Least warping, best illuminance
    ])

    # 2. Create the 4K 7u Tables (For the Cross-Generation / UNION test)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS line_scan_lens_4k7u (
        model_name TEXT, f_no_min REAL, wd_mm REAL
    )''')
    cursor.executemany('''INSERT INTO line_scan_lens_4k7u VALUES (?, ?, ?)''', [
        ('Old_4K_1', 2.8, 100), ('Old_4K_2', 4.0, 350)
    ])

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS new_series_line_scan_lens_4k7u (
        model_name TEXT, f_no_min REAL, wd_mm REAL, size_diameter_mm REAL, filter_thread_raw TEXT
    )''')
    cursor.executemany('''INSERT INTO new_series_line_scan_lens_4k7u VALUES (?, ?, ?, ?, ?)''', [
        ('New_4K_1', 2.0, 90, 45, 'M46x0.75'), ('New_4K_2', 5.6, 150, 60, None)
    ])

    # 3. Create the Unified View (Fixes the "All Lenses" Missing Filter test)
    cursor.execute('''
    CREATE VIEW IF NOT EXISTS all_lenses AS 
    SELECT model_name, NULL AS size_diameter_mm, NULL AS size_length_min_mm, 150 AS weight_g FROM line_scan_lens_12k5u
    UNION ALL 
    SELECT model_name, size_diameter_mm, NULL AS size_length_min_mm, 180 AS weight_g FROM new_series_line_scan_lens_4k7u
    ''')

    conn.commit()
    conn.close()
    print("✅ test_catalog.db created and populated successfully.")

if __name__ == "__main__":
    setup_database()