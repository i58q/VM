import os
from dotenv import load_dotenv
from pathlib import Path

# .env dosyasını yükle
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    # Bot Ayarları
    TOKEN = os.getenv('DISCORD_TOKEN')
    PREFIX = os.getenv('BOT_PREFIX', '!')
    OWNER_ID = int(os.getenv('OWNER_ID', 0))
    
    # Veritabanı
    DB_PATH = os.getenv('DB_PATH', 'data/database.db')
    
    # Kanal ID'leri
    LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', 0))
    WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
    
    # Rol ID'leri
    MUTE_ROLE_ID = int(os.getenv('MUTE_ROLE_ID', 0))
    ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID', 0))
    MOD_ROLE_ID = int(os.getenv('MOD_ROLE_ID', 0))
    
    # Ekonomi Ayarları
    CURRENCY_NAME = "💰 Coin"
    DAILY_REWARD = 100
    WORK_COOLDOWN = 60  # saniye
    MIN_WORK_REWARD = 10
    MAX_WORK_REWARD = 50
    
    # Seviye Ayarları
    XP_MULTIPLIER = 10
    VOICE_XP_MULTIPLIER = 5
    MAX_LEVEL = 100
    
    # Renkler
    COLOR_SUCCESS = 0x00FF00
    COLOR_ERROR = 0xFF0000
    COLOR_WARNING = 0xFFA500
    COLOR_INFO = 0x00BFFF
    
    @classmethod
    def validate(cls):
        """Token'ın geçerli olup olmadığını kontrol et"""
        if not cls.TOKEN:
            raise ValueError("❌ DISCORD_TOKEN bulunamadı! .env dosyasını kontrol et.")
        if len(cls.TOKEN) < 50:
            raise ValueError("❌ Token geçersiz! Lütfen doğru token'ı gir.")
        return True

# Token'ı doğrula
Config.validate()
