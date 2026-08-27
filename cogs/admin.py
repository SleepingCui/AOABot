from discord.ext import commands

class AdminCog(commands.Cog, name="Admin"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_cmd(self, ctx):
        """Reload all extensions (cogs)."""
        for ext in list(self.bot.extensions):
            try:
                await self.bot.reload_extension(ext)
            except Exception as e:
                await ctx.send(f"Failed to reload `{ext}`: `{e}`")
                return
        await ctx.send("All extensions reloaded.")

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown_cmd(self, ctx):
        await ctx.send("Shutting down the bot...")
        await self.bot.close()


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
