

import socket
import threading
import json
import time
from datetime import datetime
import os

# Bağlantı kaydı için dosya
CONNECTION_FILE = "active_connections.json"

# Global değişkenler
connected_clients = {}
client_lock = threading.Lock()
running = True

def save_connections():
    """Bağlantıları JSON olarak kaydet"""
    try:
        with client_lock:
            # Datetime'ları string'e çevir
            serializable_data = {}
            for name, data in connected_clients.items():
                serializable_data[name] = {
                    'last_seen': data['last_seen'].isoformat(),
                    'address': str(data['address'])
                }
            
            # JSON olarak kaydet
            with open(CONNECTION_FILE, 'w') as f:
                json.dump(serializable_data, f)
                
            print(f"Bağlantılar {CONNECTION_FILE} dosyasına kaydedildi: {len(connected_clients)} client")
    except Exception as e:
        print(f"Bağlantılar kaydedilirken hata: {e}")

def handle_client(client_socket, address):
    """İstemci bağlantısını yönet"""
    computer_name = None  # İsim değişkeni tanımla
    try:
        data = client_socket.recv(1024).decode()
        computer_name = data.strip()
        print(f"Yeni bağlantı: {computer_name} from {address}")
        
        # Bağlantı onayı gönder
        client_socket.send("CONNECTED".encode())
        
        # Global sözlüğü kilitle ve güncelle
        with client_lock:
            connected_clients[computer_name] = {
                'last_seen': datetime.now(),
                'address': address
            }
            # Bağlı client sayısını ve listesini logla
            print(f"Aktif bağlantılar ({len(connected_clients)}): {list(connected_clients.keys())}")
        
        # Bağlantıları kaydet
        save_connections()
        
        while running:
            try:
                data = client_socket.recv(1024)
                if not data:  # Bağlantı koptu
                    raise Exception("Bağlantı kapandı")
                
                # Heartbeat yanıtı
                message = data.decode().strip()
                print(f"Client mesajı alındı: {computer_name} -> {message}")
                if message == "HEARTBEAT":
                    client_socket.send("ALIVE".encode())
                    print(f"ALIVE yanıtı gönderildi: {computer_name}")
                
                with client_lock:
                    connected_clients[computer_name]['last_seen'] = datetime.now()
                    print(f"Son görülme zamanı güncellendi: {computer_name} -> {connected_clients[computer_name]['last_seen']}")
                
                # Her heartbeat güncellemesinde dosyayı güncelle
                save_connections()
                    
            except Exception as e:
                print(f"Client {computer_name} bağlantısı koptu: {e}")
                break
                
    except Exception as e:
        print(f"İstemci bağlantı hatası: {e}")
    finally:
        client_socket.close()
        if computer_name:  # Eğer bilgisayar adı tanımlanmışsa
            with client_lock:
                if computer_name in connected_clients:
                    del connected_clients[computer_name]
                    print(f"Client kaldırıldı: {computer_name}")
                    print(f"Aktif bağlantılar ({len(connected_clients)}): {list(connected_clients.keys())}")
            
            # Bağlantı değişikliklerini kaydet
            save_connections()
                    
        print(f"Bağlantı kapatıldı: {address}")

def start_socket_server():
    """Soket sunucusunu başlat"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Port yeniden kullanımına izin ver
    
    try:
        server.bind(('0.0.0.0', 5002))
        server.listen()
        print("Soket sunucusu başlatıldı, port: 5002")
        
        # Server'ı bloklama olmadan kapatabilmek için timeout
        server.settimeout(1)
        
        while running:
            try:
                client_socket, address = server.accept()
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                # Timeout - yeni kontrol döngüsü için devam et
                continue
            except Exception as e:
                print(f"Bağlantı kabul hatası: {e}")
                if not running:
                    break
                    
    except Exception as e:
        print(f"Soket sunucusu başlatılırken hata: {e}")
    finally:
        try:
            server.close()
            print("Soket sunucusu kapatıldı")
        except:
            pass

def stop_socket_server():
    """Soket sunucusunu durdur"""
    global running
    running = False
    print("Soket sunucusu kapatılıyor...")
    
    # Son bağlantı durumunu kaydet
    save_connections()
    
    print("Soket sunucusu durduruldu")

if __name__ == "__main__":
    try:
        # Soket sunucusunu başlat
        socket_thread = threading.Thread(target=start_socket_server)
        socket_thread.daemon = False  # Ana program kapanınca thread'in de kapanmasını istemiyoruz
        socket_thread.start()
        
        print("Soket sunucusu çalışıyor. Durdurmak için CTRL+C'ye basın.")
        
        # Ana program
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Klavye kesintisi algılandı. Kapatılıyor...")
        stop_socket_server()
        
        # Thread'in kapanmasını bekle
        if socket_thread.is_alive():
            socket_thread.join(timeout=5)
            
        print("Program sonlandırıldı.") 