import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='temizle')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 10):
        """Mesajları temizle (1-100)"""
        if amount < 1 or amount > 100:
            embed = discord.Embed(
                title="❌ Hata",
                description="Lütfen 1-100 arası bir sayı gir!",
                color=self.bot.config.COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        embed = discord.Embed(
            title="✅ Mesajlar Temizlendi",
            description=f"**{len(deleted) - 1}** mesaj silindi.",
            color=self.bot.config.COLOR_SUCCESS
        )
        msg = await ctx.send(embed=embed)
        await msg.delete(delay=5)
    
    @commands.command(name='duyuru')
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx, *, message: str):
        """Duyuru gönder"""
        embed = discord.Embed(
            title="📢 DUYURU",
            description=message,
            color=self.bot.config.COLOR_INFO
        )
        embed.set_footer(text=f"{ctx.guild.name} • {datetime.now().strftime('%d.%m.%Y')}")
        embed.timestamp = datetime.now()
        
        await ctx.send("@everyone", embed=embed)
        await ctx.message.delete()
    
    @commands.command(name='bot_durum')
    @commands.has_permissions(administrator=True)
    async def set_status(self, ctx, status_type: str, *, status_text: str):
        """Bot durumunu değiştir"""
        status_map = {
            'oynuyor': discord.ActivityType.playing,
            'izliyor': discord.ActivityType.watching,
            'dinliyor': discord.ActivityType.listening,
            'yayında': discord.ActivityType.streaming,
            'yarışıyor': discord.ActivityType.competing
        }
        
        activity_type = status_map.get(status_type.lower())
        if not activity_type:
            embed = discord.Embed(
                title="❌ Hata",
                description="Geçersiz durum tipi!\nKullanım: `!bot_durum [oynuyor/izliyor/dinliyor/yayında] [metin]`",
                color=self.bot.config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        await self.bot.change_presence(
            activity=discord.Activity(
                type=activity_type,
                name=status_text
            )
        )
        
        embed = discord.Embed(
            title="✅ Durum Güncellendi",
            description=f"Bot durumu **{status_type} {status_text}** olarak değiştirildi.",
            color=self.bot.config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='bot_sunucu_list')
    @commands.is_owner()
    async def server_list(self, ctx):
        """Botun bulunduğu sunucuları listele"""
        embed = discord.Embed(
            title="📊 Bot Sunucu Listesi",
            color=self.bot.config.COLOR_INFO
        )
        
        for guild in self.bot.guilds:
            embed.add_field(
                name=guild.name,
                value=f"ID: {guild.id}\nÜye: {guild.member_count}",
                inline=False
            )
        
        embed.set_footer(text=f"Toplam {len(self.bot.guilds)} sunucu")
        await ctx.send(embed=embed)
    
    @commands.command(name='backup')
    @commands.is_owner()
    async def backup_db(self, ctx):
        """Veritabanını yedekle"""
        import shutil
        from datetime import datetime
        
        backup_path = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(self.bot.config.DB_PATH, backup_path)
        
        embed = discord.Embed(
            title="✅ Veritabanı Yedeklendi",
            description=f"Yedek dosyası: `{backup_path}`",
            color=self.bot.config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)
        
        # Dosyayı gönder
        await ctx.send(file=discord.File(backup_path))
    
    @commands.command(name='bot_kapat')
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Botu kapat"""
        embed = discord.Embed(
            title="🛑 Bot Kapatılıyor",
            description="Bot güvenli bir şekilde kapatılıyor...",
            color=self.bot.config.COLOR_WARNING
        )
        await ctx.send(embed=embed)
        
        logger.info("Bot kapatılıyor... (Owner komutu)")
        await self.bot.close()
    
    # Slash Komutları
    @app_commands.command(name="clear", description="Mesajları temizle")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer()
        
        if amount < 1 or amount > 100:
            embed = discord.Embed(
                title="❌ Hata",
                description="Lütfen 1-100 arası bir sayı gir!",
                color=self.bot.config.COLOR_ERROR
            )
            await interaction.followup.send(embed=embed)
            return
        
        deleted = await interaction.channel.purge(limit=amount)
        
        embed = discord.Embed(
            title="✅ Mesajlar Temizlendi",
            description=f"**{len(deleted)}** mesaj silindi.",
            color=self.bot.config.COLOR_SUCCESS
        )
        await interaction.followup.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="announce", description="Duyuru gönder")
    @app_commands.default_permissions(administrator=True)
    async def slash_announce(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="📢 DUYURU",
            description=message,
            color=self.bot.config.COLOR_INFO
        )
        embed.set_footer(text=f"{interaction.guild.name} • {datetime.now().strftime('%d.%m.%Y')}")
        embed.timestamp = datetime.now()
        
        await interaction.channel.send("@everyone", embed=embed)
        await interaction.followup.send("✅ Duyuru gönderildi!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
