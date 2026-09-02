import aiosqlite
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Veritabanını oluştur"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Kullanıcılar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                discriminator TEXT,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                last_daily DATETIME,
                last_work DATETIME,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_banned BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Uyarılar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Susturmalar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                duration INTEGER,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME
            )
        ''')
        
        # Çekilişler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                channel_id INTEGER,
                prize TEXT,
                winners INTEGER,
                end_time DATETIME,
                ended BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Çekiliş katılımcıları
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_participants (
                giveaway_id INTEGER,
                user_id INTEGER,
                PRIMARY KEY (giveaway_id, user_id)
            )
        ''')
        
        # Ticket tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                status TEXT DEFAULT 'Açık',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                closed_at DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Kullanıcı bilgilerini al"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'SELECT * FROM users WHERE user_id = ?',
                (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    
    async def create_user(self, user_id: int, username: str, discriminator: str = "0000"):
        """Yeni kullanıcı oluştur"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT OR IGNORE INTO users 
                   (user_id, username, discriminator) 
                   VALUES (?, ?, ?)''',
                (user_id, username, discriminator)
            )
            await db.commit()
    
    async def add_xp(self, user_id: int, xp_amount: int):
        """XP ekle"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE users SET xp = xp + ? WHERE user_id = ?',
                (xp_amount, user_id)
            )
            await db.commit()
    
    async def add_coins(self, user_id: int, amount: int):
        """Coin ekle"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'UPDATE users SET coins = coins + ? WHERE user_id = ?',
                (amount, user_id)
            )
            await db.commit()
    
    async def add_warning(self, user_id: int, moderator_id: int, reason: str):
        """Uyarı ekle"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT INTO warnings 
                   (user_id, moderator_id, reason) 
                   VALUES (?, ?, ?)''',
                (user_id, moderator_id, reason)
            )
            await db.commit()
    
    async def get_warnings(self, user_id: int) -> List[Dict]:
        """Kullanıcının uyarılarını al"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                '''SELECT * FROM warnings 
                   WHERE user_id = ? AND active = TRUE''',
                (user_id,)
            )
            return [dict(row) for row in await cursor.fetchall()]
    
    async def add_mute(self, user_id: int, moderator_id: int, reason: str, duration: int):
        """Susturma ekle"""
        from datetime import datetime, timedelta
        end_time = datetime.now() + timedelta(minutes=duration)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT INTO mutes 
                   (user_id, moderator_id, reason, duration, end_time) 
                   VALUES (?, ?, ?, ?, ?)''',
                (user_id, moderator_id, reason, duration, end_time)
            )
            await db.commit()
    
    async def get_active_mutes(self) -> List[Dict]:
        """Aktif susturmaları al"""
        from datetime import datetime
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                '''SELECT * FROM mutes 
                   WHERE end_time > datetime('now')''',
            )
            return [dict(row) for row in await cursor.fetchall()]
