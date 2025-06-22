-- Aşağıdaki kod, bilgisayar sistemlerinden bilgi toplamak ve bu bilgileri
-- anlamlı bir şekilde saklamak için optimize edilmiş bir veritabanı şemasıdır.
-- İlişkiler, sistem_id ve diğer anahtar alanlar kullanılarak Foreign Key ile kurulmuştur.
-- -----------------------------------------------------
-- Table: hwd_system_information
-- Sistem bilgilerini (donanım, işletim sistemi) saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`hwd_system_information` (
  `system_id` INT NOT NULL AUTO_INCREMENT,
  `operating_system` VARCHAR(45),
  `processor` VARCHAR(80),
  `ram` VARCHAR(90),
  `disk_space` VARCHAR(90),
  `manufacturer` VARCHAR(90),
  `model` VARCHAR(90),
  PRIMARY KEY (`system_id`)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ---------------------------------------
-- -----------------------------------------------------
-- Table: computer_identifier
-- Bilgisayarları benzersiz bir şekilde tanımlamak için kullanılır.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`computer_identifier` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `mac` VARCHAR(45) NOT NULL,
  `computer_name` VARCHAR(45) NOT NULL,
  `system_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`mac`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--------------
-- Table: defender_information
-- Sistem güvenlik loglarını saklar (örneğin Windows Defender).
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`defender_information` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `log_time` DATETIME NOT NULL,
  `source` VARCHAR(45) NOT NULL,
  `event_id` INT NOT NULL,
  `description` TEXT NOT NULL,
  `system_id` INT,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: event_information
-- Sistem uygulama olaylarını (açılma/kapanma) saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`event_information` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `app_name` VARCHAR(70) NOT NULL,
  `event_type` ENUM('opened', 'closed') NOT NULL,
  `timestamp` DATETIME NOT NULL,
  `system_id` INT,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: firewall_log_information
-- Firewall loglarını (trafik verisi) saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`firewall_log_information` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `timestamp` DATETIME NOT NULL,
  `action` VARCHAR(45) NOT NULL,
  `protocol` VARCHAR(45) NOT NULL,
  `source_ip` VARCHAR(45),
  `destination_ip` VARCHAR(45),
  `source_port` INT,
  `destination_port` INT,
  `bytes_sent` INT,
  `bytes_received` INT,
  `action_flags` VARCHAR(50),
  `system_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: hwd_network_information
-- Ağ cihazlarına ait MAC adresi, IP adresi gibi bilgileri saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`hwd_network_information` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `mac_address` VARCHAR(70) NOT NULL,
  `network_card` VARCHAR(45) NOT NULL,
  `ip_address` VARCHAR(45) NOT NULL,
  `system_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE (`mac_address`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: hwd_pnp_devices
-- Tak ve çalıştır cihaz bilgilerini saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`hwd_pnp_devices` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `system_id` INT,
  `device_name` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: port_information
-- Açık port bilgilerini ve bu portları kullanan süreçleri saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`port_information` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `ip` VARCHAR(45) NOT NULL,
  `port` INT NOT NULL,
  `process_name` VARCHAR(45) NOT NULL,
  `pid` INT NOT NULL,
  `username` VARCHAR(65) NOT NULL,
  `system_id` INT,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: signup
-- Kullanıcı kayıt bilgilerini saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`signup` (
  `idsignup` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(30) NOT NULL,
  `email` VARCHAR(50) NOT NULL,
  `password` VARCHAR(60) NOT NULL, -- Güvenlik için şifre boyutu artırıldı.
  PRIMARY KEY (`idsignup`),
  UNIQUE (`email`)
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: soft_install_information
-- Yüklenen yazılımların bilgilerini saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`soft_install_information` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `program` VARCHAR(100) NOT NULL,
  `system_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: soft_license_information
-- Yazılım lisans bilgilerini saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`soft_license_information` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `program_name` VARCHAR(100) NOT NULL,
  `publisher` VARCHAR(100) NOT NULL,
  `system_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- -----------------------------------------------------
-- Table: soft_update_information
-- Yazılım güncelleme bilgilerini saklar.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `computer_information`.`soft_update_information` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `package_name` VARCHAR(100) NOT NULL,
  `package_version` VARCHAR(100) NOT NULL,
  `status` VARCHAR(45) NOT NULL,
  `system_id` INT NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`system_id`) REFERENCES `computer_information`.`hwd_system_information`(`system_id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARACTER SET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
