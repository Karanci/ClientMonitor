PC İZLEME UYGULAMASI - KURULUM VE ÇALIŞTIRMA KILAVUZU
=================================================

1. GEREKSİNİMLER
----------------
- Python 3.10 veya üzeri
- MySQL veritabanı
- İnternet bağlantısı
- Windows işletim sistemi

2. KURULUM
----------
a) Gerekli Python paketlerinin kurulumu:
   pip install -r requirements.txt

b) Veritabanı Ayarları:
   - server/config.py dosyasında veritabanı bağlantı bilgilerini düzenleyin
   - Örnek config.py içeriği:
     DB_CONFIG = {
         'host': 'veritabani_sunucusu',
         'user': 'kullanici_adi',
         'password': 'sifre',
         'database': 'veritabani_adi',
         'port': port_numarasi
     }

3. SUNUCU BAŞLATMA
-----------------
a) Normal Çalıştırma:
   - server klasörüne gidin
   - python app.py komutunu çalıştırın
   
b) EXE ile Çalıştırma:
   - server/dist klasöründeki app.exe dosyasını çalıştırın
   - ÖNEMLİ: templates klasörünün app.exe ile aynı dizinde olduğundan emin olun
   - EXE çalıştırma sorunlarında:
     * Yönetici olarak çalıştırmayı deneyin
     * Antivirüs programının engellemediğinden emin olun
     * Windows Defender'ın erişim iznini kontrol edin

4. İSTEMCİ BAŞLATMA
------------------
a) Normal Çalıştırma:
   - client klasörüne gidin
   - python client_heartbeat.py komutunu çalıştırın
   
b) EXE ile Çalıştırma:
   - client/dist klasöründeki client_heartbeat.exe dosyasını çalıştırın
   - Program arkaplanda çalışır, Windows bildirimleriyle durum bilgisi verir
   - Çalışma durumunu logs klasöründen kontrol edebilirsiniz

5. BAĞLANTI AYARLARI
-------------------
a) Sunucu IP Adresi Yapılandırması:
   - ÖNEMLİ: Her yeni kurulumda IP adresinin güncellenmesi gerekir
   - client/client_heartbeat.py dosyasında:
     * SERVER_HOST değişkenini sunucunun IP adresi ile güncelleyin
     * Örnek: SERVER_HOST = '192.168.1.33'
     * IP adresini öğrenmek için sunucu bilgisayarda "ipconfig" komutunu kullanın
     * Yerel ağda çalışıyorsanız yerel IP adresini kullanın
     * İnternet üzerinden bağlanacaksanız public IP adresini kullanın

b) Port Ayarları:
   - Varsayılan port: 5002
   - Port değişikliği için:
     * Sunucu tarafında: app.py dosyasında port numarasını değiştirin
     * İstemci tarafında: client_heartbeat.py dosyasında SERVER_PORT değişkenini güncelleyin
   - Güvenlik duvarı ayarlarında seçilen portun açık olduğundan emin olun

6. UYGULAMA ÖZELLİKLERİ
----------------------
- Bilgisayar donanım bilgilerini izleme
- Windows Defender loglarını takip etme
- Açık portları izleme
- Yüklü yazılımları listeleme
- Gerçek zamanlı bağlantı durumu takibi
- Web arayüzü üzerinden izleme

7. WEB ARAYÜZÜ
-------------
- Tarayıcıdan http://localhost:5000 adresine girin
- Ana sayfa: Bağlı bilgisayarların listesi
- Detay sayfası: Her bilgisayar için detaylı bilgiler
- Güvenlik sayfası: Windows Defender olayları

8. HATA AYIKLAMA
---------------
a) Log Dosyaları:
   - İstemci logları: client/logs klasöründe
   - Sunucu logları: server/logs klasöründe
   - Her gün için ayrı log dosyası oluşturulur

b) Sık Karşılaşılan Sorunlar:
   - "TemplateNotFound" hatası:
     * templates klasörünün exe ile aynı dizinde olduğunu kontrol edin
   - "Connection Refused" hatası:
     * IP adresinin doğru olduğunu kontrol edin
     * Port numarasının açık olduğunu kontrol edin
     * Sunucunun çalışır durumda olduğunu kontrol edin
   - "Permission Denied" hatası:
     * Programı yönetici olarak çalıştırın
     * Antivirüs ayarlarını kontrol edin

9. GÜVENLİK
----------
- Tüm veritabanı bağlantıları şifrelidir
- Hassas bilgiler şifrelenerek saklanır
- Windows Defender entegrasyonu mevcuttur
- Güvenlik duvarı yapılandırması önemlidir

10. KAPATMA
----------
- Sunucu: CTRL+C ile kapatılır
- İstemci: CTRL+C ile kapatılır
- EXE versiyonları: 
  * Sunucu: Konsol penceresini kapatarak
  * İstemci: Görev yöneticisinden sonlandırarak 