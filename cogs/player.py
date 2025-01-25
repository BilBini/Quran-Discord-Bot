import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from config import MP3_FOLDER
import os

class PlayerControls(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Allow only the user who started playback to control it
        return interaction.user == self.player.current_user

    @discord.ui.button(label="⏸️ Pause", style=discord.ButtonStyle.blurple, custom_id="pause_button")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.player.voice_client and self.player.voice_client.is_playing():
                self.player.voice_client.pause()
                button.label = "▶️ Resume"
                button.style = discord.ButtonStyle.green
                await interaction.response.edit_message(view=self)
            elif self.player.voice_client and self.player.voice_client.is_paused():
                self.player.voice_client.resume()
                button.label = "⏸️ Pause"
                button.style = discord.ButtonStyle.blurple
                await interaction.response.edit_message(view=self)
        except Exception as e:
            print(f"Error in pause_button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Failed to pause/resume playback", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.grey, custom_id="skip_button")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.player.voice_client:
                self.player.voice_client.stop()
                await interaction.response.defer()
        except Exception as e:
            print(f"Error in skip_button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Failed to skip track", ephemeral=True)

    @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.red, custom_id="stop_button")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if self.player.voice_client:
                await self.player.voice_client.disconnect()
                self.player.queue.clear()
                await interaction.response.edit_message(content="Playback stopped", view=None)
        except Exception as e:
            print(f"Error in stop_button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Failed to stop playback", ephemeral=True)

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}  # Track players by guild ID
        self.resume_channel_id = 1332106862098649181  # Add channel ID for resuming

    def get_player(self, guild_id):
        """Get or create a player instance for a guild"""
        if guild_id not in self.players:
            self.players[guild_id] = {
                'voice_client': None,
                'queue': [],
                'current': None,
                'current_user': None,
                'controls_message': None,
                'loop': False
            }
        return self.players[guild_id]

    def get_mp3_files(self):
        return sorted([f for f in os.listdir(MP3_FOLDER) if f.endswith('.mp3')])

    async def cleanup(self):
        """Properly clean up resources"""
        try:
            for player in self.players.values():
                if player['voice_client'] and player['voice_client'].is_connected():
                    await player['voice_client'].disconnect()
                player['queue'].clear()
                player['current'] = None
                player['current_user'] = None
                
                if player['controls_message']:
                    try:
                        await player['controls_message'].edit(view=None)
                    except:
                        pass
                    player['controls_message'] = None
        except Exception as e:
            print(f"Error during cleanup: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle when bot is force disconnected or owner leaves"""
        # Handle bot disconnection
        if member == self.bot.user and before.channel and not after.channel:
            await self.cleanup()
            return
            
        # Handle owner leaving
        guild_id = member.guild.id
        player = self.get_player(guild_id)
        
        if member == player['current_user'] and before.channel and not after.channel:
            # Store the current position
            if player['voice_client'] and player['voice_client'].is_playing():
                player['paused_position'] = player['voice_client'].source.tell()
                player['paused_file'] = player['current']
                player['voice_client'].pause()
            
            # Find new owner from current voice channel members
            if player['voice_client'] and player['voice_client'].channel:
                members = [m for m in player['voice_client'].channel.members if m != self.bot.user]
                
                if members:  # If there are other members
                    player['current_user'] = members[0]
                    embed = discord.Embed(
                        description=f"🎙️ Control transferred to {player['current_user'].display_name}",
                        color=0x00ff00
                    )
                    await player['voice_client'].channel.send(embed=embed)
                else:  # If no one is left
                    await player['voice_client'].disconnect()
                    # Don't cleanup so we can resume later

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle when a member joins the server"""
        guild_id = member.guild.id
        player = self.get_player(guild_id)
        
        # Check if this is the resume channel and no one is playing
        if member.voice and member.voice.channel and member.voice.channel.id == self.resume_channel_id:
            if player['voice_client'] and not player['voice_client'].is_connected():
                # Reconnect to the channel
                channel = self.bot.get_channel(self.resume_channel_id)
                player['voice_client'] = await channel.connect()
                
                # Resume playback if we have a paused position
                if 'paused_position' in player and 'paused_file' in player:
                    source = FFmpegPCMAudio(os.path.join(MP3_FOLDER, player['paused_file']))
                    player['voice_client'].play(source, after=lambda e: self.bot.loop.create_task(self.play_next(member)))
                    player['voice_client'].source.seek(player['paused_position'])
                    
                    # Transfer control to the new member
                    player['current_user'] = member
                    embed = discord.Embed(
                        description=f"🎙️ Playback resumed by {member.display_name}",
                        color=0x00ff00
                    )
                    await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        """Reset state when bot restarts"""
        await self.cleanup()
        print("Bot restarted - Player state cleared.")

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Handle errors and cleanup"""
        print(f"Error occurred in {event}: {args} {kwargs}")
        await self.cleanup()

    @commands.command(name='player_stop')
    async def stop_command(self, ctx):
        """Stop command handler"""
        await self.cleanup()
        await ctx.send("Playback stopped and bot disconnected.")

    async def play_command(self, ctx):
        """Handle play command for a specific guild"""
        try:
            player = self.get_player(ctx.guild.id)
            
            # Disconnect from any other channel in this guild
            if player['voice_client'] and player['voice_client'].channel != ctx.author.voice.channel:
                await player['voice_client'].move_to(ctx.author.voice.channel)
                
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
                
                if player['voice_client']:
                    if player['voice_client'].channel != channel:
                        await player['voice_client'].move_to(channel)
                else:
                    player['voice_client'] = await channel.connect()
                
                if not player['queue']:
                    player['queue'] = self.get_mp3_files()
                    player['loop'] = True
                
                # Send initial response
                embed = discord.Embed(
                    description="Starting Quran playback...",
                    color=0x5865F2
                )
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
                
                await self.play_next(ctx)
            else:
                if ctx.interaction:
                    await ctx.interaction.followup.send("You need to be in a voice channel to use this command.")
                else:
                    await ctx.send("You need to be in a voice channel to use this command.")
        except Exception as e:
            print(f"Error in play_command: {e}")
            if ctx.interaction:
                await ctx.interaction.followup.send("Failed to start playback. Please try again.")
            else:
                await ctx.send("Failed to start playback. Please try again.")

    async def play_next(self, ctx):
        try:
            player = self.get_player(ctx.guild.id)
            
            if not player['voice_client'] or not player['voice_client'].is_connected():
                return
                
            if not player['queue'] and player['loop']:
                player['queue'] = self.get_mp3_files()
                
            if player['queue']:
                player['current'] = player['queue'].pop(0)
                source = FFmpegPCMAudio(os.path.join(MP3_FOLDER, player['current']))
                player['current_user'] = ctx.author
                
                def after_playing(error):
                    if error:
                        print(f'Error: {error}')
                    if player['voice_client'] and player['voice_client'].is_connected():
                        self.bot.loop.create_task(self.play_next(ctx))
                        
                if not player['voice_client'].is_playing():
                    player['voice_client'].play(source, after=after_playing)
                
                # Create and send embed with controls
                embed = discord.Embed(
                    title="🎶 Now Playing",
                    description=f"**{player['current'][:-4]}**",
                    color=0x5865F2
                )
                embed.set_footer(text="Quran Bot - Peace be upon you")
                
                # Send message with controls and store reference
                view = PlayerControls(self)
                if player['controls_message']:
                    await player['controls_message'].edit(embed=embed, view=view)
                else:
                    player['controls_message'] = await ctx.send(embed=embed, view=view)
                
            elif player['voice_client'] and not player['voice_client'].is_playing():
                await self.cleanup()
        except Exception as e:
            print(f"Error in play_next: {e}")
            await self.cleanup()

async def setup(bot):
    # Only add the cog if it's not already loaded
    if 'Player' not in bot.cogs:
        await bot.add_cog(Player(bot)) 