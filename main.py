import asyncio
import discord
import logging
import os
from discord.ext import commands

from config import load_config

logging.basicConfig(level=logging.INFO, format = "%(asctime)s %(levelname)-8s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def discover_extensions() -> tuple[str, ...]:
    """Auto-discover every cog module under the cogs/ directory."""
    cogs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cogs")
    return tuple(
        f"cogs.{name[:-3]}"
        for name in sorted(os.listdir(cogs_dir))
        if name.endswith(".py") and name != "__init__.py"
    )


def build_bot(config):
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(
        command_prefix=config.prefix,
        intents=intents,
        help_command=None, 
        proxy=config.proxy.url if config.proxy.enabled else None,
        owner_ids=set(config.owner_ids) if config.owner_ids else None,
    )

    bot.allowed_commands = config.allowed_set
    bot.proxy_enabled = config.proxy.enabled
    bot.proxy_url = config.proxy.url

    @bot.check
    async def whitelist_check(ctx):
        if ctx.command is None:
            return True
        return ctx.command.name in config.allowed_set

    return bot


def validate_command_descriptions(bot):
    """Refuse to start unless every cog and command has a description."""
    missing = []
    for name, cog in bot.cogs.items():
        if not (cog.description or "").strip():
            missing.append(f"cog '{name}'")
    for cmd in bot.commands:
        if not (cmd.help or "").strip():
            missing.append(f"command '!{cmd.name}'")
    if missing:
        raise RuntimeError(
            "Refusing to load: missing descriptions for: " + ", ".join(missing)
        )


async def _async_main(config):
    bot = build_bot(config)

    for ext in discover_extensions():
        try:
            await bot.load_extension(ext)
        except Exception:
            logger.exception("Failed to load extension: %s", ext)
            raise
        logger.info("Loaded extension: %s", ext)

    validate_command_descriptions(bot)

    @bot.event
    async def on_ready():
        logger.info("Bot logged in successfully: %s (ID: %s)", bot.user.name, bot.user.id)
        if bot.proxy_enabled:
            logger.info("Proxy enabled: %s", bot.proxy_url)

    await bot.start(config.token)


def main():
    config = load_config()
    try:
        asyncio.run(_async_main(config))
    except RuntimeError as e:
        logger.error("Startup aborted: %s", e)


if __name__ == "__main__":
    main()
