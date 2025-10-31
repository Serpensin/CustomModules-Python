"""
Discord Private Voice Channel Manager.

This module provides dynamic private voice channel creation and management,
allowing users to create, customize, and control their own voice channels with
various settings including user limits, permissions, channel naming, and more.
"""

# pylint: disable=too-many-lines

import asyncio
import logging
import sqlite3
import sys
import traceback
from typing import Optional

import discord

if sys.version_info < (3, 10):
    raise ImportError("This module requires Python 3.10 or higher to work correctly.")


# Global variables with proper type hints
_c: sqlite3.Cursor
_conn: sqlite3.Connection
_bot: discord.Client
_logger: logging.Logger
internal_db_connection: bool


# Setup
def setup(
    client: discord.Client,
    tree: discord.app_commands.CommandTree,
    connection: Optional[sqlite3.Connection] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Setup the private voice module.

    This function initializes the private voice module by setting up the database,
    adding necessary commands to the command tree, and configuring the logger.

    Args:
        client (discord.Client): The Discord client instance.
        tree (discord.app_commands.CommandTree): The command tree to which commands will be added.
        connection (sqlite3.Connection, optional): The SQLite connection object. Defaults to None.
        logger (logging.Logger, optional): The logger instance. Defaults to None.

    Raises:
        ValueError: If the command tree or Discord client is None.
    """
    global _c, _conn, _bot, _logger, internal_db_connection  # pylint: disable=global-variable-undefined
    _bot = client
    internal_db_connection = False

    if tree is None:
        raise ValueError("Command tree cannot be None.")
    if _bot is None:
        raise ValueError("Discord client cannot be None.")

    if connection is None:
        _conn = sqlite3.connect("PrivateVoice.db")
        internal_db_connection = True
    else:
        _conn = connection
    _c = _conn.cursor()

    # Setup logger with child hierarchy
    if logger:
        _logger = logger.getChild("CustomModules").getChild("PrivateVoice")
    else:
        _logger = logging.getLogger("CustomModules.PrivateVoice")

    _logger.info("PrivateVoice module initialized")

    __setup_database()

    tree.add_command(__pvoice_admin_add)
    tree.add_command(__pvoice_admin_remove)
    tree.add_command(__pvoice_admin_list)
    tree.add_command(__pvoice_commander_add)
    tree.add_command(__pvoice_commander_remove)
    tree.add_command(__pvoice_commander_kick)
    tree.add_command(__pvoice_commander_limit)
    tree.add_command(__pvoice_commander_bitrate)
    tree.add_command(__pvoice_commander_region)
    tree.add_command(__pvoice_commander_rename)

    _logger.info("Module has been initialized.")


def add_listener() -> None:
    """
    Add event listeners for voice state updates and channel deletions.

    This function overrides the existing `on_voice_state_update` and `on_guild_channel_delete`
    event handlers of the Discord client with new handlers that include additional functionality
    for managing private voice channels.

    The new handlers call the original handlers (if they exist) and then perform additional
    actions specific to the private voice module.

    You can also _on_voice_state_update and _on_channel_delete functions directly to the event handlers.
    """
    original_on_voice_state_update = getattr(_bot, "on_voice_state_update", None)
    original_on_guild_channel_delete = getattr(_bot, "on_guild_channel_delete", None)

    async def new_on_voice_state_update(member, before, after):
        if original_on_voice_state_update:
            await original_on_voice_state_update(member, before, after)
        await _on_voice_state_update(member, before, after)

    _bot.on_voice_state_update = new_on_voice_state_update  # type: ignore[misc]

    async def new_on_guild_channel_delete(channel):
        if original_on_guild_channel_delete:
            await original_on_guild_channel_delete(channel)
        _on_channel_delete(channel)

    _bot.on_guild_channel_delete = new_on_guild_channel_delete  # type: ignore[misc]

    _logger.info("Listener has been added.")


def start_garbage_collector() -> None:
    """
    Start the garbage collector task.

    This function creates and starts a background task that periodically checks
    for stale private voice channels in the database and removes them if they no longer exist.

    The garbage collector runs indefinitely until the bot is shut down or the task is cancelled.

    Returns:
        None
    """
    _bot.loop.create_task(__garbage_collector())


# Garbage collector, that checks in specific intervals,
# that all open channels in the db still exist. And if not, removes them.
async def __garbage_collector() -> None:
    """
    Periodically check and remove stale private voice channels.

    This function runs indefinitely as a background task, periodically checking
    the database for private voice channels that no longer exist in the Discord server.
    If such channels are found, they are removed from the database.

    The function handles exceptions and ensures the database connection is properly
    closed if the task is cancelled.

    Returns:
        None
    """

    def _function():
        _c.execute("SELECT channel_id FROM PRIVATEVOICE_OPENCHANNELS")
        open_channels = {channel_id for (channel_id,) in _c.fetchall()}
        stale_channels = [
            channel_id
            for channel_id in open_channels
            if not _bot.get_channel(channel_id)
        ]
        if stale_channels:
            _c.executemany(
                "DELETE FROM PRIVATEVOICE_OPENCHANNELS WHERE channel_id = ?",
                [(channel_id,) for channel_id in stale_channels],
            )
            _conn.commit()
            _logger.debug(
                f"Removed {len(stale_channels)} stale private voice channels: {', '.join(map(str, stale_channels))}"
            )

    while True:
        try:
            _function()
            await asyncio.sleep(60 * 2)
        except asyncio.CancelledError:
            # Cleanup before propagating cancellation
            _conn.commit()
            if internal_db_connection:
                _conn.close()
            raise
        except (discord.HTTPException, sqlite3.Error) as e:
            _logger.error(f"Garbage collector failed: {e}\n{traceback.format_exc()}")
            await asyncio.sleep(20)


# Permission Overwrites
_overwrites_everyone = discord.PermissionOverwrite(
    create_instant_invite=False,
    kick_members=False,
    ban_members=False,
    administrator=False,
    manage_channels=False,
    manage_guild=False,
    add_reactions=False,
    view_audit_log=False,
    priority_speaker=False,
    stream=False,
    read_messages=False,
    view_channel=False,
    send_messages=False,
    send_tts_messages=False,
    manage_messages=False,
    embed_links=False,
    attach_files=False,
    read_message_history=False,
    mention_everyone=False,
    external_emojis=False,
    use_external_emojis=False,
    view_guild_insights=False,
    connect=False,
    speak=False,
    mute_members=False,
    deafen_members=False,
    move_members=False,
    use_voice_activation=False,
    change_nickname=False,
    manage_nicknames=False,
    manage_roles=False,
    manage_permissions=False,
    manage_webhooks=False,
    manage_expressions=False,
    manage_emojis=False,
    manage_emojis_and_stickers=False,
    use_application_commands=False,
    request_to_speak=False,
    manage_events=False,
    manage_threads=False,
    create_public_threads=False,
    create_private_threads=False,
    send_messages_in_threads=False,
    external_stickers=False,
    use_external_stickers=False,
    use_embedded_activities=False,
    moderate_members=False,
    use_soundboard=False,
    use_external_sounds=False,
    send_voice_messages=False,
    create_expressions=False,
    create_events=False,
    send_polls=False,
    create_polls=False,
    use_external_apps=False,
)

_overwrites_channelowner = discord.PermissionOverwrite(
    add_reactions=True,
    priority_speaker=True,
    stream=True,
    read_messages=True,
    view_channel=True,
    send_messages=True,
    send_tts_messages=True,
    embed_links=True,
    attach_files=True,
    read_message_history=True,
    external_emojis=True,
    use_external_emojis=True,
    connect=True,
    speak=True,
    mute_members=True,
    deafen_members=True,
    use_embedded_activities=True,
    use_soundboard=True,
    use_external_sounds=True,
    send_voice_messages=True,
    create_polls=True,
    use_voice_activation=True,
)

_overwrites_channelmember = discord.PermissionOverwrite(
    view_channel=True,
    connect=True,
    speak=True,
    use_voice_activation=True,
    use_external_apps=True,
    use_external_sounds=True,
    use_soundboard=True,
    send_voice_messages=True,
    embed_links=True,
    attach_files=True,
    stream=True,
    external_emojis=True,
    use_external_emojis=True,
)


# Helper functions
def __is_channel_in_private_voice_list(member, channel_id) -> bool:
    """
    Check if a channel is in the private voice list.

    This function queries the database to determine if the specified channel ID
    is listed as an open private voice channel in the given member's guild.

    Args:
        member (discord.Member): The member whose guild is being checked.
        channel_id (int): The ID of the channel to check.

    Returns:
        bool: True if the channel is in the private voice list, False otherwise.
    """
    _c.execute(
        "SELECT 1 FROM PRIVATEVOICE_OPENCHANNELS WHERE guild_id = ? AND channel_id = ?",
        (member.guild.id, channel_id),
    )
    return _c.fetchone() is not None


def __is_channel_flagged_public(channel_id) -> bool:
    """
    Check if a channel is flagged as public.

    This function queries the database to determine if the specified channel ID
    is flagged as public in the PRIVATEVOICE_OPENCHANNELS table.

    Args:
        channel_id (int): The ID of the channel to check.

    Returns:
        bool: True if the channel is flagged as public, False otherwise.
    """
    _c.execute(
        "SELECT public FROM PRIVATEVOICE_OPENCHANNELS WHERE channel_id = ?",
        (channel_id,),
    )
    result = _c.fetchone()
    return result[0] if result else False


def __setup_database() -> None:
    _c.executescript(
        """
    CREATE TABLE IF NOT EXISTS "PRIVATEVOICE_OPENCHANNELS" (
        "id" INTEGER NOT NULL,
        "guild_id" INTEGER NOT NULL,
        "channel_id" INTEGER NOT NULL,
        "channelowner_id" INTEGER NOT NULL,
        "public" BOOLEAN NOT NULL,
        "permit_update" BOOLEAN NOT NULL,
        PRIMARY KEY ("id" AUTOINCREMENT)
    );
    CREATE TABLE IF NOT EXISTS "PRIVATEVOICE_SETTINGS" (
          "id" INTEGER NOT NULL,
          "guild_id" INTEGER NOT NULL,
          "join_to_create_id" INTEGER NOT NULL,
          "category_id" INTEGER NOT NULL,
          "max_users" INTEGER NOT NULL,
          "bitrate" INTEGER NOT NULL,
          "public" BOOLEAN NOT NULL,
          "public_role" INTEGER,
          "permit_update" BOOLEAN NOT NULL,
          "prefix" TEXT,
          PRIMARY KEY ("id" AUTOINCREMENT)
    )
    """
    )


def __is_channel_owner(member, channel_id) -> bool:
    """
    Check if the member is the owner of the specified private voice channel.

    This function queries the database to determine if the given member is the owner
    of the private voice channel identified by the provided channel ID.

    Args:
        member (discord.Member): The member whose ownership status is being checked.
        channel_id (int): The ID of the private voice channel.

    Returns:
        bool: True if the member is the owner of the private voice channel, False otherwise.
    """
    _c.execute(
        "SELECT 1 FROM PRIVATEVOICE_OPENCHANNELS WHERE guild_id = ? AND channel_id = ? AND channelowner_id = ?",
        (member.guild.id, channel_id, member.id),
    )
    return _c.fetchone() is not None


# Is channel allowed to be updated
def __is_channel_allowed_to_update(channel_id) -> bool:
    """
    Check if the channel is allowed to be updated.
    This function queries the database to determine if the specified channel ID
    is allowed to be updated by the owner of the channel.
    Args:
        channel_id (int): The ID of the channel to check.
    Returns:
        bool: True if the channel is allowed to be updated, False otherwise.
    """
    _c.execute(
        "SELECT permit_update FROM PRIVATEVOICE_OPENCHANNELS WHERE channel_id = ?",
        (channel_id,),
    )
    result = _c.fetchone()
    return result[0] if result else False


async def __left_private_vc(member, channel_id) -> None:
    """
    Handle a member leaving a private voice channel.

    This function manages the state of a private voice channel when a member leaves.
    If the channel is public or the member is not the owner, it performs no action.
    If the channel is empty after the member leaves, it deletes the channel and removes
    it from the database. If the channel still has members, it transfers ownership to
    another member and updates the channel's permissions accordingly.

    Args:
        member (discord.Member): The member who left the voice channel.
        channel_id (int): The ID of the voice channel that the member left.

    Returns:
        None
    """
    is_public = __is_channel_flagged_public(channel_id)
    if not __is_channel_owner(member, channel_id) and not is_public:
        return
    channel: discord.VoiceChannel = member.guild.get_channel(channel_id)
    if channel.members:
        if is_public:
            return
        for member_new in channel.members:
            if member_new.id != member.id:
                await channel.edit(
                    name=f"{member_new.display_name}'s Channel",
                    overwrites={
                        member_new: _overwrites_channelowner,
                        member: _overwrites_channelmember,
                        member.guild.default_role: _overwrites_everyone,
                    },
                )
                _c.execute(
                    "UPDATE PRIVATEVOICE_OPENCHANNELS SET channelowner_id = ? WHERE channel_id = ?",
                    (member_new.id, channel_id),
                )
                break
    else:
        await channel.delete()
        _c.execute(
            "DELETE FROM PRIVATEVOICE_OPENCHANNELS WHERE channel_id = ?", (channel_id,)
        )
    _conn.commit()


# pylint: disable=too-many-locals,too-many-nested-blocks
async def __create_private_voice_channel(member, setting) -> None:
    """
    Create a new private voice channel for a member.

    This function creates a new private voice channel for the specified member based on the provided settings.
    It sets the appropriate permissions, generates a unique channel name, and adds the channel to the database.
    If the channel is public, it assigns the public role to the channel's permissions.

    Args:
        member (discord.Member): The member for whom the private voice channel is being created.
        setting (tuple): A tuple containing the settings for the private voice channel, including:
            - setting[3] (int): The ID of the category where the channel will be created.
            - setting[4] (int): The maximum number of users allowed in the channel.
            - setting[5] (int): The bitrate of the channel in kbps.
            - setting[6] (bool): Whether the channel is public.
            - setting[7] (int or None): The ID of the public role, if applicable.
            - setting[8] (bool): Whether the channel owner is allowed to update the channel settings.
            - setting[9] (str): The prefix for the channel name, if applicable.

    Returns:
        None
    """
    guild = member.guild
    category = guild.get_channel(setting[3])
    max_users = setting[4]
    bitrate = setting[5] * 1000  # Convert bitrate once
    public = setting[6]
    public_role = guild.get_role(setting[7]) if setting[7] else None
    permit_update = setting[8]
    prefix = setting[9]

    # Create a new private voice channel
    try:
        overwrites = {
            member: _overwrites_channelowner,
            guild.default_role: _overwrites_everyone,
        }
        if public:
            overwrites[public_role or guild.default_role] = _overwrites_channelmember
            overwrites.pop(member)
            existing_channels = [ch.name for ch in category.voice_channels]
            highest_number = 0
            for ch_name in existing_channels:
                if ch_name.startswith(prefix):
                    try:
                        number = int(ch_name[len(prefix) :].replace("-", "").strip())
                        highest_number = max(highest_number, number)
                    except ValueError:
                        continue
            channel_name = f"{prefix} - {highest_number + 1}"
        else:
            channel_name = f"{member.display_name}'s Channel"

        channel = await category.create_voice_channel(
            name=channel_name,
            overwrites=overwrites,
            bitrate=bitrate,
            user_limit=max_users,
        )
        if not public:
            embed = discord.Embed(
                title="Private Voice Channel",
                description=(
                    "This is your private voice channel. You can use the following commands to manage it."
                ),
                color=discord.Color.blurple(),
            )
            embed.add_field(
                name="Commands",
                value=(
                    "**/pvoice_commander_add <member>** - Add a member to the channel.\n"
                    "**/pvoice_commander_remove <member>** - Remove a member from the channel.\n"
                    "**/pvoice_commander_kick <member>** - Kick a member from the channel.\n"
                    "**/pvoice_commander_limit <limit>** - Set the user limit for the channel.\n"
                    "**/pvoice_commander_bitrate <bitrate>** - Set the bitrate for the channel.\n"
                    "**/pvoice_commander_region <region>** - Set the region for the channel.\n"
                    "**/pvoice_commander_rename <name>** - Rename the channel."
                ),
                inline=False,
            )
            await channel.send(content=member.mention, embed=embed)

        # Add to the database
        _c.execute(
            "INSERT INTO PRIVATEVOICE_OPENCHANNELS "
            "(guild_id, channel_id, channelowner_id, public, permit_update) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                guild.id,
                channel.id,
                0 if public else member.id,
                public,
                permit_update,
            ),
        )
        await member.move_to(channel)
        _logger.debug(
            f"Created a new private voice channel for {member} in {category}."
        )
    except discord.HTTPException as e:
        _logger.error(f"Failed to create a private voice channel for {member}: {e}")
        _c.execute(
            "DELETE FROM PRIVATEVOICE_SETTINGS WHERE join_to_create_id = ?",
            (setting[2],),
        )
        try:
            await member.send(
                f"Failed to create a private voice channel for you in "
                f"{category}. Please contact the server administrator."
            )
        except discord.HTTPException:
            _logger.error(
                f"Failed to send a message to {member} about the failed "
                f"private voice channel creation."
            )
    finally:
        _conn.commit()


async def __handle_private_vc(member, after_channel_id, before_channel_id=None) -> None:
    """
    Handle private voice channel management for a member.

    This function manages the private voice channels for a member when they join, leave, or switch channels.
    It checks if the member is joining a new private voice channel, leaving an existing one, or switching
    between private voice channels, and performs the necessary actions such as setting permissions or
    creating/deleting channels.

    Args:
        member (discord.Member): The member whose voice state has changed.
        after_channel_id (int): The ID of the channel the member joined.
        before_channel_id (int, optional): The ID of the channel the member left. Defaults to None.

    Returns:
        None
    """

    async def __set_channel_member_permissions(member, after_channel_id):
        channel = member.guild.get_channel(after_channel_id)
        if __is_channel_flagged_public(after_channel_id):
            return
        current_permissions = channel.overwrites_for(member)
        if current_permissions != _overwrites_channelmember:
            await channel.set_permissions(member, overwrite=_overwrites_channelmember)
            _logger.debug(
                f"Set permissions for member {member} in channel {after_channel_id}"
            )

    _logger.debug(
        f"Handling private VC for {member}. "
        f"After channel ID: {after_channel_id}, "
        f"Before channel ID: {before_channel_id}"
    )

    _c.execute(
        "SELECT * FROM PRIVATEVOICE_SETTINGS WHERE join_to_create_id = ?",
        (after_channel_id,),
    )
    pvoice_setting = _c.fetchone()

    if not pvoice_setting:
        _logger.debug(
            f"No private voice settings found for channel ID: {after_channel_id}"
        )

        _c.execute(
            "SELECT * FROM PRIVATEVOICE_OPENCHANNELS WHERE guild_id = ? AND channel_id IN (?, ?)",
            (member.guild.id, before_channel_id, after_channel_id),
        )
        pvoice_channels = _c.fetchall()
        pvoice_before = next(
            (channel for channel in pvoice_channels if channel[2] == before_channel_id),
            None,
        )
        pvoice_after = next(
            (channel for channel in pvoice_channels if channel[2] == after_channel_id),
            None,
        )

        match pvoice_before, pvoice_after:
            case None, None:
                return
            case None, pv_after if pv_after is not None:
                _logger.debug(
                    f"Member {member} joined private voice channel {after_channel_id}"
                )
                if member.id != pv_after[3]:
                    _logger.debug(
                        f"Member {member} is not the channel owner, setting permissions"
                    )
                    await __set_channel_member_permissions(member, after_channel_id)
            case _, None:
                _logger.debug(
                    f"Member {member} left private voice channel {before_channel_id}"
                )
                await __left_private_vc(member, before_channel_id)
            case _:
                _logger.debug(
                    f"Member {member} switched from private voice channel {before_channel_id} to {after_channel_id}"
                )
                await __set_channel_member_permissions(member, after_channel_id)
                await __left_private_vc(member, before_channel_id)
    else:
        await __create_private_voice_channel(member, pvoice_setting)
        _logger.debug(
            f"Created private voice channel for member {member} with settings {pvoice_setting}"
        )
        if before_channel_id and __is_channel_in_private_voice_list(
            member, before_channel_id
        ):
            await __left_private_vc(member, before_channel_id)
            _logger.debug(
                f"Handled member {member} leaving private voice channel {before_channel_id}"
            )


async def __is_channel_owner_in_current_vc(interaction: discord.Interaction) -> bool:
    """
    Check if the user is the owner of the current private voice channel.

    This function checks if the user who initiated the interaction is in a private voice channel
    and if they are the owner of that channel. If the user is not in a private voice channel or
    is not the owner, an appropriate message is sent as a response to the interaction.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.

    Returns:
        bool: True if the user is the owner of the private voice channel, False otherwise.
    """
    # interaction.user in guild context is actually a Member
    user = interaction.user
    if not isinstance(user, discord.Member):
        return False
    
    voice_channel_id = (
        user.voice.channel.id if user.voice and user.voice.channel else None
    )

    if not voice_channel_id or not __is_channel_in_private_voice_list(
        user, voice_channel_id
    ):
        await interaction.response.send_message(
            "You are not in a private voice channel.", ephemeral=True
        )
        return False

    if not __is_channel_owner(user, voice_channel_id):
        await interaction.response.send_message(
            "You are not the owner of the private voice channel.", ephemeral=True
        )
        return False

    return True


# Events
async def _on_voice_state_update(member, before, after) -> None:
    """
    Handle voice state updates for members.

    This function is called whenever a member's voice state changes, such as joining,
    leaving, or switching voice channels. It determines the type of voice state change
    and calls the appropriate handler functions to manage private voice channels.

    Args:
        member (discord.Member): The member whose voice state has changed.
        before (discord.VoiceState): The member's previous voice state.
        after (discord.VoiceState): The member's new voice state.

    Returns:
        None
    """
    before_channel_id = before.channel.id if before.channel else None
    after_channel_id = after.channel.id if after.channel else None

    match before_channel_id, after_channel_id:
        case None, after_id if after_id:
            # Joined
            _logger.debug(f"{member} joined {after.channel}")
            await __handle_private_vc(member, after_channel_id)
        case before_id, after_id if before_id and after_id and before_id != after_id:
            # Switched
            _logger.debug(f"{member} switched from {before.channel} to {after.channel}")
            await __handle_private_vc(member, after_channel_id, before_channel_id)
        case before_id, None if before_id:
            # Disconnected
            _logger.debug(f"{member} disconnected from {before.channel}")
            if not __is_channel_in_private_voice_list(member, before_channel_id):
                return
            await __left_private_vc(member, before_channel_id)
        case _:
            return


def _on_channel_delete(channel) -> None:
    """
    Handle the deletion of a channel.

    This function is called whenever a channel is deleted in the Discord server.
    It removes the corresponding entries from the PRIVATEVOICE_SETTINGS and
    PRIVATEVOICE_OPENCHANNELS tables in the database.

    Args:
        channel (discord.Channel): The channel that was deleted.

    Returns:
        None
    """
    _c.executescript(
        """
        DELETE FROM PRIVATEVOICE_SETTINGS WHERE join_to_create_id = {channel_id};
        DELETE FROM PRIVATEVOICE_OPENCHANNELS WHERE channel_id = {channel_id};
    """.format(
            channel_id=channel.id
        )
    )
    _conn.commit()


# Discord AppCommands (/)
@discord.app_commands.command(
    name="pvoice_admin_add",
    description="Add a new private voice channel generator to the server.",
)
@discord.app_commands.checks.has_permissions(manage_guild=True, manage_channels=True)
@discord.app_commands.describe(
    channel="The channel that will create the private voice channels upon joining.",
    category="The category where the private voice channels will be created.",
    max_users="The maximum number of users that can join the private voice channel.",
    bitrate="The bitrate (8-384) of the private voice channel. "
    "(Defaults to 64, if not possible.)",
    permit_update="If the owner should be able to change the bitrate, "
    "region, name and user limit. (Doesn't affect public ones.",
    public="If the channel should be a public one by default.",
    public_role="The role that will be able to join the public channel. "
    "(Defaults to everyone.)",
    prefix="The prefix for the private voice channel name. "
    "(Required/used only for public channels.)",
)
@discord.app_commands.guild_only
# pylint: disable=too-many-arguments,too-many-positional-arguments
async def __pvoice_admin_add(
    interaction: discord.Interaction,
    channel: discord.VoiceChannel,
    category: discord.CategoryChannel,
    max_users: int,
    permit_update: bool,
    bitrate: int = 64,
    public: bool = False,
    public_role: Optional[discord.Role] = None,
    prefix: str = "",
) -> None:
    """
    Add a new private voice channel generator to the server.

    This command allows an administrator to add a new private voice channel generator to the server.
    It checks if the specified channel is already a private voice channel generator, updates or inserts
    the corresponding entry in the database, and sends a confirmation message.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        channel (discord.VoiceChannel): The channel that will create the private voice channels upon joining.
        category (discord.CategoryChannel): The category where the private voice channels will be created.
        max_users (int): The maximum number of users that can join the private voice channel.
        permit_update (bool): If the owner should be able to change the bitrate, region, name, and user limit.
        bitrate (int, optional):
            The bitrate (8-384) of the private voice channel. Defaults to 64.
        public (bool, optional):
            If the channel should be a public one by default. Defaults to False.
        public_role (discord.Role, optional):
            The role that will be able to join the public channel. Defaults to None.
        prefix (str, optional):
            The prefix for the private voice channel name.
            Required/used only for public channels. Defaults to ''.

    Returns:
        None
    """
    if not interaction.guild:
        await interaction.response.send_message(
            "This command can only be used in a server.", ephemeral=True
        )
        return

    if public and not prefix.strip():
        await interaction.response.send_message(
            "The prefix is required for public channels.", ephemeral=True
        )
        return

    _c.execute(
        "SELECT 1 FROM PRIVATEVOICE_SETTINGS WHERE guild_id = ? AND join_to_create_id = ?",
        (interaction.guild.id, channel.id),
    )
    update = _c.fetchone() is not None

    _c.execute(
        "SELECT COUNT(*) FROM PRIVATEVOICE_SETTINGS WHERE guild_id = ?",
        (interaction.guild.id,),
    )
    if _c.fetchone()[0] >= 20:
        await interaction.response.send_message(
            "You have reached the maximum number of private voice channel generators for this server (20).",
            ephemeral=True,
        )
        return

    if not 0 <= max_users <= 99:
        await interaction.response.send_message(
            "The maximum number of users must be between 0 and 99.", ephemeral=True
        )
        return

    if bitrate < 8:
        bitrate = 64
    elif bitrate > 384:
        match interaction.guild.premium_tier:
            case 1:
                bitrate = 128
            case 2:
                bitrate = 256
            case 3:
                bitrate = 384
            case _:
                bitrate = 96

    if update:
        _c.execute(
            "UPDATE PRIVATEVOICE_SETTINGS SET "
            "category_id = ?, max_users = ?, bitrate = ?, public = ?, "
            "public_role = ?, permit_update = ?, prefix = ? "
            "WHERE guild_id = ? AND join_to_create_id = ?",
            (
                category.id,
                max_users,
                bitrate,
                public,
                public_role.id if public_role else None,
                permit_update,
                prefix.strip(),
                interaction.guild.id,
                channel.id,
            ),
        )
    else:
        _c.execute(
            "INSERT INTO PRIVATEVOICE_SETTINGS "
            "(guild_id, join_to_create_id, category_id, max_users, "
            "bitrate, public, public_role, permit_update, prefix) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                interaction.guild.id,
                channel.id,
                category.id,
                max_users,
                bitrate,
                public,
                public_role.id if public_role else None,
                permit_update,
                prefix.strip(),
            ),
        )
    _conn.commit()

    infinity_symbol = "\u221e"
    max_users_display = infinity_symbol if max_users == 0 else max_users
    msg = (
        f"Private voice channel generator has been "
        f"{'updated' if update else 'added'} successfully.\n\n"
        f"**Channel:** {channel.mention}\n"
        f"**Category:** {category.mention}\n"
        f"**Max Users:** {max_users_display}\n"
        f"**Bitrate:** {bitrate}kbps\n"
        f"**Allow updates:** {permit_update}\n"
        f"**Prefix:** {prefix}\n"
        f"**Public:** {public}\n"
        f"**Public Role:** {'' if not public_role else public_role.mention}"
    )
    await interaction.response.send_message(
        msg,
        ephemeral=True,
    )


@discord.app_commands.command(
    name="pvoice_admin_remove",
    description="Remove a private voice channel generator from the server.",
)
@discord.app_commands.describe(
    channel="The channel that creates the private voice channels upon joining.",
    remove="Should the channel be removed also?",
)
@discord.app_commands.checks.has_permissions(manage_guild=True, manage_channels=True)
@discord.app_commands.guild_only
async def __pvoice_admin_remove(
    interaction: discord.Interaction, channel: discord.VoiceChannel, remove: bool
) -> None:
    """
    Remove a private voice channel generator from the server.

    This command allows an administrator to remove a private voice channel generator from the server.
    It checks if the specified channel is a private voice channel generator, deletes the corresponding
    entry from the database, and optionally removes the channel from the server.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        channel (discord.VoiceChannel): The channel that creates the private voice channels upon joining.
        remove (bool): Whether the channel should be removed from the server.

    Returns:
        None
    """
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.", ephemeral=True
        )
        return
    
    _c.execute(
        "SELECT * FROM PRIVATEVOICE_SETTINGS WHERE guild_id = ? AND join_to_create_id = ?",
        (interaction.guild.id, channel.id),
    )
    if not _c.fetchone():
        await interaction.response.send_message(
            "This channel is not a private voice channel generator.", ephemeral=True
        )
        return
    _c.execute(
        "DELETE FROM PRIVATEVOICE_SETTINGS WHERE guild_id = ? AND join_to_create_id = ?",
        (interaction.guild.id, channel.id),
    )
    _conn.commit()
    if remove:
        try:
            await channel.delete()
        except (discord.Forbidden, discord.HTTPException) as e:
            _logger.error(f"Failed to remove channel: {e}")
            await interaction.response.send_message(
                "Failed to remove the channel.", ephemeral=True
            )
            return
    await interaction.response.send_message(
        "Private voice channel generator has been removed successfully.", ephemeral=True
    )


@discord.app_commands.command(
    name="pvoice_admin_list",
    description="List all private voice channel generators in the server.",
)
@discord.app_commands.checks.has_permissions(manage_guild=True, manage_channels=True)
@discord.app_commands.guild_only
async def __pvoice_admin_list(interaction: discord.Interaction) -> None:
    """
    List all private voice channel generators in the server.

    This command retrieves and lists all private voice channel generators configured in the server.
    It queries the database for private voice settings associated with the server's guild ID,
    and constructs an embed message containing details of each private voice channel generator.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.

    Returns:
        None
    """
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.", ephemeral=True
        )
        return
    
    _c.execute(
        "SELECT * FROM PRIVATEVOICE_SETTINGS WHERE guild_id = ?",
        (interaction.guild.id,),
    )
    settings = _c.fetchall()
    if not settings:
        await interaction.response.send_message(
            "No private voice channel generators found.", ephemeral=True
        )
        return
    embed = discord.Embed(title="Private Voice Channels", color=discord.Color.blurple())
    for setting in settings:
        channel = interaction.guild.get_channel(setting[2])
        category = interaction.guild.get_channel(setting[3])
        if channel is None or category is None:
            continue
        max_users_display = "\u221e" if setting[4] == 0 else setting[4]
        public_role_display = "" if not setting[6] else f"<@&{setting[6]}>"
        embed.add_field(
            name=f"Channel: {channel.name}",
            value=(
                f"Category: {category.name}\n"
                f"Max Users: {max_users_display}\n"
                f"Bitrate: {setting[5]}kbps\n"
                f"Allow updates: {setting[8]}\n"
                f"Prefix: {setting[9]}\n"
                f"Public: {setting[6]}\n"
                f"**Public Role:** {public_role_display}"
            ),
            inline=False,
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@discord.app_commands.command(
    name="pvoice_commander_add",
    description="Add a user to your current private voice channel.",
)
@discord.app_commands.describe(member="The member to add to the private voice channel.")
@discord.app_commands.guild_only
async def __pvoice_commander_add(
    interaction: discord.Interaction, member: discord.Member
) -> None:
    """
    Add a user to your current private voice channel.

    This command allows the owner of a private voice channel to add a specified member to the channel.
    It checks if the command is used in a server, verifies that the user issuing the command is the owner
    of the private voice channel, and then adds the specified member to the channel's permissions.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        member (discord.Member): The member to add to the private voice channel.

    Returns:
        None
    """
    if not await __is_channel_owner_in_current_vc(interaction):
        return

    # At this point we know the user is a Member with voice state
    assert interaction.guild is not None
    assert isinstance(interaction.user, discord.Member)
    assert interaction.user.voice is not None
    assert interaction.user.voice.channel is not None
    
    channel = interaction.guild.get_channel(interaction.user.voice.channel.id)
    if not isinstance(channel, discord.VoiceChannel):
        await interaction.response.send_message(
            "Invalid channel type.", ephemeral=True
        )
        return
    
    if len(channel.members) >= channel.user_limit:
        await interaction.response.send_message(
            "The private voice channel is full.", ephemeral=True
        )
        return
    await channel.set_permissions(member, overwrite=_overwrites_channelmember)
    await interaction.response.send_message(
        f"User {member} has been added to the private voice channel.", ephemeral=True
    )


@discord.app_commands.command(
    name="pvoice_commander_remove",
    description="Remove a user from your current private voice channel.",
)
@discord.app_commands.describe(
    member="The member to remove from the private voice channel."
)
@discord.app_commands.guild_only
async def __pvoice_commander_remove(
    interaction: discord.Interaction, member: discord.Member
) -> None:
    """
    Remove a user from your current private voice channel.

    This command allows the owner of a private voice channel to remove a specified member from the channel.
    It checks if the command is used in a server, verifies that the user issuing the command is the owner
    of the private voice channel, and then removes the specified member from the channel's permissions.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        member (discord.Member): The member to remove from the private voice channel.

    Returns:
        None
    """
    if not await __is_channel_owner_in_current_vc(interaction):
        return

    # At this point we know the user is a Member with voice state
    assert isinstance(interaction.user, discord.Member)
    assert interaction.user.voice is not None
    assert interaction.user.voice.channel is not None
    
    channel = interaction.user.voice.channel
    if member not in channel.overwrites:
        await interaction.response.send_message(
            f"User {member.mention} is not in the private voice channel.",
            ephemeral=True,
        )
        return
    await channel.set_permissions(member, overwrite=None)
    await interaction.response.send_message(
        f"User {member.mention} has been removed from the private voice channel.",
        ephemeral=True,
    )


@discord.app_commands.command(
    name="pvoice_commander_kick",
    description="Kick a user from your current private voice channel.",
)
@discord.app_commands.describe(
    member="The member to kick from the private voice channel."
)
@discord.app_commands.guild_only
async def __pvoice_commander_kick(
    interaction: discord.Interaction, member: discord.Member
) -> None:
    """
    Kick a user from your current private voice channel.

    This command allows the owner of a private voice channel to kick a specified member from the channel.
    It checks if the command is used in a server, verifies that the user issuing the command is the owner
    of the private voice channel, and then removes the specified member from the channel.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        member (discord.Member): The member to kick from the private voice channel.

    Returns:
        None
    """
    if not await __is_channel_owner_in_current_vc(interaction):
        return

    # At this point we know the user is a Member with voice state
    assert isinstance(interaction.user, discord.Member)
    assert interaction.user.voice is not None
    assert interaction.user.voice.channel is not None
    
    channel = interaction.user.voice.channel
    if member not in channel.members:
        await interaction.response.send_message(
            f"User {member.mention} is not in the private voice channel.",
            ephemeral=True,
        )
        return
    await member.move_to(None)
    await interaction.response.send_message(
        f"User {member.mention} has been kicked from the private voice channel.",
        ephemeral=True,
    )


@discord.app_commands.command(
    name="pvoice_commander_limit",
    description="Set the user limit for your current private voice channel.",
)
@discord.app_commands.describe(
    limit="The maximum number of users allowed in the private voice channel."
)
@discord.app_commands.guild_only
async def __pvoice_commander_limit(
    interaction: discord.Interaction, limit: int
) -> None:
    """
    Set the user limit for your current private voice channel.

    This command allows the owner of a private voice channel to set the user limit for the channel.
    It checks if the command is used in a server, verifies that the user issuing the command is the owner
    of the private voice channel, and then sets the user limit to the specified value.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        limit (int): The maximum number of users allowed in the private voice channel.

    Returns:
        None
    """
    if limit < 0 or limit > 99:
        await interaction.response.send_message(
            "The user limit must be between 0 and 99.", ephemeral=True
        )
        return

    if not await __is_channel_owner_in_current_vc(interaction):
        return

    # At this point we know the user is a Member with voice state
    assert isinstance(interaction.user, discord.Member)
    assert interaction.user.voice is not None
    assert interaction.user.voice.channel is not None
    
    channel = interaction.user.voice.channel
    if not __is_channel_allowed_to_update(channel.id):
        await interaction.response.send_message(
            "You are not allowed to change the user limit of the private voice channel.",
            ephemeral=True,
        )
        return
    await channel.edit(user_limit=limit)
    await interaction.response.send_message(
        f"User limit for the private voice channel has been set to {limit}.",
        ephemeral=True,
    )


@discord.app_commands.command(
    name="pvoice_commander_bitrate",
    description="Set the bitrate for your current private voice channel.",
)
@discord.app_commands.describe(
    bitrate="The bitrate (8-384) of the private voice channel."
)
@discord.app_commands.guild_only
async def __pvoice_commander_bitrate(
    interaction: discord.Interaction, bitrate: int
) -> None:
    """
    Set the bitrate for your current private voice channel.

    This command allows the owner of a private voice channel to set the bitrate for the channel.
    It checks if the command is used in a server, verifies that the user issuing the command is the owner
    of the private voice channel, and then sets the bitrate to the specified value.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        bitrate (int): The bitrate (8-384) of the private voice channel.

    Returns:
        None
    """
    if not await __is_channel_owner_in_current_vc(interaction):
        return
    
    # At this point we know the user is a Member with voice state
    assert isinstance(interaction.user, discord.Member)
    assert interaction.user.voice is not None
    assert interaction.user.voice.channel is not None
    assert interaction.guild is not None
    
    channel = interaction.user.voice.channel
    if not __is_channel_allowed_to_update(channel.id):
        await interaction.response.send_message(
            "You are not allowed to change the bitrate of the private voice channel.",
            ephemeral=True,
        )
        return

    if bitrate < 8:
        bitrate = 64
    match interaction.guild.premium_tier:
        case 0 if bitrate > 96:
            bitrate = 96
        case 1 if bitrate > 128:
            bitrate = 128
        case 2 if bitrate > 256:
            bitrate = 256
        case 3 if bitrate > 384:
            bitrate = 384

    await channel.edit(bitrate=bitrate * 1000)
    await interaction.response.send_message(
        f"Bitrate for the private voice channel has been set to {bitrate}kbps.",
        ephemeral=True,
    )


@discord.app_commands.command(
    name="pvoice_commander_region",
    description="Set the region for your current private voice channel.",
)
@discord.app_commands.describe(region="The region for the private voice channel.")
@discord.app_commands.choices(
    region=[
        discord.app_commands.Choice(name="<Automatic>", value=""),
        discord.app_commands.Choice(name="Brazil", value="brazil"),
        discord.app_commands.Choice(name="Hong Kong", value="hongkong"),
        discord.app_commands.Choice(name="India", value="india"),
        discord.app_commands.Choice(name="Japan", value="japan"),
        discord.app_commands.Choice(name="Rotterdam", value="rotterdam"),
        discord.app_commands.Choice(name="Russia", value="russia"),
        discord.app_commands.Choice(name="Singapore", value="singapore"),
        discord.app_commands.Choice(name="South Korea", value="south-korea"),
        discord.app_commands.Choice(name="South Africa", value="southafrica"),
        discord.app_commands.Choice(name="Sydney", value="sydney"),
        discord.app_commands.Choice(name="US Central", value="us-central"),
        discord.app_commands.Choice(name="US East", value="us-east"),
        discord.app_commands.Choice(name="US South", value="us-south"),
        discord.app_commands.Choice(name="US West", value="us-west"),
    ]
)
@discord.app_commands.guild_only
async def __pvoice_commander_region(
    interaction: discord.Interaction, region: str
) -> None:
    """
    Set the region for your current private voice channel.

    This command allows the owner of a private voice channel to set the
    region for the channel. It checks if the command is used in a server,
    verifies that the user issuing the command is the owner of the private
    voice channel, and then sets the region to the specified value.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        region (str): The region for the private voice channel. An empty string sets the region to automatic.

    Returns:
        None
    """
    if not await __is_channel_owner_in_current_vc(interaction):
        return
    
    # At this point we know the user is a Member with voice state
    assert isinstance(interaction.user, discord.Member)
    assert interaction.user.voice is not None
    assert interaction.user.voice.channel is not None
    
    channel = interaction.user.voice.channel
    if not __is_channel_allowed_to_update(channel.id):
        await interaction.response.send_message(
            "You are not allowed to change the region of the private voice channel.",
            ephemeral=True,
        )
        return
    await channel.edit(rtc_region=None if region == "" else region)
    await interaction.response.send_message(
        f"Region for the private voice channel has been set to {'**automatic**' if region == '' else '**' + region + '**'}.",
        ephemeral=True,
    )


@discord.app_commands.command(
    name="pvoice_commander_rename",
    description="Rename your current private voice channel.",
)
@discord.app_commands.describe(name="The new name for the private voice channel.")
@discord.app_commands.guild_only
async def __pvoice_commander_rename(
    interaction: discord.Interaction, name: str
) -> None:
    """
    Rename your current private voice channel.

    This command allows the owner of a private voice channel to rename the channel.
    It checks if the command is used in a server, verifies that the user issuing the command is the owner
    of the private voice channel, and then renames the channel to the specified name.

    Args:
        interaction (discord.Interaction): The interaction object representing the command invocation.
        name (str): The new name for the private voice channel.

    Returns:
        None
    """
    if not await __is_channel_owner_in_current_vc(interaction):
        return
    
    # At this point we know the user is a Member with voice state
    assert isinstance(interaction.user, discord.Member)
    assert interaction.user.voice is not None
    assert interaction.user.voice.channel is not None
    
    channel = interaction.user.voice.channel
    if not __is_channel_allowed_to_update(channel.id):
        await interaction.response.send_message(
            "You are not allowed to rename the private voice channel.", ephemeral=True
        )
        return

    await channel.edit(name=name)
    await interaction.response.send_message(
        f"Private voice channel has been renamed to {name}.", ephemeral=True
    )


if __name__ == "__main__":
    print("This module is not meant to be run directly.")
    sys.exit(1)
