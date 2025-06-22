import psutil
import platform
import socket
import win32com.client
import time
from database import db
import traceback
import mysql.connector
import uuid
from datetime import datetime
import logging
import os


log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"hardware_monitor_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_error(error):
    logging.error(f"Hata oluştu: {str(error)}")
    with open(os.path.join(log_dir, "error.txt"), "a") as f:
        f.write(f"{datetime.now()} - {str(error)}\n")

class HardwareMonitor:
    def __init__(self):
        self.interval = 60  
        self.system_id = None
        self.running = True
        
    def collect_system_info(self):
        """Sistem bilgilerini topla"""
        try:
            system_info = {}
            
            # Temel sistem bilgileri
            system_info["computer_name"] = socket.gethostname()
            system_info["operating_system"] = f"{platform.system()} {platform.release()}"
            system_info["processor"] = platform.processor()
            system_info["ram"] = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
            system_info["disk_space"] = f"{round(psutil.disk_usage('/').total / (1024**3), 2)} GB"
            
            
            wmi = win32com.client.GetObject('winmgmts:')
            for item in wmi.InstancesOf("Win32_ComputerSystem"):
                system_info["manufacturer"] = item.Manufacturer
                system_info["model"] = item.Model
            
            return system_info
        except Exception as e:
            print(f"Sistem bilgileri toplanırken hata: {str(e)}")
            return None

    def collect_network_info(self):
        """Ağ bilgilerini topla"""
        try:
            network_info = []
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        network_info.append({
                            "interface": interface,
                            "ip_address": addr.address,
                            "mac_address": next(
                                (a.address for a in addrs if a.family == psutil.AF_LINK), "N/A"
                            )
                        })
            return network_info
        except Exception as e:
            print(f"Ağ bilgileri toplanırken hata: {str(e)}")
            return None

    def collect_device_info(self):
        """Bağlı cihaz bilgilerini topla"""
        try:
            device_info = []
            wmi = win32com.client.GetObject("winmgmts:\\\\.\\root\\cimv2")
            devices = wmi.InstancesOf("Win32_PnPEntity")
            
            for device in devices:
                if device.Name:
                    device_name = device.Name.strip()
                    if device_name:
                        device_info.append({
                            "device_name": device_name
                        })
            
            return device_info
            
        except Exception as e:
            print(f"Cihaz bilgileri toplanırken hata: {str(e)}")
            print(traceback.format_exc())
            return None

    def save_to_database(self):
        try:
          
            connection = mysql.connector.connect(
                host='mysql-20847602-ktun-f5b8.h.aivencloud.com',
                user='avnadmin',
                password='AVNS_J3Mb3cvEjKmRdkQc1DN',
                database='defaultdb',
                port=13447,
                charset='utf8mb4'
            )
            
            cursor = connection.cursor(dictionary=True)
            
            
            cursor.execute("""
                SELECT system_id 
                FROM hwd_system_information 
                WHERE computer_name = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (self.system_info['computer_name'],))
            
            result = cursor.fetchone()
            if result:
                self.system_id = result['system_id']
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mevcut System ID kullanılıyor: {self.system_id}")
            else:
               
                timestamp = int(time.time()) % 1000000
                self.system_id = timestamp
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Yeni System ID oluşturuldu: {self.system_id}")

            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                UPDATE hwd_system_information 
                SET operating_system = %s,
                    processor = %s,
                    ram = %s,
                    disk_space = %s,
                    manufacturer = %s,
                    model = %s,
                    created_at = %s
                WHERE computer_name = %s
            """, (
                self.system_info['operating_system'],
                self.system_info['processor'],
                self.system_info['ram'],
                self.system_info['disk_space'],
                self.system_info['manufacturer'],
                self.system_info['model'],
                current_time,
                self.system_info['computer_name']
            ))

           
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO hwd_system_information 
                    (system_id, computer_name, operating_system, processor, ram, disk_space, manufacturer, model, created_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.system_id,
                    self.system_info['computer_name'],
                    self.system_info['operating_system'],
                    self.system_info['processor'],
                    self.system_info['ram'],
                    self.system_info['disk_space'],
                    self.system_info['manufacturer'],
                    self.system_info['model'],
                    current_time
                ))

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sistem bilgileri kaydedildi")

           
            cursor.execute("""
                DELETE FROM hwd_network_information 
                WHERE system_id = %s
            """, (self.system_id,))

            
            for network in self.network_info:
                cursor.execute("""
                    INSERT INTO hwd_network_information 
                    (system_id, Ag_karti, IP_adress, mac_address, created_at) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    self.system_id,
                    network['interface'],
                    network['ip_address'],
                    network['mac_address'],
                    current_time
                ))
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ağ bilgileri kaydedildi")

            cursor.execute("""
                DELETE FROM hwd_pnp_devices 
                WHERE system_id = %s
            """, (self.system_id,))

            # Yeni cihaz bilgilerini ekle
            for device in self.device_info:
                cursor.execute("""
                    INSERT INTO hwd_pnp_devices
                    (system_id, device_name, created_at)
                    VALUES (%s, %s, %s)
                """, (
                    self.system_id,
                    device['device_name'],
                    current_time
                ))

            connection.commit()
            connection.close()
            return self.system_id
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Veritabanı hatası: {str(e)}")
            print(traceback.format_exc())
            return None

    def run(self):
        """Sürekli çalışan ana döngü"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Hardware Monitor başlatıldı...")
        
        while self.running:
            try:
                # Sistem bilgilerini topla
                self.system_info = self.collect_system_info()
                if not self.system_info:
                    print("Sistem bilgileri toplanamadı!")
                    time.sleep(self.interval)
                    continue
                
                # Ağ bilgilerini topla
                self.network_info = self.collect_network_info()
                if not self.network_info:
                    print("Ağ bilgileri toplanamadı!")
                    time.sleep(self.interval)
                    continue
               
                self.device_info = self.collect_device_info()
                if not self.device_info:
                    print("Cihaz bilgileri toplanamadı!")
                    time.sleep(self.interval)
                    continue
                
                
                if self.save_to_database():
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Veriler başarıyla kaydedildi.")
                else:
                    print("Veriler kaydedilemedi!")
                
                time.sleep(self.interval)
                    
            except Exception as e:
                print(f"Hata oluştu: {str(e)}")
                print(traceback.format_exc())
                time.sleep(60)  

    def stop(self):
        """Monitörü durdur"""
        self.running = False

if __name__ == "__main__":
    monitor = HardwareMonitor()
    try:
        logging.info("Hardware monitor başlatılıyor...")
        monitor.run()
    except KeyboardInterrupt:
        print("\nMonitör durduruluyor...")
        monitor.stop()
    except Exception as e:
        log_error(e)
        logging.error(f"Kritik hata: {e}")
    finally:
        logging.info("Hardware monitor tamamlandı.") 