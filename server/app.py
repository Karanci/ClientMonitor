from flask import Flask, render_template, request, jsonify
from database import db
import mysql.connector
from config import DB_CONFIG
import json
from datetime import datetime, timedelta
import os
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

base_path = get_base_path()
template_path = os.path.join(base_path, 'templates')
static_path = os.path.join(template_path, 'static')

app = Flask(__name__,
           template_folder=template_path,
           static_folder=static_path)

CONNECTION_FILE = "active_connections.json"

def get_db_connection():
    """Veritabanı bağlantısı oluştur"""
    try:
        print("Veritabanı bağlantısı deneniyor...")
        print(f"Bağlantı ayarları: {DB_CONFIG}")
        
        conn = mysql.connector.connect(
            **DB_CONFIG,
            autocommit=True
        )
        print("Veritabanı bağlantısı başarılı!")
        return conn
    except mysql.connector.Error as err:
        print(f"Veritabanı bağlantı hatası: {err}")
        print(f"Hata detayı: {type(err).__name__}")
        import traceback
        print(f"Hata izi: {traceback.format_exc()}")
        return None
    except Exception as e:
        print(f"Beklenmeyen hata: {str(e)}")
        print(f"Hata detayı: {type(e).__name__}")
        import traceback
        print(f"Hata izi: {traceback.format_exc()}")
        return None

def execute_query_with_retry(query, params=None, max_retries=3):
    """Sorguyu yeniden deneme mekanizması ile çalıştır"""
    for attempt in range(max_retries):
        try:
            print(f"Sorgu çalıştırılıyor (Deneme {attempt+1}/{max_retries})...")
            conn = get_db_connection()
            if not conn:
                raise Exception("Veritabanı bağlantısı kurulamadı")
                
            cursor = conn.cursor(dictionary=True)
            if params:
                print(f"Sorgu parametreleri: {params}")
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            print("Sorgu başarıyla çalıştırıldı!")
            return result
            
        except mysql.connector.Error as err:
            print(f"Sorgu çalıştırılırken hata oluştu (Deneme {attempt+1}/{max_retries}): {err}")
            print(f"Hata detayı: {type(err).__name__}")
            import traceback
            print(f"Hata izi: {traceback.format_exc()}")
            if attempt == max_retries - 1:
                raise
            continue
        except Exception as e:
            print(f"Beklenmeyen hata: {str(e)}")
            print(f"Hata detayı: {type(e).__name__}")
            import traceback
            print(f"Hata izi: {traceback.format_exc()}")
            if attempt == max_retries - 1:
                raise
            continue

def get_active_connections():
    """JSON dosyasından aktif bağlantıları oku"""
    try:
        if not os.path.exists(CONNECTION_FILE):
            print(f"Bağlantı dosyası bulunamadı: {CONNECTION_FILE}")
            return {}
            
        with open(CONNECTION_FILE, 'r') as f:
            connections = json.load(f)
            
            # String tarihleri datetime nesnelerine çevir
            for name, data in connections.items():
                if 'last_seen' in data:
                    data['last_seen'] = datetime.fromisoformat(data['last_seen'])
                    
            print(f"Bağlantılar yüklendi: {len(connections)} client")
            return connections
    except Exception as e:
        print(f"Bağlantı dosyası okunurken hata: {e}")
        return {}

def check_pc_status(computer_name):
    """PC'nin durumunu kontrol et"""
    try:
        # Aktif bağlantıları oku
        connections = get_active_connections()
        
        # Bağlantıları debug için logla
        print(f"Kontrol edilen bilgisayar: {computer_name}")
        print(f"Aktif bağlantılar ({len(connections)}): {list(connections.keys())}")
        
        if computer_name in connections:
            last_seen = connections[computer_name]['last_seen']
            time_diff = (datetime.now() - last_seen).total_seconds()
            print(f"Bilgisayar {computer_name} son görülme: {last_seen}, fark: {time_diff} saniye")
            
            if time_diff > 30:
                print(f"Bilgisayar {computer_name} KAPALI olarak işaretlendi (30 saniyeden fazla süre)")
                return {'status': 'KAPALI', 'last_update': last_seen}
            
            print(f"Bilgisayar {computer_name} AÇIK olarak işaretlendi")
            # Burada status'ü tam olarak "AÇIK" şeklinde döndürüyoruz, Açık değil
            return {'status': 'AÇIK', 'last_update': last_seen}
            
        print(f"Bilgisayar {computer_name} bağlantılar listesinde bulunamadı")
        return {'status': 'KAPALI', 'last_update': None}
    except Exception as e:
        print(f"PC durumu kontrol edilirken hata: {e}")
        return {'status': 'HATA', 'last_update': None}

def get_pc_details(computer_name):
    """PC detaylarını getir"""
    try:
        conn = get_db_connection()
        if not conn:
            raise Exception("Veritabanı bağlantısı kurulamadı")
            
        cursor = conn.cursor(dictionary=True)
        
        
        system_query = """
            SELECT *
            FROM hwd_system_information
            WHERE computer_name = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        cursor.execute(system_query, (computer_name,))
        system = cursor.fetchone()
        
        if not system:
            print(f"Sistem bilgisi bulunamadı: {computer_name}")
            cursor.close()
            conn.close()
            return None
            
        system_id = system['system_id']
        print(f"Sistem ID bulundu: {system_id}")
        
      
        try:
            port_query = """
                SELECT port, process_name, pid, username, ip, created_at
                FROM port_information
                WHERE system_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(port_query, (system_id,))
            ports = cursor.fetchall()
            print(f"Port bilgileri alındı: {len(ports)} kayıt")
        except Exception as e:
            print(f"Port bilgileri alınırken hata: {e}")
            ports = []
        
        
        try:
            defender_query = """
                SELECT log_time, source, event_id, description, created_at
                FROM defender_information
                WHERE system_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(defender_query, (system_id,))
            defender = cursor.fetchall()
            print(f"Defender bilgileri alındı: {len(defender)} kayıt")
        except Exception as e:
            print(f"Defender bilgileri alınırken hata: {e}")
            defender = []
        
        
        try:
            event_query = """
                SELECT app_name, event_type, timestamp, created_at
                FROM event_information
                WHERE system_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """
            cursor.execute(event_query, (system_id,))
            events = cursor.fetchall()
            print(f"Event bilgileri alındı: {len(events)} kayıt")
        except Exception as e:
            print(f"Event bilgileri alınırken hata: {e}")
            events = []
        
      
        try:
            network_query = """
                SELECT Ag_karti as adapter_name, IP_adress as ip_address, mac_address, created_at
                FROM hwd_network_information
                WHERE system_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(network_query, (system_id,))
            networks = cursor.fetchall()
            print(f"Ağ bilgileri alındı: {len(networks)} kayıt")
        except Exception as e:
            print(f"Ağ bilgileri alınırken hata: {e}")
            networks = []

        
        try:
            devices_query = """
                SELECT device_name, created_at
                FROM hwd_pnp_devices
                WHERE system_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(devices_query, (system_id,))
            devices = cursor.fetchall()
            print(f"Bağlı cihazlar alındı: {len(devices)} kayıt")
        except Exception as e:
            print(f"Bağlı cihazlar alınırken hata: {e}")
            devices = []

        
        try:
            apps_query = """
                SELECT software_name as app_name, version, publisher, install_date, created_at
                FROM software_information
                WHERE system_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(apps_query, (system_id,))
            applications = cursor.fetchall()
            print(f"Yüklü uygulamalar alındı: {len(applications)} kayıt")
        except Exception as e:
            print(f"Yüklü uygulamalar alınırken hata: {e}")
            applications = []
        
        cursor.close()
        conn.close()
        
        return {
            'system': {
                'computer_name': system['computer_name'],
                'operating_system': system['operating_system'],
                'processor': system['processor'],
                'ram': system['ram'],
                'disk_space': system['disk_space'],
                'manufacturer': system['manufacturer'],
                'model': system['model'],
                'last_update': system['created_at'].isoformat() if system['created_at'] else None
            },
            'ports': [{
                'port': p['port'],
                'process': p['process_name'],
                'pid': p['pid'],
                'username': p['username'],
                'ip': p['ip'],
                'last_update': p['created_at'].isoformat() if p['created_at'] else None
            } for p in ports],
            'defender': [{
                'time': d['log_time'],
                'source': d['source'],
                'event_id': d['event_id'],
                'description': d['description'],
                'last_update': d['created_at'].isoformat() if d['created_at'] else None
            } for d in defender],
            'events': [{
                'app_name': e['app_name'],
                'event_type': e['event_type'],
                'timestamp': e['timestamp'],
                'last_update': e['created_at'].isoformat() if e['created_at'] else None
            } for e in events],
            'networks': [{
                'adapter_name': n['adapter_name'],
                'ip_address': n['ip_address'],
                'mac_address': n['mac_address'],
                'last_update': n['created_at'].isoformat() if n['created_at'] else None
            } for n in networks],
            'devices': [{
                'name': d['device_name'],
                'last_update': d['created_at'].isoformat() if d['created_at'] else None
            } for d in devices],
            'applications': [{
                'name': a['app_name'],
                'version': a['version'],
                'publisher': a['publisher'],
                'install_date': a['install_date'],
                'last_update': a['created_at'].isoformat() if a['created_at'] else None
            } for a in applications]
        }
        
    except Exception as e:
        print(f"Detay getirme hatası: {str(e)}")
        print(f"Hata detayı: {type(e).__name__}")
        import traceback
        print(f"Hata izi: {traceback.format_exc()}")
        return None

@app.route('/')
def index():
    try:
        query = """
            SELECT 
                si.computer_name,
                si.created_at as last_update,
                CASE 
                    WHEN TIMESTAMPDIFF(SECOND, si.created_at, NOW()) <= 60 THEN 'Açık'
                    ELSE 'Kapalı'
                END as status,
                si.operating_system,
                si.processor,
                si.ram,
                si.disk_space,
                si.manufacturer,
                si.model
            FROM hwd_system_information si
            INNER JOIN (
                SELECT computer_name, MAX(created_at) as max_date
                FROM hwd_system_information
                GROUP BY computer_name
            ) latest ON si.computer_name = latest.computer_name AND si.created_at = latest.max_date
        """
        computers = execute_query_with_retry(query)
        return render_template('index.html', computers=computers)
    except Exception as err:
        print(f"Ana sayfa hatası: {str(err)}")
        return render_template('index.html', computers=[])

@app.route('/api/pc-status/<computer_name>')
def pc_status(computer_name):
    
    status_info = check_pc_status(computer_name)
    
    
    details = None
    if status_info['status'] == 'AÇIK':
        details = get_pc_details(computer_name)
    
    return jsonify({
        'status': status_info['status'],
        'last_update': status_info['last_update'].isoformat() if status_info['last_update'] else None,
        'details': details
    })

@app.route('/get_system_details')
def get_system_details():
    try:
        computer_name = request.args.get('computer_name')
        if not computer_name:
            return jsonify({"error": "Bilgisayar adı belirtilmedi"})
            
        print(f"Detaylar istenen bilgisayar: {computer_name}")
            
        
        status_info = check_pc_status(computer_name)
        print(f"PC durumu: {status_info}")
        
        
        details = get_pc_details(computer_name)
        
        if not details:
            return jsonify({"error": "Bilgisayar detayları alınamadı"})
            
        return jsonify({
            'success': True,
            'status': status_info['status'],
            'last_update': status_info['last_update'].isoformat() if status_info['last_update'] else None,
            'details': details
        })
        
    except Exception as err:
        print(f"Sistem detayları hatası: {str(err)}")
        print(f"Hata detayı: {type(err).__name__}")
        import traceback
        print(f"Hata izi: {traceback.format_exc()}")
        return jsonify({
            "error": f"Bilgiler alınırken bir hata oluştu: {str(err)}"
        })

@app.route('/get_computers')
def get_computers():
    try:
        query = """
            SELECT 
                si.computer_name,
                si.operating_system,
                si.processor,
                si.ram,
                si.disk_space,
                si.manufacturer,
                si.model
            FROM hwd_system_information si
            INNER JOIN (
                SELECT computer_name, MAX(created_at) as max_date
                FROM hwd_system_information
                GROUP BY computer_name
            ) latest ON si.computer_name = latest.computer_name 
            AND si.created_at = latest.max_date
        """
        computers = execute_query_with_retry(query)
        
       
        for computer in computers:
            status_info = check_pc_status(computer['computer_name'])
            computer['status'] = status_info['status']
            computer['last_update'] = status_info['last_update'].isoformat() if status_info['last_update'] else None
            
       
        return jsonify(computers)
    except Exception as err:
        print(f"PC listesi hatası: {str(err)}")
        return jsonify([])

@app.route('/status')
def status_page():
    try:
        # En son sistem bilgilerini al
        system_query = """
            SELECT 
                si.computer_name,
                si.created_at as last_update,
                CASE 
                    WHEN TIMESTAMPDIFF(SECOND, si.created_at, NOW()) <= 60 THEN 'Açık'
                    ELSE 'Kapalı'
                END as status,
                si.operating_system,
                si.processor,
                si.ram,
                si.disk_space,
                si.manufacturer,
                si.model
            FROM hwd_system_information si
            INNER JOIN (
                SELECT computer_name, MAX(created_at) as max_date
                FROM hwd_system_information
                GROUP BY computer_name
            ) latest ON si.computer_name = latest.computer_name AND si.created_at = latest.max_date
        """
        computers = execute_query_with_retry(system_query)
        
        # Soket bağlantı durumlarını kontrol et
        for computer in computers:
            status_info = check_pc_status(computer['computer_name'])
            computer['status'] = status_info['status']
            computer['last_update'] = status_info['last_update'].isoformat() if status_info['last_update'] else None
        
        # İstatistikleri hesapla
        total_computers = len(computers)
        online_computers = sum(1 for computer in computers if computer['status'] == 'AÇIK')
        offline_computers = total_computers - online_computers
        
        # İşletim sistemi dağılımlarını hesapla
        os_distribution = {}
        for computer in computers:
            os = computer['operating_system'] or 'Bilinmiyor'
            if os in os_distribution:
                os_distribution[os] += 1
            else:
                os_distribution[os] = 1
        
        # Son 24 saatteki olaylar
        event_query = """
            SELECT 
                ei.app_name, 
                ei.event_type, 
                ei.timestamp, 
                si.computer_name,
                ei.created_at
            FROM event_information ei
            JOIN hwd_system_information si ON ei.system_id = si.system_id
            WHERE ei.created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY ei.created_at DESC
            LIMIT 50
        """
        try:
            recent_events = execute_query_with_retry(event_query)
        except Exception as e:
            print(f"Son olaylar alınırken hata: {e}")
            recent_events = []
        
        # Windows Defender olayları
        defender_query = """
            SELECT 
                di.log_time, 
                di.source, 
                di.event_id, 
                di.description, 
                si.computer_name,
                di.created_at
            FROM defender_information di
            JOIN hwd_system_information si ON di.system_id = si.system_id
            ORDER BY di.created_at DESC
        """
        try:
            defender_events = execute_query_with_retry(defender_query)
        except Exception as e:
            print(f"Defender olayları alınırken hata: {e}")
            defender_events = []
            
        # Açık portlar
        ports_query = """
            SELECT 
                pi.port, 
                pi.process_name, 
                pi.pid, 
                pi.username, 
                pi.ip, 
                si.computer_name,
                pi.created_at
            FROM port_information pi
            JOIN hwd_system_information si ON pi.system_id = si.system_id
            WHERE pi.created_at >= DATE_SUB(NOW(), INTERVAL 12 HOUR)
            ORDER BY pi.created_at DESC
            LIMIT 50
        """
        try:
            open_ports = execute_query_with_retry(ports_query)
        except Exception as e:
            print(f"Açık portlar alınırken hata: {e}")
            open_ports = []
        
        # Verileri şablona ilet
        return render_template('status.html', 
                              computers=computers,
                              total_computers=total_computers,
                              online_computers=online_computers,
                              offline_computers=offline_computers,
                              os_distribution=os_distribution,
                              recent_events=recent_events,
                              defender_events=defender_events,
                              open_ports=open_ports)
    except Exception as err:
        print(f"Sistem durumu sayfası hatası: {str(err)}")
        import traceback
        print(f"Hata izi: {traceback.format_exc()}")
        return render_template('status.html', 
                              computers=[],
                              total_computers=0,
                              online_computers=0,
                              offline_computers=0,
                              os_distribution={},
                              recent_events=[],
                              defender_events=[],
                              open_ports=[])

@app.route('/api/get_all_pc_status')
def get_all_pc_status():
    try:
        # En son sistem bilgilerini al
        system_query = """
            SELECT 
                si.computer_name,
                si.created_at as last_update,
                CASE 
                    WHEN TIMESTAMPDIFF(SECOND, si.created_at, NOW()) <= 60 THEN 'Açık'
                    ELSE 'Kapalı'
                END as status,
                si.operating_system,
                si.processor,
                si.ram,
                si.disk_space,
                si.manufacturer,
                si.model
            FROM hwd_system_information si
            INNER JOIN (
                SELECT computer_name, MAX(created_at) as max_date
                FROM hwd_system_information
                GROUP BY computer_name
            ) latest ON si.computer_name = latest.computer_name AND si.created_at = latest.max_date
        """
        computers = execute_query_with_retry(system_query)
        
        # Aktif bağlantıları oku
        connections = get_active_connections()
        
        # Soket bağlantı durumlarını kontrol et
        for computer in computers:
            status_info = check_pc_status(computer['computer_name'])
            computer['status'] = status_info['status']
            computer['last_update'] = status_info['last_update'].isoformat() if status_info['last_update'] else None
        
        # Aktif bağlantıda olup veritabanında olmayan bilgisayarları ekle
        for computer_name in connections:
            if not any(c['computer_name'] == computer_name for c in computers):
                computers.append({
                    'computer_name': computer_name,
                    'status': 'AÇIK',
                    'last_update': connections[computer_name]['last_seen'].isoformat(),
                    'operating_system': 'Bilinmiyor',
                    'processor': 'Bilinmiyor',
                    'ram': 'Bilinmiyor',
                    'disk_space': 'Bilinmiyor',
                    'manufacturer': 'Bilinmiyor',
                    'model': 'Bilinmiyor'
                })
        
        # İstatistikleri hesapla
        total_computers = len(computers)
        online_computers = sum(1 for computer in computers if computer['status'] == 'AÇIK')
        offline_computers = total_computers - online_computers
        
        # İşletim sistemi dağılımlarını hesapla
        os_distribution = {}
        for computer in computers:
            os = computer['operating_system'] or 'Bilinmiyor'
            if os in os_distribution:
                os_distribution[os] += 1
            else:
                os_distribution[os] = 1
                
        return jsonify({
            'computers': computers,
            'total_computers': total_computers,
            'online_computers': online_computers,
            'offline_computers': offline_computers,
            'os_distribution': os_distribution
        })
        
    except Exception as err:
        print(f"API hatası: {str(err)}")
        import traceback
        print(f"Hata izi: {traceback.format_exc()}")
        return jsonify({
            'error': str(err),
            'computers': [],
            'total_computers': 0,
            'online_computers': 0,
            'offline_computers': 0,
            'os_distribution': {}
        }), 500

# Sadece aktif bağlantıları görüntüleyen basit bir API
@app.route('/api/active_connections')
def active_connections():
    connections = get_active_connections()
    
    active = []
    for name, info in connections.items():
        active.append({
            'name': name,
            'last_seen': info['last_seen'].isoformat(),
            'address': str(info['address'])
        })
    
    return jsonify({
        'count': len(active),
        'connections': active
    })

@app.route('/security')
def security_page():
    try:
        # Windows Defender olayları
        defender_query = """
            SELECT 
                di.log_time, 
                di.source, 
                di.event_id, 
                di.description, 
                si.computer_name,
                di.created_at
            FROM defender_information di
            JOIN hwd_system_information si ON di.system_id = si.system_id
            ORDER BY di.created_at DESC
        """
        try:
            defender_events = execute_query_with_retry(defender_query)
        except Exception as e:
            print(f"Defender olayları alınırken hata: {e}")
            defender_events = []
        
        # İstatistikleri hesapla
        total_computers_query = "SELECT COUNT(DISTINCT computer_name) as total FROM hwd_system_information"
        total_events_query = "SELECT COUNT(*) as total FROM defender_information"
        total_warnings_query = """
            SELECT COUNT(*) as total FROM defender_information 
            WHERE event_id IN (1006, 1007, 1008, 1009, 1116, 1117, 1073758208, -1073725430) 
            OR description LIKE '%tehdit%' OR description LIKE '%virüs%' OR description LIKE '%malware%'
        """
        
        try:
            total_computers = execute_query_with_retry(total_computers_query)[0]['total']
            total_events = execute_query_with_retry(total_events_query)[0]['total']
            total_warnings = execute_query_with_retry(total_warnings_query)[0]['total']
        except Exception as e:
            print(f"İstatistikler alınırken hata: {e}")
            total_computers = 0
            total_events = 0
            total_warnings = 0
        
        # Günlük olay sayısını hesapla (son 30 gün)
        daily_events_query = """
            SELECT 
                DATE(created_at) as event_date,
                COUNT(*) as event_count
            FROM defender_information
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(created_at)
            ORDER BY event_date
        """
        try:
            daily_events = execute_query_with_retry(daily_events_query)
        except Exception as e:
            print(f"Günlük olaylar alınırken hata: {e}")
            daily_events = []
        
        # Olay türleri dağılımı
        event_types_query = """
            SELECT 
                event_id,
                COUNT(*) as count
            FROM defender_information
            GROUP BY event_id
            ORDER BY count DESC
            LIMIT 10
        """
        try:
            event_types = execute_query_with_retry(event_types_query)
        except Exception as e:
            print(f"Olay türleri alınırken hata: {e}")
            event_types = []
            
        # Bilgisayarlara göre risk dağılımı
        computer_risks_query = """
            SELECT 
                si.computer_name,
                COUNT(*) as total_events,
                SUM(CASE 
                    WHEN di.event_id IN (1006, 1007, 1008, 1009, 1116, 1117, 1073758208, -1073725430) 
                         OR di.description LIKE '%tehdit%' OR di.description LIKE '%virüs%' OR di.description LIKE '%malware%' 
                    THEN 1 ELSE 0 END) as high_events,
                SUM(CASE 
                    WHEN di.event_id IN (1005, 1010, 1118, 1119, -1073725430, 1073742724, 1013, 1015, 1121, 1122, 1123, 8004) 
                    THEN 1 ELSE 0 END) as medium_events,
                SUM(CASE 
                    WHEN di.event_id NOT IN (1005, 1006, 1007, 1008, 1009, 1010, 1116, 1117, 1118, 1119, 1073758208, -1073725430, 1073742724, 1013, 1015, 1121, 1122, 1123, 8004)
                         AND di.description NOT LIKE '%tehdit%' AND di.description NOT LIKE '%virüs%' AND di.description NOT LIKE '%malware%'
                    THEN 1 ELSE 0 END) as low_events
            FROM defender_information di
            JOIN hwd_system_information si ON di.system_id = si.system_id
            GROUP BY si.computer_name
            ORDER BY high_events DESC, medium_events DESC
        """
        try:
            computer_risks_data = execute_query_with_retry(computer_risks_query)
            
            # Risk skorlarını hesapla
            computer_risks = []
            for computer in computer_risks_data:
                # Risk skoru hesapla (yüksek: 10 puan, orta: 5 puan, düşük: 1 puan)
                risk_score = (computer['high_events'] * 10 + computer['medium_events'] * 5 + computer['low_events'] * 1)
                
                # Toplam olay sayısına göre normalize et (0-100 arası)
                max_score = computer['total_events'] * 10  # Tüm olaylar yüksek öncelikli olsaydı
                normalized_score = int((risk_score / max_score) * 100) if max_score > 0 else 0
                
                # Risk seviyesini belirle
                risk_level = "danger" if normalized_score >= 70 else "warning" if normalized_score >= 40 else "success"
                
                computer_risks.append({
                    'computer_name': computer['computer_name'],
                    'total_events': computer['total_events'],
                    'high_events': computer['high_events'],
                    'medium_events': computer['medium_events'],
                    'low_events': computer['low_events'],
                    'risk_score': normalized_score,
                    'risk_level': risk_level
                })
        except Exception as e:
            print(f"Bilgisayar risk verileri alınırken hata: {e}")
            computer_risks = []
            
        # Kritik olayların sayısını hesapla
        critical_events = sum(c['high_events'] for c in computer_risks) if computer_risks else 0
            
        return render_template('security.html',
                              defender_events=defender_events,
                              total_computers=total_computers,
                              total_events=total_events,
                              total_warnings=total_warnings,
                              critical_events=critical_events,
                              daily_events=daily_events,
                              event_types=event_types,
                              computer_risks=computer_risks)
                              
    except Exception as err:
        print(f"Güvenlik sayfası hatası: {str(err)}")
        import traceback
        print(f"Hata izi: {traceback.format_exc()}")
        return render_template('security.html',
                              defender_events=[],
                              total_computers=0,
                              total_events=0,
                              total_warnings=0,
                              critical_events=0,
                              daily_events=[],
                              event_types=[],
                              computer_risks=[])

if __name__ == '__main__':
    # Flask uygulamasını başlat
    app.run(debug=True, host='0.0.0.0', port=5000)  # Debug modunu açık bırakabiliriz