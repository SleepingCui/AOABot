import logging

from discord.ext import commands

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog, name="Admin"):
    """Owner-only administration commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cmd(self, ctx):
        """Reload all extensions, hot-loading any newly added ones."""
        from main import discover_extensions, validate_command_descriptions

        newly_loaded = []
        for ext in discover_extensions():
            try:
                if ext in self.bot.extensions:
                    await self.bot.reload_extension(ext)
                else:
                    await self.bot.load_extension(ext)
                    newly_loaded.append(ext)
            except Exception as e:
                logger.exception("Failed to reload extension: %s", ext)
                await ctx.send(f"Failed to reload `{ext}`: `{e}`")
                return

        try:
            validate_command_descriptions(self.bot)
        except RuntimeError as e:
            for ext in newly_loaded:
                await self.bot.unload_extension(ext)
            logger.error("Reload rejected: %s", e)
            await ctx.send(f"Reload rejected: `{e}`")
            return

        await ctx.send("All extensions reloaded.")

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown_cmd(self, ctx):
        """Stop the bot and close the connection."""
        await ctx.send("Shutting down the bot...")
        await self.bot.close()


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
