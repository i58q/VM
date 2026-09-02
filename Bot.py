import discord
from discord.ext import commands
import asyncio
import logging
from datetime import datetime
from config import Config
from database import Database

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarpelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=None,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="⭐ Marpel Bot | !yardım"
            )
        )
        
        self.config = Config
        self.db = Database(Config.DB_PATH)
        self.uptime = datetime.now()
        self.startup_time = datetime.now()
        
        # Token kontrolü
        if not Config.TOKEN:
            raise ValueError("❌ Token bulunamadı! .env dosyasını kontrol et.")
        
        logger.info("🤖 Marpel Bot başlatılıyor...")
    
    async def setup_hook(self):
        """Cog'ları yükle"""
        try:
            # Cog'ları yükle
            await self.load_extension('cogs.admin')
            await self.load_extension('cogs.moderation')
            await self.load_extension('cogs.economy')
            await self.load_extension('cogs.fun')
            await self.load_extension('cogs.leveling')
            await self.load_extension('cogs.tickets')
            await self.load_extension('cogs.utility')
            
            logger.info("✅ Tüm cog'lar başarıyla yüklendi!")
            
            # Slash komutlarını senkronize et
            await self.tree.sync()
            logger.info("✅ Slash komutları senkronize edildi!")
            
        except Exception as e:
            logger.error(f"❌ Cog yükleme hatası: {e}")
    
    async def on_ready(self):
        """Bot hazır olduğunda"""
        logger.info(f"✅ {self.user} olarak giriş yapıldı!")
        logger.info(f"📊 {len(self.guilds)} sunucuda aktif")
        logger.info(f"👥 {sum(guild.member_count for guild in self.guilds)} kullanıcıya hizmet veriyor")
        
        # Durum mesajı
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"⭐ {len(self.guilds)} sunucu | !yardım"
            )
        )
    
    async def on_command_error(self, ctx, error):
        """Komut hatalarını yakala"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Yetki Hatası",
                description="Bu komutu kullanmak için gerekli yetkilere sahip değilsin!",
                color=Config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Eksik Argüman",
                description=f"Lütfen gerekli argümanları gir.\n{ctx.command.help}",
                color=Config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        # Diğer hatalar
        logger.error(f"Hata: {error}")
        embed = discord.Embed(
            title="❌ Bir Hata Oluştu",
            description=f"```{str(error)[:500]}```",
            color=Config.COLOR_ERROR
        )
        await ctx.send(embed=embed)
    
    async def on_message(self, message):
        """Mesaj geldiğinde"""
        if message.author.bot:
            return
        
        # Kullanıcıyı veritabanına ekle
        await self.db.create_user(
            message.author.id,
            message.author.name,
            message.author.discriminator
        )
        
        # XP sistemi (eğer leveling cog yüklüyse)
        leveling_cog = self.get_cog('Leveling')
        if leveling_cog:
            await leveling_cog.add_xp(message.author)
        
        # Komutları işle
        await self.process_commands(message)
    
    async def on_member_join(self, member):
        """Üye katıldığında"""
        # Hoş geldin mesajı
        welcome_channel = self.get_channel(Config.WELCOME_CHANNEL_ID)
        if welcome_channel:
            embed = discord.Embed(
                title="👋 Hoş Geldin!",
                description=f"{member.mention} sunucumuza katıldı!\n\n"
                           f"📌 Kuralları okumayı unutma!\n"
                           f"📢 `!yardım` ile komutları görebilirsin.",
                color=Config.COLOR_SUCCESS
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text="Marpel Bot")
            embed.timestamp = datetime.now()
            
            await welcome_channel.send(embed=embed)
        
        # Veritabanına ekle
        await self.db.create_user(
            member.id,
            member.name,
            member.discriminator
        )
    
    async def on_member_remove(self, member):
        """Üye ayrıldığında"""
        log_channel = self.get_channel(Config.LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="👋 Üye Ayrıldı",
                description=f"{member.mention} ({member.name}) sunucudan ayrıldı.",
                color=Config.COLOR_WARNING
            )
            embed.timestamp = datetime.now()
            await log_channel.send(embed=embed)
    
    async def close(self):
        """Bot kapanırken"""
        logger.info("🛑 Bot kapatılıyor...")
        await super().close()
