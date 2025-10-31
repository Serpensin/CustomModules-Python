import sys

if sys.version_info < (3, 10):
    raise ImportError("This module requires Python 3.10 or higher to work correctly.")
import asyncio
import logging
import sqlite3
from datetime import datetime
from time import time
from typing import Any, Literal, Optional

import discord
import pytz

from CustomModules.bitmap_handler import BitmapHandler

# Global variables with proper type hints
_c: sqlite3.Cursor
_conn: sqlite3.Connection
_bot: discord.Client
_logger: logging.Logger
_bitmap_handler: BitmapHandler

# SQL query constants
SQL_DELETE_STATDOCK_BY_CHANNEL = "DELETE FROM `STATDOCK` WHERE `channel_id` = ?"
ERR_GUILD_ONLY = "This command can only be used in a guild."

_overwrites = discord.PermissionOverwrite(
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
    view_channel=True,
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

_bitmap = [
    "time",  # 0
    "role",  # 1
    "member",  # 2
    "countusers",  # 3
    "countbots",  # 4
    "counttext",  # 5
    "countvoice",  # 6
    "countcategory",  # 7
    "channel",  # 8
    "countstage",  # 9
    "countforum",  # 10
    # MAXENTRY 63
]


# Setup
def setup(
    client: discord.Client,
    tree: discord.app_commands.CommandTree,
    connection: Optional[sqlite3.Connection] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    global _c, _conn, _bot, _logger, _bitmap_handler
    _bot = client
    _bitmap_handler = BitmapHandler(_bitmap)

    if tree is None:
        raise ValueError("Command tree cannot be None.")
    if _bot is None:
        raise ValueError("Discord client cannot be None.")

    if connection is None:
        _conn = sqlite3.connect("StatDocks.db")
    _c = _conn.cursor()

    # Setup logger with child hierarchy
    if logger:
        _logger = logger.getChild("CustomModules").getChild("StatDock")
    else:
        _logger = logging.getLogger("CustomModules.StatDock")

    _setup_database()

    tree.add_command(_statdock_add)
    tree.add_command(_statdock_list)
    tree.add_command(_statdock_update)
    tree.add_command(_statdock_enable_hidden)

    _logger.info("StatDock module has been set up.")


async def task() -> None:
    # Calling this function in setup_hook(), can/will lead to a deadlock!
    async def _function():
        _c.execute(
            "SELECT * FROM `STATDOCK` WHERE `enabled` = 1 AND (last_updated + frequency * 60) < ?",
            (int(time()),),
        )
        data = _c.fetchall()
        for entry in data:
            guild_id = entry[2]
            category_id = entry[3]
            channel_id = entry[4]
            stat_type = entry[5]
            timezone = entry[6]
            timeformat = entry[7]
            counter = entry[12]
            role_id = entry[8]
            prefix = entry[9]

            await _update_dock(
                enabled=True,
                guild_id=guild_id,
                category_id=category_id,
                channel_id=channel_id,
                stat_type=stat_type,
                timezone=timezone,
                timeformat=timeformat,
                counter=counter,
                role_id=role_id,
                prefix=prefix,
            )

    await _bot.wait_until_ready()
    _logger.info("Task has been started.")

    while True:
        await _function()
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            break


def _setup_database() -> None:
    if _conn is None:
        raise ValueError("Database connection is not initialized.")
    _c.executescript(
        """
    CREATE TABLE IF NOT EXISTS "STATDOCK" (
        `id` integer not null primary key autoincrement,
        `enabled` BOOLEAN not null default 1,
        `guild_id` INT not null,
        `category_id` INT not null,
        `channel_id` INT not null,
        `type` INT not null,
        `timezone` varchar(255) null,
        `timeformat` varchar(255) null,
        `role_id` INT null,
        `prefix` varchar(255) null,
        `frequency` INT not null,
        `last_updated` INT not null,
        `counter` INT not null default 0
    )
    """
    )


# Main functions
async def _init_dock(
    guild: discord.Guild,
    category: discord.CategoryChannel,
    channel: discord.VoiceChannel,
    stat_type: Literal["time", "role", "member"],
    timezone: str,
    timeformat: str,
    role: Optional[discord.Role],
    prefix: Optional[str],
    frequency: int,
    countbots: bool = False,
    countusers: bool = False,
    counttext: bool = False,
    countvoice: bool = False,
    countcategory: bool = False,
    countstage: bool = False,
    countforum: bool = False,
) -> Optional[str]:
    # Initializes the dock the first time.
    try:
        match stat_type:
            case "time":
                prefix_with_space = prefix + " " if prefix else ""
                current_time = _get_current_time(
                    timezone=timezone, time_format=timeformat
                )
                await channel.edit(name=f"{prefix_with_space}{current_time}")
            case "role":
                members_in_role = await _count_members_by_role(
                    role=role, countbots=countbots, countusers=countusers
                )
                prefix_with_space = prefix + " " if prefix else ""
                await channel.edit(name=f"{prefix_with_space}{members_in_role}")
            case "member":
                members_in_guild = await _count_members_in_guild(
                    guild=guild, countbots=countbots, countusers=countusers
                )
                prefix_with_space = prefix + " " if prefix else ""
                await channel.edit(name=f"{prefix_with_space}{members_in_guild}")
            case "channel":
                channels_in_guild = await _count_channels_in_guild(
                    guild=guild,
                    counttext=counttext,
                    countvoice=countvoice,
                    countcategory=countcategory,
                    countstage=countstage,
                    countforum=countforum,
                )
                prefix_with_space = prefix + " " if prefix else ""
                await channel.edit(name=f"{prefix_with_space}{channels_in_guild}")

            case _:
                raise ValueError(f"Invalid stat_type: {stat_type}.")
    except Exception as e:
        _logger.warning(e)
        return str(e)

    _c.execute(
        "INSERT INTO `STATDOCK` (guild_id, category_id, channel_id, type, timezone, timeformat, prefix, frequency, last_updated, counter, role_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            guild.id,
            category.id,
            channel.id,
            _bitmap_handler.get_bitkey(stat_type),
            timezone,
            timeformat,
            prefix,
            frequency,
            int(time()),
            _bitmap_handler.get_bitkey(
                "countbots" if countbots else "",
                "countusers" if countusers else "",
                "counttext" if counttext else "",
                "countvoice" if countvoice else "",
                "countcategory" if countcategory else "",
                "countstage" if countstage else "",
                "countforum" if countforum else "",
            ),
            None if not role else role.id,
        ),
    )
    _conn.commit()


async def _re_init_dock(
    guild_id: int,
    category_id: int,
    channel_id: int,
    stat_type: str,
    timezone: str,
    timeformat: str,
    counter: int,
    role_id: int,
    prefix: str,
    ignore_none_category: bool = False,
) -> None:
    # Re-initializes the dock, if the channel got deleted and the stat dock not disabled/deleted.
    if _conn is None:
        raise ValueError("Database connection is not initialized.")
    guild: Optional[discord.Guild] = await _get_or_fetch("guild", guild_id)
    category: Optional[discord.CategoryChannel] = await _get_or_fetch("channel", category_id)
    
    # For role type, get the role
    role: Optional[discord.Role] = None
    if stat_type == "role":
        role = await _get_or_fetch("role", role_id)
    
    if (
        guild is None
        or (category is None and not ignore_none_category)
        or (stat_type == "role" and role is None)
    ):
        _c.execute(SQL_DELETE_STATDOCK_BY_CHANNEL, (channel_id,))
        _conn.commit()
        return
    
    try:
        created_channel = None
        match stat_type:
            case "time":
                prefix_with_space = prefix + " " if prefix else ""
                current_time = _get_current_time(
                    timezone=timezone, time_format=timeformat
                )
                created_channel = await guild.create_voice_channel(
                    name=f"{prefix_with_space}{current_time}",
                    category=category,
                    overwrites={guild.default_role: _overwrites},
                )
            case "role":
                if role is None:
                    _logger.error("Role is None despite passing validation")
                    return
                members_in_role = await _count_members_by_role(
                    role=role,
                    countbots=_bitmap_handler.check_key_in_bitkey("countbots", counter),
                    countusers=_bitmap_handler.check_key_in_bitkey("countusers", counter),
                )
                prefix_with_space = prefix + " " if prefix else ""
                created_channel = await guild.create_voice_channel(
                    name=f"{prefix_with_space}{members_in_role}",
                    category=category,
                    overwrites={guild.default_role: _overwrites},
                )
            case "member":
                members_in_guild = await _count_members_in_guild(
                    guild=guild,
                    countbots=_bitmap_handler.check_key_in_bitkey("countbots", counter),
                    countusers=_bitmap_handler.check_key_in_bitkey("countusers", counter),
                )
                prefix_with_space = prefix + " " if prefix else ""
                created_channel = await guild.create_voice_channel(
                    name=f"{prefix_with_space}{members_in_guild}",
                    category=category,
                    overwrites={guild.default_role: _overwrites},
                )
            case "channel":
                channels_in_guild = await _count_channels_in_guild(
                    guild=guild,
                    counttext=_bitmap_handler.check_key_in_bitkey("counttext", counter),
                    countvoice=_bitmap_handler.check_key_in_bitkey("countvoice", counter),
                    countcategory=_bitmap_handler.check_key_in_bitkey("countcategory", counter),
                    countstage=_bitmap_handler.check_key_in_bitkey("countstage", counter),
                    countforum=_bitmap_handler.check_key_in_bitkey("countforum", counter),
                )
                prefix_with_space = prefix + " " if prefix else ""
                created_channel = await guild.create_voice_channel(
                    name=f"{prefix_with_space}{channels_in_guild}",
                    category=category,
                    overwrites={guild.default_role: _overwrites},
                )

        if created_channel:
            _c.execute(
                "UPDATE `STATDOCK` SET `last_updated` = ?, `channel_id` = ?, enabled = 1 WHERE `channel_id` = ?",
                (
                    int(time()),
                    created_channel.id,
                    channel_id,
                ),
            )
            _conn.commit()
    except Exception as e:
        _logger.warning(e)


async def _update_dock(
    enabled,
    guild_id,
    category_id,
    channel_id,
    stat_type,
    timezone,
    timeformat,
    counter,
    role_id,
    prefix,
) -> Optional[bool]:
    # Updates a dock.
    if _conn is None:
        raise ValueError("Database connection is not initialized.")
    channel_result = await _get_or_fetch("channel", channel_id)
    guild_result = await _get_or_fetch("guild", guild_id)
    stat_type = _bitmap_handler.get_active_keys(stat_type, single=True)
    if not channel_result or not guild_result:
        if not enabled:
            _c.execute("DELETE FROM `STATDOCK` WHERE `channel_id` = ?", (channel_id,))
            _conn.commit()
            return False
        else:
            await _re_init_dock(
                guild_id=guild_id,
                category_id=category_id,
                channel_id=channel_id,
                stat_type=stat_type,  # type: ignore[arg-type]
                timezone=timezone,
                timeformat=timeformat,
                counter=counter,
                role_id=role_id,
                prefix=prefix,
            )
    else:
        # Type narrow to ensure we have the correct types
        channel = channel_result
        guild = guild_result
        assert isinstance(channel, discord.VoiceChannel)
        assert isinstance(guild, discord.Guild)
        
        try:
            new_name = None
            match stat_type:
                case "time":
                    new_name = f"{prefix + ' ' if prefix else ''}{_get_current_time(timezone=timezone, time_format=timeformat)}"
                case "role":
                    role: Optional[discord.Role] = guild.get_role(role_id)
                    if role is None:
                        _logger.warning(f"Role {role_id} not found in guild {guild_id}")
                        return
                    members_in_role = await _count_members_by_role(
                        role=role,
                        countbots=_bitmap_handler.check_key_in_bitkey("countbots", counter),
                        countusers=_bitmap_handler.check_key_in_bitkey("countusers", counter),
                    )
                    new_name = f"{prefix + ' ' if prefix else ''}{members_in_role}"
                case "member":
                    members_in_guild = await _count_members_in_guild(
                        guild=guild,
                        countbots=_bitmap_handler.check_key_in_bitkey("countbots", counter),
                        countusers=_bitmap_handler.check_key_in_bitkey("countusers", counter),
                    )
                    new_name = f"{prefix + ' ' if prefix else ''}{members_in_guild}"
                case "channel":
                    channels_in_guild = await _count_channels_in_guild(
                        guild=guild,
                        counttext=_bitmap_handler.check_key_in_bitkey("counttext", counter),
                        countvoice=_bitmap_handler.check_key_in_bitkey("countvoice", counter),
                        countcategory=_bitmap_handler.check_key_in_bitkey(
                            "countcategory", counter
                        ),
                        countstage=_bitmap_handler.check_key_in_bitkey("countstage", counter),
                        countforum=_bitmap_handler.check_key_in_bitkey("countforum", counter),
                    )
                    new_name = f"{prefix + ' ' if prefix else ''}{channels_in_guild}"
            if new_name and channel.name != new_name:
                await channel.edit(name=new_name)
            _c.execute(
                "UPDATE `STATDOCK` SET `last_updated` = ? WHERE `channel_id` = ?",
                (
                    int(time()),
                    channel_id,
                ),
            )
            _conn.commit()
        except Exception as e:
            _logger.warning(e)


# Helper functions
async def _count_members_in_guild(
    guild: discord.Guild, countbots: bool, countusers: bool
) -> int:
    members = [
        member
        for member in guild.members
        if (countusers and not member.bot) or (countbots and member.bot)
    ]
    return len(members)


async def _count_members_by_role(
    role: Optional[discord.Role], countbots: bool, countusers: bool
) -> int:
    if role is None:
        return 0
    members_in_role = [
        member
        for member in role.members
        if (countusers and not member.bot) or (countbots and member.bot)
    ]
    return len(members_in_role)


async def _count_channels_in_guild(
    guild: discord.Guild,
    counttext: bool,
    countvoice: bool,
    countcategory: bool,
    countstage: bool,
    countforum: bool,
) -> int:
    count = 0

    for channel in guild.channels:
        match channel:
            case discord.TextChannel() if counttext:
                count += 1
            case discord.VoiceChannel() if countvoice:
                count += 1
            case discord.CategoryChannel() if countcategory:
                count += 1
            case discord.StageChannel() if countstage:
                count += 1
            case discord.ForumChannel() if countforum:
                count += 1

    return count


async def _get_or_fetch(item: str, item_id: int) -> Optional[Any]:
    """
    Attempts to retrieve an object using the 'get_<item>' method of the bot class, and
    if not found, attempts to retrieve it using the 'fetch_<item>' method.

    :param item: Name of the object to retrieve
    :param item_id: ID of the object to retrieve
    :return: Object if found, else None
    :raises AttributeError: If the required methods are not found in the bot class
    """
    get_method_name = f"get_{item}"
    fetch_method_name = f"fetch_{item}"

    get_method = getattr(_bot, get_method_name, None)
    fetch_method = getattr(_bot, fetch_method_name, None)

    if get_method is None or fetch_method is None:
        raise AttributeError(
            f"Methods {get_method_name} or {fetch_method_name} not found on bot object."
        )

    item_object = get_method(item_id)
    if item_object is None:
        try:
            item_object = await fetch_method(item_id)
        except (discord.NotFound, discord.Forbidden):
            pass
    return item_object


def _is_valid_timezone(timezone: str) -> bool:
    """Check if timezone is valid."""
    return timezone in pytz.all_timezones


def _is_valid_timeformat(timeformat: str) -> bool:
    """Check if timeformat is valid."""
    try:
        datetime.now().strftime(timeformat)
        return True
    except ValueError:
        return False


def _get_current_time(timezone: str, time_format: str) -> str:
    """Get current time formatted according to timezone and format."""
    if not _is_valid_timezone(timezone) or not _is_valid_timeformat(time_format):
        raise ValueError("Invalid timezone or format.")
    return datetime.now(pytz.timezone(timezone)).strftime(time_format)


async def _statdock_type_change(interaction, timezone, time_format):
    if not _is_valid_timezone(timezone) or not _is_valid_timeformat(time_format):
        raise ValueError("Invalid timezone or format.")

    tz = pytz.timezone(timezone)
    current_time = datetime.now(tz)
    return current_time.strftime(time_format)


# Discord AppCommands (/)
@discord.app_commands.command(
    name="statdock_add", description="Initializes a new stat dock."
)
@discord.app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
@discord.app_commands.checks.has_permissions(manage_guild=True, manage_channels=True)
@discord.app_commands.describe(
    category="The category you want to create the dock in.",
    frequency="The frequency in which the stat dock updates.",
    stat_type="The kind of dock, you wanna create.",
    timezone="The timezone you wanna use. - Only for type `Time` (Europe/Berlin).",
    timeformat="The time format you wanna use. - Only for type `Time` (%d.%m.%Y | %H:%M:%S)",
    countbots="Should bots be included? - Only used for type `Member in role` and `Member`.",
    countusers="Should users be included? - Only used for type `Member in role` and `Member`.",
    role="Role, whose member count should be tracked. - Only for type `Member in role`.",
    prefix="Text, that is put before the counter.",
    counttext="Include text channels. - Only used for type `Channel counter`",
    countvoice="Include voice channels. - Only used for type `Channel counter`",
    countcategory="Include category channels. - Only used for type `Channel counter`",
    countstage="Include stage channels. - Only used for type `Channel counter`",
    countforum="Include forum channels. - Only used for type `Channel counter`",
)
@discord.app_commands.choices(
    stat_type=[
        discord.app_commands.Choice(name="Time", value="time"),
        discord.app_commands.Choice(name="Member in role", value="role"),
        discord.app_commands.Choice(name="Member", value="member"),
        discord.app_commands.Choice(name="Channel counter", value="channel"),
    ],
    frequency=[  # type: ignore[arg-type]
        discord.app_commands.Choice(name="6 minutes", value=6),
        discord.app_commands.Choice(name="10 minutes", value=10),
        discord.app_commands.Choice(name="15 minutes", value=15),
        discord.app_commands.Choice(name="20 minutes", value=20),
        discord.app_commands.Choice(name="25 minutes", value=25),
        discord.app_commands.Choice(name="30 minutes", value=30),
        discord.app_commands.Choice(name="45 minutes", value=45),
        discord.app_commands.Choice(name="2 hours", value=120),
        discord.app_commands.Choice(name="3 hours", value=180),
        discord.app_commands.Choice(name="4 hours", value=240),
        discord.app_commands.Choice(name="6 hours", value=360),
        discord.app_commands.Choice(name="8 hours", value=480),
        discord.app_commands.Choice(name="12 hours", value=720),
        discord.app_commands.Choice(name="1 day", value=1440),
    ],
)
async def _statdock_add(
    interaction: discord.Interaction,
    stat_type: str,
    category: discord.CategoryChannel,
    frequency: int,
    prefix: Optional[str] = None,
    timezone: str = "Europe/Berlin",
    timeformat: str = "%H:%M",
    countbots: bool = False,
    countusers: bool = False,
    counttext: bool = False,
    countvoice: bool = False,
    countcategory: bool = False,
    countstage: bool = False,
    countforum: bool = False,
    role: Optional[discord.Role] = None,
) -> None:

    if not category:
        await interaction.response.send_message("How did we get here?", ephemeral=True)
        return

    if interaction.guild is None:
        await interaction.response.send_message(ERR_GUILD_ONLY, ephemeral=True)
        return

    if stat_type in ["role", "member"]:
        if not (countbots or countusers):
            await interaction.response.send_message(
                content="You need to enable `countbots`, `countusers`, or both, to use this stat dock.",
                ephemeral=True,
            )
            return
        if stat_type == "role":
            if role is None:
                await interaction.response.send_message(
                    content="You need to enter a role, to use this stat dock.",
                    ephemeral=True,
                )
                return
    elif stat_type == "time" and not (
        _is_valid_timezone(timezone) or _is_valid_timeformat(timeformat)
    ):
        await interaction.response.send_message(
            "You either entered a wrong timezone, or format."
        )
        return
    elif stat_type == "channel" and not (
        counttext or countvoice or countcategory or countstage or countforum
    ):
        await interaction.response.send_message(
            content="You need to enable at least one of those options to use this dock\n`counttext`, `countvoice`, `countcategory`, `countstage`, `countforum`.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        "The stat dock is being created...", ephemeral=True
    )

    # Type narrowing for stat_type
    if stat_type not in ["time", "role", "member"]:
        await interaction.edit_original_response(
            content=f"Invalid stat_type: {stat_type}"
        )
        return
    stat_type_literal: Literal["time", "role", "member"] = stat_type  # type: ignore

    try:
        created_channel = await interaction.guild.create_voice_channel(
            name="Loading...",
            category=category,
            overwrites={interaction.guild.default_role: _overwrites},
        )
    except Exception as e:
        _logger.error(e)
        await interaction.edit_original_response(
            content=f"The channel couldn't be created:\n```txt{e}```"
        )
        return

    result = await _init_dock(
        guild=interaction.guild,
        category=category,
        channel=created_channel,
        stat_type=stat_type_literal,
        timezone=timezone,
        timeformat=timeformat,
        countbots=countbots,
        countusers=countusers,
        counttext=counttext,
        countvoice=countvoice,
        countcategory=countcategory,
        countstage=countstage,
        countforum=countforum,
        role=None if not role else role,
        prefix=None if not prefix else prefix.strip(),
        frequency=frequency,
    )
    if isinstance(result, str):
        await created_channel.delete(reason="Dock creation failed!")
        await interaction.edit_original_response(
            content=f"Dock creation failed!\n```txt{result}```"
        )
    else:
        await interaction.edit_original_response(content="Stat dock created.")


@_statdock_add.autocomplete("timezone")
async def timezone_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[discord.app_commands.Choice]:
    return [
        discord.app_commands.Choice(name=tz, value=tz)
        for tz in pytz.all_timezones
        if current.lower() in tz.lower()
    ][:25]


@discord.app_commands.command(
    name="statdock_update", description="Updates a dock [enable/disable/delete/prefix]."
)
@discord.app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
@discord.app_commands.checks.has_permissions(manage_guild=True, manage_channels=True)
@discord.app_commands.describe(
    dock="The dock you want to update.",
    action="The action you wanna perform.",
    prefix="The new prefix. - Only if `action` is `prefix`. Enter `DELETE to remove.`",
)
@discord.app_commands.choices(
    action=[
        discord.app_commands.Choice(name="enable", value="enable"),
        discord.app_commands.Choice(name="disable", value="disable"),
        discord.app_commands.Choice(name="delete", value="delete"),
        discord.app_commands.Choice(name="prefix", value="prefix"),
    ]
)
async def _statdock_update(
    interaction: discord.Interaction,
    dock: discord.VoiceChannel,
    action: str,
    prefix: Optional[str] = None,
) -> None:
    await interaction.response.defer(ephemeral=True)

    is_dock = _c.execute(
        "SELECT EXISTS(SELECT 1 FROM STATDOCK WHERE `channel_id` = ?)", (dock.id,)
    ).fetchone()[0]
    if not is_dock:
        await interaction.followup.send(
            content=f"The channel {dock.mention} isn't a dock."
        )
        return

    match action:
        case "enable":
            enabled = _c.execute(
                "SELECT `enabled` FROM `STATDOCK` WHERE `channel_id` = ?", (dock.id,)
            ).fetchone()[0]
            if enabled:
                await interaction.followup.send("This dock is already enabled.")
                return
            _c.execute(
                "UPDATE `STATDOCK` SET `enabled` = 1 WHERE `channel_id` = ?", (dock.id,)
            )
            await interaction.followup.send("Dock enabled.")

        case "disable":
            enabled = _c.execute(
                "SELECT `enabled` FROM `STATDOCK` WHERE `channel_id` = ?", (dock.id,)
            ).fetchone()[0]
            if not enabled:
                await interaction.followup.send("This dock is already disabled.")
                return
            _c.execute(
                "UPDATE `STATDOCK` SET `enabled` = 0 WHERE `channel_id` = ?", (dock.id,)
            )
            await interaction.followup.send("Dock disabled.")

        case "delete":
            _c.execute(SQL_DELETE_STATDOCK_BY_CHANNEL, (dock.id,))
            await dock.delete()
            await interaction.followup.send("Dock deleted.")

        case "prefix":
            _c.execute(
                "UPDATE `STATDOCK` SET `prefix` = ? WHERE `channel_id` = ?",
                (
                    prefix if prefix != "DELETE" else None,
                    dock.id,
                ),
            )
            if prefix == "DELETE":
                await interaction.followup.send("Prefix removed.")
            else:
                await interaction.followup.send(f"Prefix changed to `{prefix}`.")

    _conn.commit()


@discord.app_commands.command(
    name="statdock_list", description="Lists every created stat dock."
)
@discord.app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def _statdock_list(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)

    if interaction.guild is None:
        await interaction.followup.send(ERR_GUILD_ONLY)
        return

    _c.execute("SELECT * FROM STATDOCK WHERE `guild_id` = ?", (interaction.guild.id,))
    data = _c.fetchall()

    if not data:
        await interaction.followup.send("No embeds found for this server.")
        return

    embeds = []
    for entry in data:
        count_type = _bitmap_handler.get_active_keys(entry[5], single=True)
        embed_color = discord.Color.green() if entry[1] else discord.Color.red()
        # Handle the case where count_type might be a list
        if isinstance(count_type, list):
            count_type_str = count_type[0] if count_type else "unknown"
        else:
            count_type_str = count_type
        embed_title = f"Embed ID: {entry[0]} - {count_type_str.capitalize()}"

        embed = discord.Embed(title=embed_title, color=embed_color)
        embed.add_field(name="Channel", value=f"<#{entry[4]}>")
        embed.add_field(name="Frequency", value=f"{entry[10]} min")
        embed.add_field(name="Last Updated", value=f"<t:{entry[11]}:F>")
        embed.add_field(name="Prefix", value=entry[9])

        match count_type:
            case ["member", "role"]:
                embed.add_field(
                    name="Count Members",
                    value=_bitmap_handler.check_key_in_bitkey("countusers", entry[12]),
                )
                embed.add_field(
                    name="Count Bots",
                    value=_bitmap_handler.check_key_in_bitkey("countbots", entry[12]),
                )
                if count_type == "role":
                    role = interaction.guild.get_role(entry[8])
                    if role:
                        embed.add_field(name="Role", value=role.mention, inline=False)
            case "time":
                embed.add_field(name="Timezone", value=entry[6])
                embed.add_field(name="Time Format", value=entry[7])
            case "channel":
                embed.add_field(
                    name="Count Text",
                    value=_bitmap_handler.check_key_in_bitkey("counttext", entry[12]),
                )
                embed.add_field(
                    name="Count Voice",
                    value=_bitmap_handler.check_key_in_bitkey("countvoice", entry[12]),
                )
                embed.add_field(
                    name="Count Category",
                    value=_bitmap_handler.check_key_in_bitkey("countcategory", entry[12]),
                )
                embed.add_field(
                    name="Count Stage",
                    value=_bitmap_handler.check_key_in_bitkey("countstage", entry[12]),
                )
                embed.add_field(
                    name="Count Forum",
                    value=_bitmap_handler.check_key_in_bitkey("countforum", entry[12]),
                )

        embeds.append(embed)

        if len(embeds) == 10:
            await interaction.followup.send(embeds=embeds)
            embeds = []

    if embeds:
        await interaction.followup.send(embeds=embeds)


@discord.app_commands.command(
    name="statdock_enable_hidden",
    description="Enables all disabled channels, that got deleted.",
)
@discord.app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def _statdock_enable_hidden(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)

    if interaction.guild is None:
        await interaction.followup.send(ERR_GUILD_ONLY)
        return

    _c.execute(
        "SELECT * FROM `STATDOCK` WHERE `enabled` = 0 AND `guild_id` = ?",
        (interaction.guild.id,),
    )
    data = _c.fetchall()
    for entry in data:
        channel = interaction.guild.get_channel(entry[4])
        if channel is not None:
            continue
        stat_type_result = _bitmap_handler.get_active_keys(entry[5], single=True)
        # Ensure stat_type is a string
        if isinstance(stat_type_result, list):
            stat_type_str = stat_type_result[0] if stat_type_result else ""
        else:
            stat_type_str = stat_type_result
        await _re_init_dock(
            guild_id=interaction.guild.id,
            category_id=entry[3],
            channel_id=entry[4],
            stat_type=stat_type_str,
            timezone=entry[6],
            timeformat=entry[7],
            counter=entry[12],
            role_id=entry[8],
            prefix=entry[9],
            ignore_none_category=True,
        )
    await interaction.followup.send("All hidden docks got enabled.")
