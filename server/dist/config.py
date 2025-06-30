# Veritabanı ayarları
DB_CONFIG = {
    'host': 'host',
    'user': 'admin',
    'password': 'admin',
    'database': 'defaultdb',
    'port': 13345,
    'charset': 'utf8mb4',
    'ssl_verify_cert': False,  # Client PC'lerde sertifika doğrulamasını devre dışı bırakıyoruz
    'ssl_ca': None             # Client PC'lerde SSL sertifikası kullanmıyoruz
}

# Client/Server modu ayarı (Client PC'lerde True olmalı)
IS_CLIENT_MODE = True  # True: Sadece veri toplama, False: Tam işlev (veritabanı bağlantısı dahil)

# Client bilgisayar adı (otomatik algılanır)
import socket
CLIENT_NAME = socket.gethostname()
