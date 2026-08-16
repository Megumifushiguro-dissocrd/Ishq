import discord
from discord.ext import commands
from discord import app_commands

TARGET_INFO_CHANNEL_ID = 1538526814857855017

# Master Role Configuration for Info Output
ROLES_CONFIG = [
    {"threshold": 100,   "role_id": 1538207193885835376},
    {"threshold": 200,   "role_id": 1538534818906767390},
    {"threshold": 300,   "role_id": 1538534949471387750},
    {"threshold": 500,   "role_id": 1538207196024799312},
    {"threshold": 750,   "role_id": 1538535031121772624},
    {"threshold": 1000,  "role_id": 1538207198054719579},
    {"threshold": 1500,  "role_id": 1538535128463048794},
    {"threshold": 2000,  "role_id": 1538535223179091979},
    {"threshold": 2500,  "role_id": 1538207199958925332},
    {"threshold": 3000,  "role_id": 1538535299083145336},
    {"threshold": 4000,  "role_id": 1538535391886315611},
    {"threshold": 5000,  "role_id": 1538207201766940715},
    {"threshold": 7500,  "role_id": 1538207204283256922},
    {"threshold": 10000, "role_id": 1538207207009685546},
    {"threshold": 12500, "role_id": 1538535490805039195},
    {"threshold": 15000, "role_id": 1538535925586468914},
    {"threshold": 18000, "role_id": 1538536040606732411},
    {"threshold": 21000, "role_id": 1538536252553306205},
    {"threshold": 25000, "role_id": 1538207209287188511}
]

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rules", description="Post the official server rules, info, & role progression embeds.")
    @commands.has_permissions(administrator=True)
    async def rules(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        channel = guild.get_channel(TARGET_INFO_CHANNEL_ID)

        if not channel:
            await interaction.followup.send(f"Error: Could not find channel with ID `{TARGET_INFO_CHANNEL_ID}`.", ephemeral=True)
            return

        arrow_emoji = "<:20839:1538526421595721748>"

        # Fetch the bot user profile to access bot.banner
        bot_user = await self.bot.fetch_user(self.bot.user.id)

        # ------------------ EMBED 1: SERVER RULES ------------------
        rules_embed = discord.Embed(
            title="📜 OFFICIAL SERVER RULES",
            description=(
                f"Welcome to **{guild.name}**! To ensure a safe, friendly, and enjoyable community for everyone, "
                f"please read and follow our community rules. Ignorance of the rules is not an excuse.\n"
            ),
            color=discord.Color.from_rgb(255, 105, 180)  # Aesthetic Pink
        )

        rules_list = [
            ("1. Respect Everyone", "Treat all members with kindness. No harassment, bullying, or hate speech."),
            ("2. No Toxicity", "Keep arguments and drama to a minimum. Resolve issues respectfully."),
            ("3. No Spam", "Avoid flooding chats, excessive mentions, or repeated messages."),
            ("4. Use the Correct Channels", f"Post content in its appropriate channel (e.g., chat in <#1538197351368491088>)."),
            ("5. Keep It Safe for Work (SFW)", "No NSFW, explicit, or inappropriate content."),
            ("6. No Discrimination", "Racism, sexism, homophobia, or any form of discrimination is not allowed."),
            ("7. No Advertising", "Don't promote other servers, social media, or products without staff permission."),
            ("8. Respect Privacy", "Never share personal or private information without consent."),
            ("9. No Impersonation", "Do not pretend to be another member, staff, or public figure."),
            ("10. Follow Discord's Terms of Service", "Breaking Discord's rules may result in removal from the server."),
            ("11. Listen to Staff", "Staff decisions are final. If you disagree, open a ticket instead of arguing in chat."),
            ("12. Have Fun & Be Friendly", "Help create a welcoming and positive community for everyone!")
        ]

        for title, desc in rules_list:
            rules_embed.add_field(name=title, value=f"{arrow_emoji} {desc}", inline=False)

        rules_embed.add_field(
            name="⚠️ Rule Violations",
            value="Depending on the severity, punishments may include a warning, mute, kick, or permanent ban.",
            inline=False
        )
        rules_embed.set_footer(text=f"Server: {guild.name} • Rules are subject to change by Staff", icon_url=guild.icon.url if guild.icon else None)

        # ------------------ EMBED 2: MESSAGE ROLES & PROGRESSION INFO ------------------
        roles_embed = discord.Embed(
            title="🏆 MESSAGE ROLES & PROGRESSION",
            description=(
                f"Earn unique roles simply by chatting in <#1538197351368491088>!\n"
                f"Below is the complete list of message milestone roles and requirements:\n"
            ),
            color=discord.Color.from_rgb(212, 175, 55)  # Gold Theme
        )

        half = (len(ROLES_CONFIG) + 1) // 2
        col1_text = ""
        for item in ROLES_CONFIG[:half]:
            col1_text += f"{arrow_emoji} <@&{item['role_id']}> • **{item['threshold']} msgs**\n"

        col2_text = ""
        for item in ROLES_CONFIG[half:]:
            col2_text += f"{arrow_emoji} <@&{item['role_id']}> • **{item['threshold']} msgs**\n"

        roles_embed.add_field(name="Tier 1 Milestones", value=col1_text, inline=True)
        roles_embed.add_field(name="Tier 2 Milestones", value=col2_text, inline=True)

        roles_embed.add_field(
            name="💡 Commands",
            value=(
                f"{arrow_emoji} Use `/rank` to generate your personal role progression card.\n"
                f"{arrow_emoji} Use `/ranklist` to view the interactive role list."
            ),
            inline=False
        )

        # ------------------ EMBED 3: SERVER INFORMATION & LINKS ------------------
        info_embed = discord.Embed(
            title="ℹ️ SERVER INFORMATION & LINKS",
            description=f"Everything you need to navigate **{guild.name}** smoothly!",
            color=discord.Color.from_rgb(147, 112, 219)  # Purple Accent
        )

        info_embed.add_field(
            name="📌 Important Channels",
            value=(
                f"{arrow_emoji} **General Chat:** <#1538197351368491088>\n"
                f"{arrow_emoji} **Commands & Rank Check:** <#1538197426937008270>\n"
                f"{arrow_emoji} **Rank Up Announcements:** <#1538539804050853954>\n"
                f"{arrow_emoji} **Information & Rules:** <#1538526814857855017>"
            ),
            inline=False
        )

        info_embed.set_footer(text=f"Enjoy your stay in {guild.name}! ✨", icon_url=guild.icon.url if guild.icon else None)

        # Set bot's official banner as the image if set on Discord Developer Portal
        if bot_user.banner:
            info_embed.set_image(url=bot_user.banner.url)

        await channel.send(embeds=[rules_embed, roles_embed, info_embed])

        await interaction.followup.send(f"Successfully sent rules, roles, & information embeds to {channel.mention}!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
      
