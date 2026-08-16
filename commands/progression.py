import io
import time
import aiosqlite
import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont

# -------------------------------------------------------------------
# CONFIGURATION SETTINGS
# -------------------------------------------------------------------
DATABASE_PATH = "progression_data.db"
COUNT_CHANNEL_ID = 1538197351368491088      # Tracking channel
ANNOUNCE_CHANNEL_ID = 1538539804050853954   # Announcement channel

# Master Role Progression List (19 Roles)
ROLES_CONFIG = [
    {"threshold": 100,   "role_id": 1538207193885835376, "name": "100 msgs"},
    {"threshold": 200,   "role_id": 1538534818906767390, "name": "200 msgs"},
    {"threshold": 300,   "role_id": 1538534949471387750, "name": "300 msgs"},
    {"threshold": 500,   "role_id": 1538207196024799312, "name": "500 msgs"},
    {"threshold": 750,   "role_id": 1538535031121772624, "name": "750 msgs"},
    {"threshold": 1000,  "role_id": 1538207198054719579, "name": "1k msgs"},
    {"threshold": 1500,  "role_id": 1538535128463048794, "name": "1.5k msgs"},
    {"threshold": 2000,  "role_id": 1538535223179091979, "name": "2k msgs"},
    {"threshold": 2500,  "role_id": 1538207199958925332, "name": "2.5k msgs"},
    {"threshold": 3000,  "role_id": 1538535299083145336, "name": "3k msgs"},
    {"threshold": 4000,  "role_id": 1538535391886315611, "name": "4k msgs"},
    {"threshold": 5000,  "role_id": 1538207201766940715, "name": "5k msgs"},
    {"threshold": 7500,  "role_id": 1538207204283256922, "name": "7.5k msgs"},
    {"threshold": 10000, "role_id": 1538207207009685546, "name": "10k msgs"},
    {"threshold": 12500, "role_id": 1538535490805039195, "name": "12.5k msgs"},
    {"threshold": 15000, "role_id": 1538535925586468914, "name": "15k msgs"},
    {"threshold": 18000, "role_id": 1538536040606732411, "name": "18k msgs"},
    {"threshold": 21000, "role_id": 1538536252553306205, "name": "21k msgs"},
    {"threshold": 25000, "role_id": 1538207209287188511, "name": "25k msgs"}
]


# -------------------------------------------------------------------
# INTERACTIVE PAGINATION VIEW FOR /RANKLIST
# -------------------------------------------------------------------
class RanklistPaginationView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.page = 0
        self.per_page = 10
        self.total_pages = (len(ROLES_CONFIG) + self.per_page - 1) // self.per_page

    def get_embed(self) -> discord.Embed:
        start = self.page * self.per_page
        end = start + self.per_page
        current_chunk = ROLES_CONFIG[start:end]

        embed = discord.Embed(
            title="📜 MESSAGE ROLE PROGRESSION LIST",
            description="Official milestone roles and message requirements:",
            color=discord.Color.from_rgb(212, 175, 55)
        )

        value_text = ""
        for config in current_chunk:
            value_text += f"<@&{config['role_id']}> • **{config['threshold']} messages**\n"

        embed.add_field(name=f"Page {self.page + 1}/{self.total_pages}", value=value_text, inline=False)
        embed.set_footer(
            text=f"Server: {self.interaction.guild.name}",
            icon_url=self.interaction.guild.icon.url if self.interaction.guild.icon else None
        )
        return embed

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message("You cannot use this button.", ephemeral=True)
        
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message("You cannot use this button.", ephemeral=True)

        if self.page < self.total_pages - 1:
            self.page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)


# -------------------------------------------------------------------
# MAIN COG CLASS
# -------------------------------------------------------------------
class MessageRoleProgression(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = None

    async def cog_load(self):
        """Initializes SQLite Database."""
        self.db = await aiosqlite.connect(DATABASE_PATH)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS message_counts (
                guild_id INTEGER,
                user_id INTEGER,
                messages INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        await self.db.commit()

    async def cog_unload(self):
        if self.db:
            await self.db.close()

    # -------------------------------------------------------------------
    # DATABASE & PROGRESSION HELPERS
    # -------------------------------------------------------------------
    async def get_user_messages(self, guild_id: int, user_id: int) -> int:
        async with self.db.execute(
            "SELECT messages FROM message_counts WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def increment_user_messages(self, guild_id: int, user_id: int) -> int:
        async with self.db.execute(
            """
            INSERT INTO message_counts (guild_id, user_id, messages) 
            VALUES (?, ?, 1)
            ON CONFLICT(guild_id, user_id) 
            DO UPDATE SET messages = messages + 1
            RETURNING messages;
            """,
            (guild_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            await self.db.commit()
            return row[0]

    def calculate_role_progression(self, total_msgs: int):
        current_role = None
        next_role = ROLES_CONFIG[0]

        for i, config in enumerate(ROLES_CONFIG):
            if total_msgs >= config["threshold"]:
                current_role = config
                if i + 1 < len(ROLES_CONFIG):
                    next_role = ROLES_CONFIG[i + 1]
                else:
                    next_role = None
            else:
                if current_role is None:
                    next_role = config
                break

        if next_role:
            prev_thresh = current_role["threshold"] if current_role else 0
            needed = next_role["threshold"] - prev_thresh
            gained = total_msgs - prev_thresh
            percentage = min(100.0, max(0.0, (gained / needed) * 100.0))
        else:
            percentage = 100.0

        return current_role, next_role, percentage

    # -------------------------------------------------------------------
    # LUXURY GRAPHICS GENERATOR
    # -------------------------------------------------------------------
    async def create_rank_card(
        self, member: discord.Member, total_msgs: int, 
        current_role: dict, next_role: dict, percentage: float
    ) -> io.BytesIO:
        width, height = 950, 330
        base = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        # 1. Dark Luxury Gradient
        bg = Image.new("RGBA", (width, height))
        draw_bg = ImageDraw.Draw(bg)
        for y in range(height):
            r = int(16 + (y / height) * 14)
            g = int(12 + (y / height) * 8)
            b = int(24 + (y / height) * 18)
            draw_bg.line([(0, y), (width, y)], fill=(r, g, b, 255))
        base.paste(bg)

        draw = ImageDraw.Draw(base)

        # 2. Double Golden Frame Lines
        draw.rounded_rectangle([(15, 15), (width - 15, height - 15)], radius=16, outline=(212, 175, 55, 220), width=2)
        draw.rounded_rectangle([(20, 20), (width - 20, height - 20)], radius=12, outline=(255, 215, 0, 60), width=1)

        # 3. Avatar Processing
        avatar_bytes = await member.display_avatar.with_format("png").read()
        avatar_raw = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((160, 160))

        mask = Image.new("L", (160, 160), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 160, 160), fill=255)

        avatar_x, avatar_y = 45, 85
        base.paste(avatar_raw, (avatar_x, avatar_y), mask)
        draw.ellipse([(avatar_x - 5, avatar_y - 5), (avatar_x + 165, avatar_y + 165)], outline=(212, 175, 55), width=3)

        # 4. Text Headers
        font = ImageFont.load_default()
        draw.text((230, 45), f"{member.display_name.upper()}", fill=(255, 255, 255), font=font)
        draw.text((230, 75), "ROLE PROGRESSION", fill=(212, 175, 55), font=font)

        # 5. Progress Bar
        bar_x, bar_y, bar_w, bar_h = 230, 125, 660, 32
        draw.rounded_rectangle([(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)], radius=16, fill=(30, 30, 45, 255), outline=(70, 70, 90))

        fill_width = int((percentage / 100.0) * bar_w)
        if fill_width > 15:
            draw.rounded_rectangle([(bar_x, bar_y), (bar_x + fill_width, bar_y + bar_h)], radius=16, fill=(212, 175, 55))

        draw.text((bar_x + (bar_w // 2) - 20, bar_y + 8), f"{percentage:.1f}%", fill=(255, 255, 255), font=font)

        # 6. Stats Lines
        curr_name = current_role["name"] if current_role else "None"
        next_name = next_role["name"] if next_role else "Max Role"
        next_req = f"{next_role['threshold']} msgs" if next_role else "N/A"

        draw.text((230, 180), f"Did Message • Total Message: {total_msgs}", fill=(220, 220, 220), font=font)
        draw.text((230, 210), f"Current Role: {curr_name}", fill=(180, 180, 255), font=font)
        draw.text((230, 240), f"Next Role: {next_name} ({next_req})", fill=(212, 175, 55), font=font)
        draw.text((700, 270), f"Server: {member.guild.name}", fill=(120, 120, 140), font=font)

        buffer = io.BytesIO()
        base.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    async def create_congrats_card(self, member: discord.Member, new_role_name: str) -> io.BytesIO:
        width, height = 800, 260
        base = Image.new("RGBA", (width, height), (15, 10, 25, 255))
        draw = ImageDraw.Draw(base)

        draw.rounded_rectangle([(10, 10), (width - 10, height - 10)], radius=20, outline=(255, 105, 180), width=3)

        avatar_bytes = await member.display_avatar.with_format("png").read()
        avatar_raw = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((130, 130))

        mask = Image.new("L", (130, 130), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 130, 130), fill=255)
        base.paste(avatar_raw, (40, 65), mask)

        draw.ellipse([(35, 60), (175, 200)], outline=(255, 215, 0), width=2)

        font = ImageFont.load_default()
        draw.text((200, 45), f"CONGRATULATIONS {member.display_name.upper()}!", fill=(255, 215, 0), font=font)
        draw.text((200, 90), f"You earned @{new_role_name}", fill=(255, 105, 180), font=font)
        draw.text((200, 150), f"Keep chatting in {member.guild.name}!", fill=(170, 170, 190), font=font)

        buffer = io.BytesIO()
        base.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # -------------------------------------------------------------------
    # MESSAGE EVENT LISTENERS
    # -------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if message.channel.id != COUNT_CHANNEL_ID:
            return

        new_total = await self.increment_user_messages(message.guild.id, message.author.id)

        # Check if threshold hit
        for index, config in enumerate(ROLES_CONFIG):
            if new_total == config["threshold"]:
                guild = message.guild
                member = message.author
                new_role = guild.get_role(config["role_id"])

                if not new_role:
                    continue

                # Strip old progression role
                prev_role = None
                if index > 0:
                    prev_config = ROLES_CONFIG[index - 1]
                    prev_role = guild.get_role(prev_config["role_id"])
                    if prev_role and prev_role in member.roles:
                        try:
                            await member.remove_roles(prev_role)
                        except discord.Forbidden:
                            pass

                # Assign new progression role
                try:
                    await member.add_roles(new_role)
                except discord.Forbidden:
                    pass

                # Post rank up card to channel 1538539804050853954
                announce_chan = guild.get_channel(ANNOUNCE_CHANNEL_ID)
                if announce_chan:
                    card_file = await self.create_congrats_card(member, config["name"])
                    file = discord.File(card_file, filename="rankup.png")

                    prev_mention = prev_role.mention if prev_role else "None"

                    embed = discord.Embed(
                        title="🎉 MESSAGE RANK UP!",
                        description=(
                            f"{member.mention} got ranked up from {prev_mention} to {new_role.mention}\n\n"
                            f"**More details:**\n"
                            f"• **Previous Role:** {prev_mention}\n"
                            f"• **Now New Role:** {new_role.mention}"
                        ),
                        color=discord.Color.from_rgb(255, 105, 180)
                    )
                    embed.set_image(url="attachment://rankup.png")
                    embed.set_footer(text=f"Server: {guild.name}", icon_url=guild.icon.url if guild.icon else None)

                    await announce_chan.send(content=f"{member.mention}", embed=embed, file=file)

    # -------------------------------------------------------------------
    # SLASH COMMANDS
    # -------------------------------------------------------------------
    @app_commands.command(name="rank", description="Check your message role progression.")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        target = member or interaction.user

        total_msgs = await self.get_user_messages(interaction.guild.id, target.id)
        current_role, next_role, percentage = self.calculate_role_progression(total_msgs)

        card_buffer = await self.create_rank_card(target, total_msgs, current_role, next_role, percentage)
        file = discord.File(card_buffer, filename="rank_card.png")
        await interaction.followup.send(file=file)

    @app_commands.command(name="ranklist", description="List all message milestone roles.")
    async def ranklist(self, interaction: discord.Interaction):
        view = RanklistPaginationView(interaction)
        await interaction.response.send_message(embed=view.get_embed(), view=view)


async def setup(bot):
    await bot.add_cog(MessageRoleProgression(bot))
      
