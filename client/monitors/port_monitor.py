import psutil
import requests
import time
from datetime import datetime
import traceback
import mysql.connector
from config import DB_CONFIG

class PortMonitor:
    def __init__(self):
        self.running = True
        self.interval = 300 
        self.api_key = "60d977ce-4c62-45b2-976d-8018b74a9897"

    def get_open_ports(self):
        """Sistemdeki açık portları tespit et"""
        try:
            open_ports = {}
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'LISTEN':
                    try:
                        process = psutil.Process(conn.pid)
                        open_ports[conn.laddr.port] = {
                            'ip': conn.laddr.ip,
                            'process': process.name(),
                            'pid': conn.pid,
                            'username': process.username()
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            return open_ports
        except Exception as e:
            print(f"Port bilgileri alınırken hata: {str(e)}")
            print(traceback.format_exc())
            return None

    def check_vulnerabilities(self, port):
        """Port için güvenlik açıklarını kontrol et"""
        try:
            port_services = {
                80: {"name": "HTTP", "keywords": ["http", "apache", "nginx", "iis"]},
                443: {"name": "HTTPS", "keywords": ["https", "ssl", "tls"]},
                21: {"name": "FTP", "keywords": ["ftp", "vsftpd"]},
                22: {"name": "SSH", "keywords": ["ssh", "openssh"]},
                23: {"name": "Telnet", "keywords": ["telnet"]},
                25: {"name": "SMTP", "keywords": ["smtp", "mail"]},
                53: {"name": "DNS", "keywords": ["dns", "bind"]},
                3306: {"name": "MySQL", "keywords": ["mysql", "mariadb"]},
                3389: {"name": "RDP", "keywords": ["rdp", "remote desktop"]},
                445: {"name": "SMB", "keywords": ["smb", "samba"]},
                139: {"name": "NetBIOS", "keywords": ["netbios"]},
                8080: {"name": "HTTP-Proxy", "keywords": ["http", "proxy"]}
            }
            
            service = port_services.get(port, {"name": "Bilinmeyen", "keywords": []})
            vulnerabilities = []
            
            headers = {'apiKey': self.api_key}
            
            for keyword in service["keywords"]:
                try:
                    params = {
                        'keywordSearch': keyword,
                        'pubStartDate': '2023-01-01T00:00:00.000'
                    }
                    
                    response = requests.get(
                        "https://services.nvd.nist.gov/rest/json/cves/2.0", 
                        headers=headers, 
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        vulns = data.get('vulnerabilities', [])
                        
                        for vuln in vulns[:3]:  
                            cve = vuln['cve']
                            vuln_info = {
                                'id': cve.get('id'),
                                'severity': cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 'Bilinmiyor'),
                                'description': cve.get('descriptions', [{}])[0].get('value', 'Açıklama yok')
                            }
                            vulnerabilities.append(vuln_info)
                    
                except Exception as e:
                    print(f"Güvenlik açığı kontrolü sırasında hata: {str(e)}")
            
            return service["name"], vulnerabilities
            
        except Exception as e:
            print(f"Güvenlik açığı kontrolü sırasında hata: {str(e)}")
            print(traceback.format_exc())
            return None, None

    def save_to_database(self, port_info):
        """Port bilgilerini veritabanına kaydet"""
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
                print("Sistem bilgileri bulunamadı. Port bilgileri kaydedilemedi.")
                return False
                
            system_id = result[0]
            
            for port, info in port_info.items():
                query = """
                    INSERT INTO port_information 
                    (system_id, port, process_name, pid, username, ip)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                values = (
                    system_id,
                    port,
                    info['process'],
                    info['pid'],
                    info['username'],
                    info['ip']
                )
                
                try:
                    cursor.execute(query, values)
                    print(f"[{datetime.now()}] Port bilgisi kaydedildi: {info['ip']}:{port}")
                except Exception as e:
                    print(f"Port bilgisi kaydedilirken hata: {e}")
            
            connection.commit()
            connection.close()
            return True
            
        except Exception as e:
            print(f"Veritabanına port bilgisi eklerken hata: {str(e)}")
            print(traceback.format_exc())
            return False

    def run(self):
        """Ana döngü"""
        print(f"[{datetime.now()}] Port izleme başlatıldı...")
        
        while self.running:
            try:
                # Port bilgilerini topla
                open_ports = self.get_open_ports()
                
                if open_ports:
                    # Veritabanına kaydet
                    self.save_to_database(open_ports)
                    
                    for port in open_ports:
                        service_name, vulnerabilities = self.check_vulnerabilities(port)
                        if vulnerabilities:
                            print(f"\n[{datetime.now()}] Port {port} ({service_name}) için güvenlik açıkları:")
                            for vuln in vulnerabilities:
                                print(f"CVE: {vuln['id']}")
                                print(f"Şiddet: {vuln['severity']}")
                                print(f"Açıklama: {vuln['description']}\n")
                
             
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"Hata oluştu: {str(e)}")
                print(traceback.format_exc())
                time.sleep(60) 

    def stop(self):
        """İzlemeyi durdur"""
        self.running = False

if __name__ == "__main__":
    monitor = PortMonitor()
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\nProgram kapatılıyor...")
        monitor.stop() 