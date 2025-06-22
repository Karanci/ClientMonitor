import psutil
import time
from datetime import datetime
import traceback
import mysql.connector
from config import DB_CONFIG

class EventMonitor:
    def __init__(self):
        self.running = True
        self.interval = 5  

    def insert_event(self, app_name, event_type):
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
                print("Sistem bilgileri bulunamadı. Event bilgisi kaydedilemedi.")
                return
                
            system_id = result[0]

            
            query = """
                INSERT INTO event_information (app_name, event_type, timestamp, system_id)
                VALUES (%s, %s, %s, %s)
            """
            timestamp = datetime.now()
            cursor.execute(query, (app_name, event_type, timestamp, system_id))
            connection.commit()
            print(f"[{timestamp}] Event kaydedildi: {app_name} - {event_type}")
            
            connection.close()
            
        except Exception as err:
            print(f"Veritabanına event eklerken hata oluştu: {err}")
            print(traceback.format_exc())

    def monitor_events(self):
        """Uygulama olaylarını izle"""
        running_apps = set()
        print(f"[{datetime.now()}] Olay izleme başlatıldı...")
        
        while self.running:
            try:
                current_apps = set()

                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        current_apps.add(proc.info['name'].lower())
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        continue

                
                new_apps = current_apps - running_apps
                for app in new_apps:
                    self.insert_event(app, "opened")

                
                closed_apps = running_apps - current_apps
                for app in closed_apps:
                    self.insert_event(app, "closed")

                running_apps = current_apps
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"Hata oluştu: {str(e)}")
                print(traceback.format_exc())
                time.sleep(60)  

    def stop(self):
        """İzlemeyi durdur"""
        self.running = False

if __name__ == "__main__":
    monitor = EventMonitor()
    try:
        monitor.monitor_events()
    except KeyboardInterrupt:
        print("\nProgram kapatılıyor...")
        monitor.stop() 