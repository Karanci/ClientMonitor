import win32evtlog
import time
from datetime import datetime
import traceback
import mysql.connector
from config import DB_CONFIG

class DefenderMonitor:
    def __init__(self):
        self.running = True
        self.interval = 300  
        self.max_events = 10  

    def collect_defender_logs(self):
        """Windows Defender loglarını topla"""
        try:
            server = 'localhost'
            log_type = 'Microsoft-Windows-Windows Defender/Operational'
            
            hand = win32evtlog.OpenEventLog(server, log_type)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            events = []
            event_count = 0
            
            while event_count < self.max_events:
                events_batch = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events_batch:
                    break
                    
                for event in events_batch:
                    if event_count >= self.max_events:
                        break
                        
                    event_dict = {
                        'log_time': event.TimeGenerated.strftime('%Y-%m-%d %H:%M:%S'),
                        'source': event.SourceName,
                        'event_id': event.EventID,
                        'description': event.StringInserts if event.StringInserts else ['No description']
                    }
                    events.append(event_dict)
                    event_count += 1
            
            return events
            
        except Exception as e:
            print(f"Windows Defender logları alınırken hata: {str(e)}")
            print(traceback.format_exc())
            return None

    def save_to_database(self, events):
        """Defender loglarını veritabanına kaydet"""
        try:
            # Veritabanı bağlantısı
            connection = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                port=DB_CONFIG['port'],
                charset=DB_CONFIG['charset']
            )
            
            cursor = connection.cursor()
            
            # Önce system_id'yi al
            cursor.execute(
                "SELECT system_id FROM hwd_system_information ORDER BY created_at DESC LIMIT 1"
            )
            result = cursor.fetchone()
            
            if not result:
                print("Sistem bilgileri bulunamadı. Defender logları kaydedilemedi.")
                return False
                
            system_id = result[0]
            
            for event in events:
                # StringInserts listesini stringe çevir
                description = ' '.join(event['description']) if isinstance(event['description'], list) else str(event['description'])
                
                query = """
                    INSERT INTO defender_information 
                    (system_id, log_time, source, event_id, description)
                    VALUES (%s, %s, %s, %s, %s)
                """
                values = (
                    system_id,
                    event['log_time'],
                    event['source'],
                    event['event_id'],
                    description
                )
                try:
                    cursor.execute(query, values)
                    print(f"[{datetime.now()}] Defender log kaydedildi: Event ID {event['event_id']}")
                except Exception as e:
                    print(f"Log kaydedilirken hata: {e}")
            
            connection.commit()
            connection.close()
            return True

        except Exception as e:
            print(f"Veritabanına log eklerken hata: {str(e)}")
            print(traceback.format_exc())
            return False

    def run(self):
        """Ana döngü"""
        print(f"[{datetime.now()}] Windows Defender izleme başlatıldı...")
        
        while self.running:
            try:
                # Logları topla
                events = self.collect_defender_logs()
            
                if events:
                    self.save_to_database(events)
                
             
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"Hata oluştu: {str(e)}")
                print(traceback.format_exc())
                time.sleep(60)  

    def stop(self):
        """İzlemeyi durdur"""
        self.running = False

if __name__ == "__main__":
    monitor = DefenderMonitor()
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\nProgram kapatılıyor...")
        monitor.stop() 