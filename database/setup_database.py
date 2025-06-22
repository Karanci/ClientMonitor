from database.database import db

def setup_database():
    try:
        # Sistem metrikleri tablosu
        db.execute_update("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id SERIAL PRIMARY KEY,
            cpu_usage FLOAT,
            ram_usage FLOAT,
            disk_usage FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Ağ metrikleri tablosu
        db.execute_update("""
        CREATE TABLE IF NOT EXISTS network_metrics (
            id SERIAL PRIMARY KEY,
            download_speed FLOAT,
            upload_speed FLOAT,
            ping FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Donanım bilgileri tablosu (zaten mevcut olabilir)
        db.execute_update("""
        CREATE TABLE IF NOT EXISTS hwd_system_information (
            system_id SERIAL PRIMARY KEY,
            computer_name VARCHAR(255),
            operating_system VARCHAR(255),
            processor VARCHAR(255),
            ram VARCHAR(50),
            disk_space VARCHAR(50),
            manufacturer VARCHAR(255),
            model VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        print("Veritabanı tabloları başarıyla oluşturuldu!")

    except Exception as e:
        print(f"Veritabanı kurulum hatası: {str(e)}")

# Veritabanı kurulumunu başlat
setup_database() 