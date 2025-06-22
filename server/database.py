import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

class Database:
    _instance = None
    _connection = None
    _cursor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.connection = None
        self._cursor = None
        self.connect()

    def connect(self):
        """Veritabanına bağlantı oluşturur"""
        try:
            if self.connection is None:
                self.connection = mysql.connector.connect(**DB_CONFIG)
                self._cursor = self.connection.cursor(dictionary=True)
                print("Veritabanı bağlantısı başarılı!")
        except Error as e:
            print(f"Veritabanı bağlantı hatası: {e}")
            raise

    def get_connection(self):
        """Veritabanı bağlantısını döndürür"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection

    def get_cursor(self):
        """Veritabanı cursor'ını döndürür"""
        if not self._cursor or not self.connection.is_connected():
            self.connect()
        return self._cursor

    def close(self):
        """Veritabanı bağlantısını kapatır"""
        if self._cursor:
            self._cursor.close()
        if self.connection:
            self.connection.close()
            self.connection = None
            self._cursor = None

    def execute_query(self, query, params=None, max_retries=3):
        """Sorgu çalıştırır ve sonuçları döndürür"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                cursor = self.get_cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
            except Error as err:
                print(f"Sorgu çalıştırılırken hata oluştu (Deneme {retry_count + 1}/{max_retries}): {err}")
                if err.errno in (2006, 2013):  # Bağlantı kayboldu hataları
                    retry_count += 1
                    if retry_count < max_retries:
                        self.connect()  # Yeniden bağlan
                        continue
                raise
            finally:
                self.get_connection().commit()

    def execute_update(self, query, params=None, max_retries=3):
        """Update sorgusu çalıştırır"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                cursor = self.get_cursor()
                cursor.execute(query, params)
                self.get_connection().commit()
                return
            except Error as err:
                print(f"Güncelleme sorgusu çalıştırılırken hata oluştu (Deneme {retry_count + 1}/{max_retries}): {err}")
                if err.errno in (2006, 2013):  # Bağlantı kayboldu hataları
                    retry_count += 1
                    if retry_count < max_retries:
                        self.connect()  # Yeniden bağlan
                        continue
                raise

# Singleton instance'ı global olarak kullanılabilir
db = Database() 