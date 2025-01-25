import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from .player import Player
from config import MP3_FOLDER
import os

class QuranCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = Player(bot)
        self.controllers = {}  # Store user control permissions
        # Remove the default help command
        bot.remove_command('help')

    async def create_embed(self, title, description, color=0x00ff00):
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        embed.set_footer(text="Quran Bot - Peace be upon you")
        return embed

    async def verify_controller(self, ctx):
        if ctx.author.id not in self.controllers:
            embed = await self.create_embed(
                "⚠️ Permission Denied",
                "Only the user who started playback can control the player.",
                0xff0000
            )
            await ctx.send(embed=embed)
            return False
        return True

    @commands.hybrid_command(name="play", description="Start playing the Quran")
    async def play_command(self, ctx: commands.Context):
        """Play command that delegates to Player cog"""
        # Acknowledge the interaction immediately
        if ctx.interaction:
            await ctx.interaction.response.defer()
            
        player = self.bot.get_cog('Player')
        if player:
            await player.play_command(ctx)
        else:
            await ctx.send("Player cog not loaded. Please contact the bot administrator.")

    @commands.hybrid_command(name="pause", description="Pause the playback")
    async def pause_command(self, ctx: commands.Context):
        if not await self.verify_controller(ctx):
            return
            
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = await self.create_embed(
                "⏸️ Playback Paused",
                "Use `/resume` to continue playing.",
                0xffff00
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="resume", description="Resume the playback")
    async def resume_command(self, ctx: commands.Context):
        if not await self.verify_controller(ctx):
            return
            
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = await self.create_embed(
                "▶️ Playback Resumed",
                "Now continuing the Quran recitation.",
                0x00ff00
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="stop", description="Stop the playback")
    async def stop_command(self, ctx: commands.Context):
        # Check if user is the current owner
        player = self.bot.get_cog('Player')
        if player and player.current_user and ctx.author.id != player.current_user.id:
            embed = await self.create_embed(
                "⚠️ Permission Denied",
                "Only the current session owner can stop playback.",
                0xff0000
            )
            await ctx.send(embed=embed)
            return
            
        if ctx.voice_client:
            await player.cleanup()
            embed = await self.create_embed(
                "⏹️ Playback Stopped",
                "The Quran player has been stopped.",
                0xff0000
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="skip", description="Skip to next Surah")
    async def skip_command(self, ctx: commands.Context):
        if not await self.verify_controller(ctx):
            return
            
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = await self.create_embed(
                "⏭️ Surah Skipped",
                "Moving to the next Surah...",
                0x00ff00
            )
            await ctx.send(embed=embed)
            await self.player.play_next(ctx)

    @commands.hybrid_command(name="help", description="Show help information")
    async def help_command(self, ctx: commands.Context):
        embed = await self.create_embed(
            "🕌 Quran Bot Help",
            "**Commands:**\n"
            "`/play` - Start playing the Quran\n"
            "`/pause` - Pause playback\n"
            "`/resume` - Resume playback\n"
            "`/stop` - Stop playback\n"
            "`/skip` - Skip to next Surah\n"
            "`/help` - Show this help message\n\n"
            "Only the user who started playback can control it.",
            0x00aaff
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(QuranCommands(bot)) 