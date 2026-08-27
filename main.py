import asyncio
import discord
from discord.ext import commands

from config import load_config

COGS = ("cogs.analyze", "cogs.general", "cogs.admin")


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


async def _async_main(config):
    bot = build_bot(config)

    for ext in COGS:
        await bot.load_extension(ext)

    @bot.event
    async def on_ready():
        print(f"Bot logged in successfully: {bot.user.name} (ID: {bot.user.id})")
        if bot.proxy_enabled:
            print(f"  Proxy enabled: {bot.proxy_url}")

    await bot.start(config.token)


def main():
    config = load_config()
    asyncio.run(_async_main(config))


if __name__ == "__main__":
    main()
