import winreg
import time
from datetime import datetime
import traceback
import mysql.connector
from config import DB_CONFIG

class SoftwareMonitor:
    def __init__(self):
        self.running = True
        self.interval = 3600  

    def get_installed_software(self):
        """Yüklü yazılımları tespit et"""
        try:
            software_list = []
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_64KEY),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_32KEY),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0)
            ]
            
            for root, path, flags in registry_paths:
                try:
                    key = winreg.OpenKey(root, path, 0, winreg.KEY_READ | flags)
                    software_list.extend(self._get_software_from_key(key))
                except WindowsError:
                    continue
                finally:
                    try:
                        winreg.CloseKey(key)
                    except:
                        pass
                    
            return software_list
            
        except Exception as e:
            print(f"Yazılım bilgileri alınırken hata: {str(e)}")
            print(traceback.format_exc())
            return None

    def _get_software_from_key(self, key):
        """Registry anahtarından yazılım bilgilerini al"""
        software_list = []
        i = 0
        
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                try:
                    software_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    software_info = {
                        "name": software_name,
                        "version": "Bilinmiyor",
                        "install_date": "Bilinmiyor",
                        "publisher": "Bilinmiyor"
                    }
                    
                    try:
                        software_info["version"] = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                        software_info["install_date"] = winreg.QueryValueEx(subkey, "InstallDate")[0]
                        software_info["publisher"] = winreg.QueryValueEx(subkey, "Publisher")[0]
                    except:
                        pass
                    
                    software_list.append(software_info)
                except:
                    pass
                finally:
                    winreg.CloseKey(subkey)
                i += 1
                
            except WindowsError:
                break
                
        return software_list

    def save_to_database(self, software_list):
        """Yazılım bilgilerini veritabanına kaydet"""
        try:
           
            connection = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                port=DB_CONFIG['port'],
                charset=DB_CONFIG['charset']
            )
            
            cursor = connection.cursor()
            
           
            cursor.execute(
                "SELECT system_id FROM hwd_system_information ORDER BY created_at DESC LIMIT 1"
            )
            result = cursor.fetchone()
            
            if not result:
                print("Sistem bilgileri bulunamadı. Yazılım bilgileri kaydedilemedi.")
                return False
                
            system_id = result[0]
            
            for software in software_list:
                query = """
                    INSERT INTO software_information 
                    (system_id, software_name, version, install_date, publisher)
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (
                    system_id,
                    software['name'],
                    software['version'],
                    software['install_date'],
                    software['publisher']
                )
                
                try:
                    cursor.execute(query, values)
                    print(f"[{datetime.now()}] Yazılım bilgisi kaydedildi: {software['name']}")
                except Exception as e:
                    print(f"Yazılım bilgisi kaydedilirken hata: {e}")
            
            connection.commit()
            connection.close()
            return True
            
        except Exception as e:
            print(f"Veritabanına yazılım bilgisi eklerken hata: {str(e)}")
            print(traceback.format_exc())
            return False

    def run(self):
        """Ana döngü"""
        print(f"[{datetime.now()}] Yazılım izleme başlatıldı...")
        
        while self.running:
            try:
                
                software_list = self.get_installed_software()
                
                if software_list:
                    
                    self.save_to_database(software_list)
                
               
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"Hata oluştu: {str(e)}")
                print(traceback.format_exc())
                time.sleep(60)  

    def stop(self):
        """İzlemeyi durdur"""
        self.running = False

if __name__ == "__main__":
    monitor = SoftwareMonitor()
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\nProgram kapatılıyor...")
        monitor.stop() 