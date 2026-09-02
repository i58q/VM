import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='uyarı')
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "Belirtilmedi"):
        """Kullanıcıya uyarı ver"""
        await self.bot.db.add_warning(member.id, ctx.author.id, reason)
        warnings = await self.bot.db.get_warnings(member.id)
        
        embed = discord.Embed(
            title="⚠️ Uyarı Verildi",
            description=f"{member.mention} uyarıldı!",
            color=self.bot.config.COLOR_WARNING
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Uyarı Sayısı", value=len(warnings), inline=True)
        embed.add_field(name="Yetkili", value=ctx.author.mention, inline=True)
        embed.timestamp = datetime.now()
        
        await ctx.send(embed=embed)
        
        # Log
        log_channel = ctx.guild.get_channel(self.bot.config.LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="⚠️ Uyarı",
                description=f"{member.mention} uyarıldı",
                color=self.bot.config.COLOR_WARNING
            )
            log_embed.add_field(name="Sebep", value=reason)
            log_embed.add_field(name="Yetkili", value=ctx.author.mention)
            log_embed.timestamp = datetime.now()
            await log_channel.send(embed=log_embed)
        
        # 3 uyarı = mute
        if len(warnings) >= 3:
            await self.mute_user(ctx, member, "3 uyarı", 60)
            await ctx.send(f"🔇 {member.mention} 3 uyarı nedeniyle 1 saat susturuldu!")
    
    @commands.command(name='uyarılar')
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """Kullanıcının uyarılarını göster"""
        warnings = await self.bot.db.get_warnings(member.id)
        
        if not warnings:
            embed = discord.Embed(
                title="✅ Uyarı Yok",
                description=f"{member.mention} hiç uyarı almamış.",
                color=self.bot.config.COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"⚠️ {member.name} - Uyarılar",
            description=f"Toplam **{len(warnings)}** uyarı",
            color=self.bot.config.COLOR_WARNING
        )
        
        for i, warning in enumerate(warnings[:10], 1):
            embed.add_field(
                name=f"#{i}",
                value=f"**Sebep:** {warning['reason']}\n**Tarih:** {warning['date'][:19]}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='sustur')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: int, *, reason: str = "Belirtilmedi"):
        """Kullanıcıyı sustur"""
        await self.mute_user(ctx, member, reason, duration)
    
    async def mute_user(self, ctx, member: discord.Member, reason: str, duration: int):
        """Susturma işlemi"""
        mute_role = ctx.guild.get_role(self.bot.config.MUTE_ROLE_ID)
        if not mute_role:
            # Mute rolü yoksa oluştur
            mute_role = await ctx.guild.create_role(
                name="Susturuldu",
                permissions=discord.Permissions(send_messages=False, speak=False),
                color=discord.Color.dark_gray()
            )
            # Tüm kanallara mute rolü ekle
            for channel in ctx.guild.channels:
                await channel.set_permissions(mute_role, send_messages=False, speak=False)
            
            self.bot.config.MUTE_ROLE_ID = mute_role.id
        
        await member.add_roles(mute_role)
        await self.bot.db.add_mute(member.id, ctx.author.id, reason, duration)
        
        embed = discord.Embed(
            title="🔇 Kullanıcı Susturuldu",
            description=f"{member.mention} susturuldu!",
            color=self.bot.config.COLOR_WARNING
        )
        embed.add_field(name="Süre", value=f"{duration} dakika", inline=True)
        embed.add_field(name="Sebep", value=reason, inline=True)
        embed.add_field(name="Yetkili", value=ctx.author.mention, inline=True)
        embed.timestamp = datetime.now()
        
        await ctx.send(embed=embed)
        
        # Otomatik susturma kaldırma
        await asyncio.sleep(duration * 60)
        await member.remove_roles(mute_role)
    
    @commands.command(name='sustur_kaldır')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Susturmayı kaldır"""
        mute_role = ctx.guild.get_role(self.bot.config.MUTE_ROLE_ID)
        if mute_role and mute_role in member.roles:
            await member.remove_roles(mute_role)
            
            embed = discord.Embed(
                title="🔊 Susturma Kaldırıldı",
                description=f"{member.mention} susturması kaldırıldı.",
                color=self.bot.config.COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Hata",
                description=f"{member.mention} zaten susturulmamış.",
                color=self.bot.config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='ban')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "Belirtilmedi"):
        """Kullanıcıyı banla"""
        await ctx.guild.ban(member, reason=reason)
        
        embed = discord.Embed(
            title="🔨 Kullanıcı Banlandı",
            description=f"{member.mention} banlandı!",
            color=self.bot.config.COLOR_ERROR
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Yetkili", value=ctx.author.mention, inline=True)
        embed.timestamp = datetime.now()
        
        await ctx.send(embed=embed)
    
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Banı kaldır"""
        user = await ctx.guild.fetch_ban(user_id)
        if user:
            await ctx.guild.unban(user.user)
            
            embed = discord.Embed(
                title="✅ Ban Kaldırıldı",
                description=f"{user.user.mention} banı kaldırıldı.",
                color=self.bot.config.COLOR_SUCCESS
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Hata",
                description="Bu kullanıcı banlı değil.",
                color=self.bot.config.COLOR_ERROR
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='kick')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Belirtilmedi"):
        """Kullanıcıyı at"""
        await ctx.guild.kick(member, reason=reason)
        
        embed = discord.Embed(
            title="👢 Kullanıcı Atıldı",
            description=f"{member.mention} sunucudan atıldı!",
            color=self.bot.config.COLOR_WARNING
        )
        embed.add_field(name="Sebep", value=reason, inline=False)
        embed.add_field(name="Yetkili", value=ctx.author.mention, inline=True)
        embed.timestamp = datetime.now()
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
