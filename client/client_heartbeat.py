import socket
import time
import sys
import logging
import os
from datetime import datetime
import platform
import threading
import traceback
from win10toast import ToastNotifier  # Windows bildirimleri için

# Log klasörünü oluştur
os.makedirs('logs', exist_ok=True)

# Windows bildirimi için toaster oluştur
toaster = ToastNotifier()

# Log yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'heartbeat.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Sunucu bağlantı ayarları
SERVER_HOST = '192.168.1.33'  # Sunucunun IP adresi - buraya doğru IP girilmeli
SERVER_PORT = 5002            # Sunucu port numarası

# Heartbeat ayarları
HEARTBEAT_INTERVAL = 5     # Heartbeat gönderme aralığı (saniye)
RECONNECT_INTERVAL = 10    # Yeniden bağlanma aralığı (saniye)
MAX_RETRIES = 5            # Maksimum yeniden deneme sayısı

def get_computer_name():
    """Bilgisayar adını döndürür"""
    return platform.node()

class HeartbeatClient:
    """Heartbeat client sınıfı"""
    
    def __init__(self, server_host, server_port):
        """Client başlatma"""
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.computer_name = get_computer_name()
        self.stop_event = threading.Event()
        
        # İstatistik ekleyelim
        self.total_heartbeats = 0
        self.successful_heartbeats = 0
        self.last_successful_heartbeat = None
        
    def connect(self):
        """Sunucuya bağlan"""
        try:
            # Önceki soketi kapat
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
            
            # Yeni soket oluştur
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Bağlantı zaman aşımını ayarla (5 saniye)
            self.socket.settimeout(5)
            
            logger.info(f"Sunucuya bağlanılıyor: {self.server_host}:{self.server_port}")
            self.socket.connect((self.server_host, self.server_port))
            
            # Bilgisayar adını gönder
            self.socket.send(self.computer_name.encode())
            
            # Sunucudan yanıt bekle
            try:
                response = self.socket.recv(1024).decode()
                logger.info(f"Sunucudan yanıt alındı: {response}")
                
                # Eğer özel bir yanıt bekliyorsak (CONNECTED vb.), 
                # alternatif olarak herhangi bir yanıtı kabul edebiliriz
                if response:  # Herhangi bir yanıt geldiyse başarılı sayalım
                    logger.info(f"Sunucuya bağlandı: {self.server_host}:{self.server_port}")
                    self.connected = True
                    
                    # Zaman aşımını uzun bir süreye ayarla (normal çalışma için)
                    self.socket.settimeout(30)
                    return True
                else:
                    logger.error("Sunucudan boş yanıt alındı")
                    self.connected = False
                    return False
            except socket.timeout:
                logger.error("Sunucu yanıt zaman aşımı")
                self.connected = False
                return False
                
        except Exception as e:
            logger.error(f"Bağlantı hatası: {str(e)}")
            self.connected = False
            return False
    
    def send_heartbeat(self):
        """Heartbeat sinyali gönder"""
        if not self.connected:
            return False
            
        try:
            # Heartbeat mesajı gönder
            heartbeat_msg = "HEARTBEAT"
            logger.info(f"Heartbeat gönderiliyor: {heartbeat_msg}")
            self.socket.send(heartbeat_msg.encode())
            
            # İstatistik güncelle
            self.total_heartbeats += 1
            
            # Yanıt bekle
            response = self.socket.recv(1024).decode()
            logger.info(f"Heartbeat yanıtı alındı: {response}")
            if response == "ALIVE":
                logger.info(f"Heartbeat başarılı, bağlantı aktif: {self.server_host}:{self.server_port}")
                self.successful_heartbeats += 1
                self.last_successful_heartbeat = datetime.now()
                return True
            else:
                logger.warning(f"Heartbeat yanıtı beklenmeyen: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Heartbeat gönderme hatası: {str(e)}")
            self.connected = False
            return False
    
    def log_stats(self):
        """İstatistikleri logla"""
        success_rate = 0
        if self.total_heartbeats > 0:
            success_rate = (self.successful_heartbeats / self.total_heartbeats) * 100
            
        logger.info(f"İstatistikler: Toplam: {self.total_heartbeats}, Başarılı: {self.successful_heartbeats}, Başarı oranı: {success_rate:.1f}%")
        logger.info(f"Son başarılı heartbeat: {self.last_successful_heartbeat}")
    
    def run(self):
        """Ana döngü: Bağlantı kur ve heartbeat gönder"""
        logger.info(f"Heartbeat client başlatılıyor... (Bilgisayar adı: {self.computer_name})")
        
        connect_retries = 0
        stats_counter = 0
        
        while not self.stop_event.is_set():
            # Bağlı değilse bağlanmayı dene
            if not self.connected:
                if connect_retries >= MAX_RETRIES:
                    logger.warning(f"Maksimum yeniden bağlanma denemesi aşıldı ({MAX_RETRIES}). Daha uzun süre bekleniyor...")
                    time.sleep(RECONNECT_INTERVAL * 2)  # Daha uzun süre bekle
                    connect_retries = 0
                
                logger.info(f"Sunucuya bağlanmaya çalışılıyor... (Deneme: {connect_retries+1})")
                if self.connect():
                    connect_retries = 0
                else:
                    connect_retries += 1
                    time.sleep(RECONNECT_INTERVAL)
                    continue
            
            # Heartbeat gönder
            if not self.send_heartbeat():
                logger.warning("Heartbeat gönderilemedi, yeniden bağlanılacak...")
                self.connected = False
                continue
            
            # Her 10 heartbeat'te bir istatistik logla
            stats_counter += 1
            if stats_counter >= 10:
                self.log_stats()
                stats_counter = 0
            
            # Sonraki heartbeat'e kadar bekle
            time.sleep(HEARTBEAT_INTERVAL)
    
    def start(self):
        """Client'ı ayrı bir thread'de başlat"""
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()
        return thread
    
    def stop(self):
        """Client'ı durdur"""
        self.stop_event.set()
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        logger.info("Heartbeat client durduruldu")
        self.log_stats()  # Son istatistikleri göster

def main():
    """Ana metod"""
    try:
        # Komut satırı argümanlarını al (varsa)
        host = SERVER_HOST
        port = SERVER_PORT
        
        if len(sys.argv) > 1:
            host = sys.argv[1]
        if len(sys.argv) > 2:
            port = int(sys.argv[2])
        
        logger.info(f"Heartbeat client başlatılıyor - Sunucu: {host}:{port}")
        
        # Başlangıç bildirimi göster
        toaster.show_toast(
            "Heartbeat Client",
            "Program başlatıldı ve arkaplanda çalışıyor...",
            duration=5,
            threaded=True
        )
        
        # Client oluştur ve başlat
        client = HeartbeatClient(host, port)
        thread = client.start()
        
        # Ana thread kapatma sinyalini beklesin
        try:
            while thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Kullanıcı tarafından kapatılıyor...")
            client.stop()
            # Kapatma bildirimi göster
            toaster.show_toast(
                "Heartbeat Client",
                "Program kapatılıyor...",
                duration=3,
                threaded=True
            )
        
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)}")
        traceback.print_exc()
        # Hata bildirimi göster
        toaster.show_toast(
            "Heartbeat Client - Hata",
            f"Program hata ile karşılaştı: {str(e)}",
            duration=5,
            threaded=True
        )

if __name__ == "__main__":
    main() 