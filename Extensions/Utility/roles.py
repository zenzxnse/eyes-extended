import discord, asyncio
from discord.ext import commands
from discord import app_commands
import aiosqlite
from typing import Union


async def setup_db():
    async with aiosqlite.connect("db/roles.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS role_menus (
                guild_id INTEGER,
                menu_name TEXT,
                menu_description TEXT,
                placeholder TEXT DEFAULT 'Choose a role...',
                max_values INTEGER DEFAULT 0,
                min_values INTEGER DEFAULT 0,
                max_configured INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, menu_name)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS menu_roles (
                guild_id INTEGER,
                menu_name TEXT,
                role_id INTEGER,
                emoji TEXT,
                role_description TEXT,
                PRIMARY KEY (guild_id, menu_name, role_id),
                FOREIGN KEY (guild_id, menu_name) REFERENCES role_menus (guild_id, menu_name)
            )
        """)
        try:
            await db.execute("ALTER TABLE role_menus ADD COLUMN max_configured INTEGER DEFAULT 0")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" in str(e):
                pass  # Column already exists, ignore the error
            else:
                raise
        
        # Set max_configured to 1 for all rows
        await db.execute("UPDATE role_menus SET max_configured = 1")
        await db.commit()

async def add_roles_to_db(guild_id: int, menu_name: str, role_id: int, emoji: str = None, description: str = None):
    async with aiosqlite.connect("db/roles.db") as db:
        # Ensure the role menu exists for the specific guild
        await db.execute("INSERT OR IGNORE INTO role_menus (guild_id, menu_name) VALUES (?, ?)", (guild_id, menu_name))
        # Update or insert the role into the menu with emoji and description
        await db.execute("""
            INSERT INTO menu_roles (guild_id, menu_name, role_id, emoji, role_description)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, menu_name, role_id) DO UPDATE SET
            emoji = excluded.emoji,
            role_description = excluded.role_description
        """, (guild_id, menu_name, role_id, emoji, description))
        await db.commit()


class RoleMenuDropdown(discord.ui.Select):
    def __init__(self, roles, placeholder, min_values, max_values):
        options = []
        for role in roles:
            emoji = role[1]
            if emoji and emoji.startswith('<:'):
                emoji = discord.PartialEmoji.from_str(emoji)
            option = discord.SelectOption(label=role[0].name, description=role[2], value=str(role[0].id), emoji=emoji)
            options.append(option)
        super().__init__(placeholder=placeholder, min_values=min_values, max_values=max_values, options=options)
        self.previously_selected_roles = set()  # Keep track of previously selected roles

    async def callback(self, interaction: discord.Interaction):
        selected_role_ids = {int(value) for value in self.values}
        current_role_ids = {role.id for role in interaction.user.roles}

        roles_to_add = selected_role_ids - current_role_ids
        roles_to_remove = self.previously_selected_roles - selected_role_ids  # Only remove roles that were deselected

        roles_added_names = []
        roles_removed_names = []

        for role_id in roles_to_add:
            if role_id == interaction.guild.default_role.id:  # Skip the @everyone role
                continue
            role = interaction.guild.get_role(role_id)
            if role:
                try:
                    await interaction.user.add_roles(role)
                    roles_added_names.append(role.name)
                except discord.NotFound:
                    if interaction.response.is_done():
                        await interaction.followup.send(f"The role {role.name} could not be found.", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"The role {role.name} could not be found.", ephemeral=True)
                except discord.Forbidden:
                    if interaction.response.is_done():
                        await interaction.followup.send("I do not have permission to add roles.", ephemeral=True)
                    else:
                        await interaction.response.send_message("I do not have permission to add roles.", ephemeral=True)

        for role_id in roles_to_remove:
            if role_id == interaction.guild.default_role.id:  # Skip the @everyone role
                continue
            role = interaction.guild.get_role(role_id)
            if role:
                try:
                    await interaction.user.remove_roles(role)
                    roles_removed_names.append(role.name)
                except discord.NotFound:
                    if interaction.response.is_done():
                        await interaction.followup.send(f"The role {role.name} could not be found.", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"The role {role.name} could not be found.", ephemeral=True)
                except discord.Forbidden:
                    if interaction.response.is_done():
                        await interaction.followup.send("I do not have permission to remove roles.", ephemeral=True)
                    else:
                        await interaction.response.send_message("I do not have permission to remove roles.", ephemeral=True)

        self.previously_selected_roles = selected_role_ids  # Update previously selected roles

        messages = []
        if roles_added_names:
            messages.append(f"Roles added: {', '.join(roles_added_names)}")
        if roles_removed_names:
            messages.append(f"Roles removed: {', '.join(roles_removed_names)}")

        if messages:
            if interaction.response.is_done():
                await interaction.followup.send("\n".join(messages), ephemeral=True)
            else:
                await interaction.response.send_message("\n".join(messages), ephemeral=True)
        else:
            if interaction.response.is_done():
                await interaction.followup.send("No changes to your roles were made.", ephemeral=True)
            else:
                await interaction.response.send_message("No changes to your roles were made.", ephemeral=True)


class RoleMenuView(discord.ui.View):
    def __init__(self, roles, placeholder, min_values, max_values, interaction_user):
        super().__init__()
        self.add_item(RoleMenuDropdown(roles, placeholder, min_values, max_values))
        self.interaction_user = interaction_user

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.interaction_user

class RoleCreationView(discord.ui.View):
    def __init__(self, menu_name, interaction_user):
        super().__init__(timeout=600)
        self.menu_name = menu_name
        self.role = None
        self.description = None
        self.emoji = None
        self.is_new_role = False
        self.interaction_user = interaction_user
        self.processing = False

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.interaction_user

    @discord.ui.button(label="Update Role Menu", style=discord.ButtonStyle.success)
    async def update_the_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.processing:
            await interaction.response.send_message("A role is already being added to this menu. Please finish that process first.", ephemeral=True)
            return

        self.processing = True
        await interaction.response.send_message("Please mention the role you want to update in the menu.")
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        
        try:
            role_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            self.role = role_message.role_mentions[0] if role_message.role_mentions else None
            
            if not self.role:
                await interaction.followup.send("No valid role was mentioned. Please try again.")
                self.processing = False
                return
            
            # Check if the role already exists in the role menu
            async with aiosqlite.connect("db/roles.db") as db:
                async with db.execute("SELECT 1 FROM menu_roles WHERE guild_id = ? AND menu_name = ? AND role_id = ?", (interaction.guild.id, self.menu_name, self.role.id)) as cursor:
                    role_exists = await cursor.fetchone()
            
            if role_exists:
                await interaction.followup.send(f"The role {self.role.mention} already exists in the {self.menu_name} menu. Would you like to edit it? (yes/no)")
                edit_message = await self.bot.wait_for('message', check=check, timeout=60.0)
                if edit_message.content.lower() != 'yes':
                    await interaction.followup.send("Role update cancelled.")
                    self.processing = False
                    return
                self.is_new_role = False
            else:
                self.is_new_role = True
            
            await interaction.followup.send("Please provide a description for the role (max 100 characters):")
            description_message = await self.bot.wait_for('message', check=check, timeout=60.0)
            self.description = description_message.content[:100]
            
            emoji_message = await interaction.followup.send("If you would like this role to have an emoji in the role menu, please react to this message with the desired emoji. If you don't want an emoji, react with ❌.")
            await emoji_message.add_reaction('❌')
            
            def emoji_check(reaction, user):
                return user == interaction.user and reaction.message == emoji_message
            
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', check=emoji_check, timeout=60.0)
                if str(reaction.emoji) == '❌':
                    self.emoji = None
                else:
                    self.emoji = str(reaction.emoji)
            except asyncio.TimeoutError:
                self.emoji = None
            
            if self.emoji:
                await interaction.followup.send(f"Role {self.role.name} will be updated in the {self.menu_name} menu with description: {self.description} and emoji: {self.emoji}")
            else:
                await interaction.followup.send(f"Role {self.role.name} will be updated in the {self.menu_name} menu with description: {self.description} and no emoji.")
            
            async with aiosqlite.connect("db/roles.db") as db:
                await add_roles_to_db(interaction.guild.id, self.menu_name, self.role.id, self.emoji, self.description)
                
                if self.is_new_role:
                    # Check if max_configured is set to 1 (max values set to "max")
                    async with db.execute("SELECT max_configured FROM role_menus WHERE guild_id = ? AND menu_name = ?", (interaction.guild.id, self.menu_name)) as cursor:
                        max_configured = await cursor.fetchone()
                        if max_configured and max_configured[0] == 1:
                            # If max_configured is 1, increment the max value by 1
                            await db.execute("UPDATE role_menus SET max_values = max_values + 1 WHERE guild_id = ? AND menu_name = ?", (interaction.guild.id, self.menu_name))
                            await db.commit()
            
            await role_message.delete()
            await description_message.delete()
            await emoji_message.delete()
            
            self.processing = False
            
        except asyncio.TimeoutError:
            await interaction.followup.send("The role update process has timed out. Please try again.")
            self.processing = False

class Roles(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    create = app_commands.Group(name="create", description="Create a new role menu")
    async def fetch_roles_from_db(self, interaction: discord.Interaction, menu_name: str):
        async with aiosqlite.connect("db/roles.db") as db:
            async with db.execute("SELECT role_id, emoji, role_description FROM menu_roles WHERE menu_name = ?", (menu_name,)) as cursor:
                rows = await cursor.fetchall()
                roles = [(interaction.guild.get_role(int(row[0])), row[1], row[2]) for row in rows if interaction.guild.get_role(int(row[0]))]
            async with db.execute("SELECT placeholder, max_values, min_values FROM role_menus WHERE menu_name = ?", (menu_name,)) as cursor:
                menu_settings = await cursor.fetchone()
                settings = {
                    'placeholder': menu_settings[0],
                    'max_values': menu_settings[1],
                    'min_values': menu_settings[2]
                }
        return roles, settings
    
    async def check_role_menu_exists(self, guild_id: int, role_menu_name: str) -> bool:
        async with aiosqlite.connect("db/roles.db") as db:
            async with db.execute("SELECT 1 FROM role_menus WHERE guild_id = ? AND menu_name = ?", (guild_id, role_menu_name)) as cursor:
                return await cursor.fetchone() is not None
            
    async def autocomplete_menuname(self, interaction: discord.Interaction, current: str):
        guild_id = interaction.guild.id
        async with aiosqlite.connect("db/roles.db") as db:
            async with db.execute("SELECT menu_name FROM role_menus WHERE guild_id = ? AND menu_name LIKE ?", (guild_id, '%' + current + '%',)) as cursor:
                menus = await cursor.fetchall()
        return [app_commands.Choice(name=menu[0], value=menu[0]) for menu in menus]
    
    @app_commands.command(name="roles")
    @app_commands.describe(menuname="Name of the menu to display")
    @app_commands.autocomplete(menuname=autocomplete_menuname)
    async def roles(self, interaction: discord.Interaction, menuname: str):
        roles, settings = await self.fetch_roles_from_db(interaction, menuname)
        max_values = settings['max_values']
        
        if max_values <= 0:
            # If max_values is 0 or negative, set it to the number of roles in the menu
            max_values = len(roles)
            async with aiosqlite.connect("db/roles.db") as db:
                await db.execute("UPDATE role_menus SET max_values = ? WHERE guild_id = ? AND menu_name = ?", (max_values, interaction.guild.id, menuname))
                await db.commit()
        
        if roles:
            view = RoleMenuView(roles, settings['placeholder'], settings['min_values'], max_values, interaction.user)
            await interaction.response.send_message(f"Select a role from the {menuname} menu:", view=view, ephemeral=True)
        else:
            await interaction.response.send_message("No roles found for this menu.", ephemeral=True)

    @create.command(name="rolemenu")
    @app_commands.describe(menuname="Name of the menu to create", placeholder="Optional placeholder text for the dropdown", max_values="Maximum number of selectable roles or 'max' for all roles", min_values="Minimum number of selectable roles")
    @app_commands.rename(placeholder="placeholder", max_values="max_values", min_values="min_values")
    async def create_rolemenu(self, interaction: discord.Interaction, menuname: str, placeholder: str = "Choose a role...", max_values: str = "1", min_values: int = 0):
        guild_id = interaction.guild.id
        async with aiosqlite.connect("db/roles.db") as db:
            # Check if the menu name already exists in this guild
            cursor = await db.execute("SELECT 1 FROM role_menus WHERE guild_id = ? AND menu_name = ?", (guild_id, menuname))
            exists = await cursor.fetchone()
            if exists:
                await interaction.response.send_message(f"A role menu with the name '{menuname}' already exists in this guild. Please choose a different name.", ephemeral=True)
                return

            max_configured = 0
            if max_values.lower() == "max":
                # Count all roles for this menu in the guild
                cursor = await db.execute("SELECT COUNT(*) FROM menu_roles WHERE guild_id = ? AND menu_name = ?", (guild_id, menuname))
                count = await cursor.fetchone()
                max_values = count[0] if count else 0  # Set to the count of roles or 0 if none
                max_configured = 1
            else:
                try:
                    max_values = max(1, int(max_values))
                except ValueError:
                    await interaction.response.send_message("Invalid input for max_values. Please enter a positive integer or 'max'.", ephemeral=True)
                    return

            min_values = max(0, min(min_values, max_values))

            await db.execute("INSERT INTO role_menus (guild_id, menu_name, placeholder, max_values, min_values, max_configured) VALUES (?, ?, ?, ?, ?, ?)", (guild_id, menuname, placeholder, max_values, min_values, max_configured))
            await db.commit()
        await interaction.response.send_message(f"Role menu '{menuname}' created successfully for this guild with placeholder '{placeholder}', max selectable roles: {max_values}, min selectable roles: {min_values}.", ephemeral=True)
    
    update = app_commands.Group(name="update", description="Update an existing role menu")
    
    @update.command(name="rolemenu")
    @app_commands.autocomplete(menuname=autocomplete_menuname)
    async def update_rolemenu(self, interaction: discord.Interaction, menuname: str):
        guild_id = interaction.guild.id
        menu_exists = await self.check_role_menu_exists(guild_id, menuname)
        if menu_exists:
            view = RoleCreationView(menuname, interaction.user)
            view.bot = self.bot  # Assign the bot instance to the view
            await interaction.response.send_message(f"Click the button below to update a role in the {menuname} menu.", view=view)
        else:
            await interaction.response.send_message(f"The role menu '{menuname}' does not exist in this guild.", ephemeral=True)
    remove = app_commands.Group(name="remove", description="Remove an existing role menu")

    @remove.command(name="rolemenu")
    @app_commands.describe(menuname="Name of the menu to delete")
    @app_commands.autocomplete(menuname=autocomplete_menuname)
    async def delete_rolemenu(self, interaction: discord.Interaction, menuname: str):
        guild_id = interaction.guild.id
        menu_exists = await self.check_role_menu_exists(guild_id, menuname)
        if menu_exists:
            async with aiosqlite.connect("db/roles.db") as db:
                await db.execute("DELETE FROM role_menus WHERE guild_id = ? AND menu_name = ?", (guild_id, menuname))
                await db.execute("DELETE FROM menu_roles WHERE guild_id = ? AND menu_name = ?", (guild_id, menuname))
                await db.commit()
            await interaction.response.send_message(f"The role menu '{menuname}' has been deleted from this guild.", ephemeral=True)
        else:
            await interaction.response.send_message(f"The role menu '{menuname}' does not exist in this guild.", ephemeral=True)

async def setup(bot:commands.Bot):
    await bot.add_cog(Roles(bot))
    await setup_db()

