import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Replace with your actual Welcome Channel ID
        self.welcome_channel_id = 1538197351368491088
        
        # Local file path or container storage path
        self.image_path = "/storage/emulated/0/Pictures/file_0000000076dc8208bd451dca2dd4a5b1.png"

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(self.welcome_channel_id)
        if not channel:
            return

        guild = member.guild
        member_count = guild.member_count
        emoji_arrow = "<:20839:1538526421595721748>"

        description_text = (
            f"Hey {member.mention}, welcome to **{guild.name}**!\n"
            f"We are glad to have you here. You are our **#{member_count}** member!\n\n"
            f"**__Quick Links & Channels__**\n"
            f"{emoji_arrow} checkout - <#1538526814857855017>\n"
            f"{emoji_arrow} Checkout - <#1538197351368491088>\n"
            f"{emoji_arrow} Checkout - <#1538197426937008270>"
        )

        # Advanced Embed Configuration
        embed = discord.Embed(
            title="Welcome to ishq™ !",
            description=description_text,
            color=discord.Color.from_rgb(255, 105, 180)
        )

        embed.set_author(
            name=f"{member.name} joined!",
            icon_url=member.display_avatar.url
        )

        # Attach image if file exists
        try:
            file = discord.File(self.image_path, filename="welcome_card.png")
            embed.set_image(url="attachment://welcome_card.png")
            
            embed.set_footer(
                text=f"Server: {guild.name}",
                icon_url=guild.icon.url if guild.icon else None
            )
            embed.timestamp = discord.utils.utcnow()

            await channel.send(embed=embed, file=file)
            
        except FileNotFoundError:
            # Fallback if image file path isn't found on host server
            embed.set_footer(
                text=f"Server: {guild.name} | Image Not Found",
                icon_url=guild.icon.url if guild.icon else None
            )
            embed.timestamp = discord.utils.utcnow()
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
  
