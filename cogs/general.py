import discord
from discord.ext import commands

from _version import __version__


class GeneralCog(commands.Cog, name="General"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        latency_ms = round(self.bot.latency * 1000, 1)
        await ctx.send(f"Latency `{latency_ms} ms`")

    @commands.command(name="help", aliases=["commands", "cmds", "h"])
    async def help_cmd(self, ctx):
        allowed = self.bot.allowed_commands
        lines = ["**Available Commands**", "", "```"]
        for cmd in sorted(self.bot.commands, key=lambda c: c.name):
            if cmd.name not in allowed:
                continue
            brief = (cmd.help or "").splitlines()[0]
            lines.append(f"!{cmd.name:<10} {brief}")
        lines.append("```")
        lines.append("Upload a record file and send `!analyze` to start analyzing.")
        await ctx.send("\n".join(lines))

    @commands.command(name="botinfo", aliases=["info", "about"])
    async def botinfo(self, ctx):
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
