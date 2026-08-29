import discord
from discord.ext import commands

from _version import __version__


class GeneralCog(commands.Cog, name="General"):
    """General commands: ping, help and bot info."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check the bot's response latency."""
        latency_ms = round(self.bot.latency * 1000, 1)
        await ctx.send(f"Latency `{latency_ms} ms`")

    @commands.command(name="help", aliases=["commands", "cmds", "h"])
    async def help_cmd(self, ctx):
        """Show all available commands and their descriptions."""
        allowed = self.bot.allowed_commands
        lines = ["**Available Commands**"]
        for cog in sorted(self.bot.cogs.values(), key=lambda c: c.qualified_name):
            cmds = [c for c in cog.get_commands() if c.name in allowed]
            if not cmds:
                continue
            lines.append("")
            lines.append(f"**{cog.qualified_name}** — {cog.description or 'No description'}")
            for cmd in sorted(cmds, key=lambda c: c.name):
                lines.append(f"`!{cmd.name}` — {cmd.help or 'No description'}")
        lines.append("")
        lines.append(
            "Upload a record file and send `!analyze` to analyze it, or `!decode` to get its raw decoded contents."
        )
        await ctx.send("\n".join(lines))

    @commands.command(name="botinfo", aliases=["info", "about"])
    async def botinfo(self, ctx):
        """Show bot version, proxy and command information."""
        proxy_state = (
            f"Enabled (`{self.bot.proxy_url}`)"
            if self.bot.proxy_enabled
            else "Not enabled"
        )
        embed = discord.Embed(
            title="ADOFAI Offset Analyzer Bot",
            description=(
                "Upload `.tlog` / `.json` / `.crpl2` record files to generate offset analysis charts and statistics."
            ),
            color=0x3498DB,
        )
        embed.add_field(name="Version", value=f"`v{__version__}`", inline=True)
        embed.add_field(
            name="Analyzer", value="`offset_analyzer`", inline=True
        )
        embed.add_field(
            name="Proxy", value=proxy_state, inline=True
        )
        embed.add_field(
            name="Allowed Commands",
            value=str(len(self.bot.allowed_commands)),
            inline=True,
        )
        embed.set_footer(text="Command Prefix: " + self.bot.command_prefix)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(GeneralCog(bot))
