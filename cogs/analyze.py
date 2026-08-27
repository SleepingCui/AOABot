import io

import discord
from discord.ext import commands

from services.analyzer import VALID_CHART_TYPES, build_report_async

VALID_EXTENSIONS = (".tlog", ".gz", ".json", ".crpl2")


class AnalyzeCog(commands.Cog, name="Analyze"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="analyze", aliases=["an", "adofai"])
    async def analyze_record(self, ctx, chart_type: str = "combined"):
        chart_type = chart_type.lower()
        if chart_type not in VALID_CHART_TYPES:
            await ctx.send(
                f"Unknown chart type `{chart_type}`. Available: `{', '.join(VALID_CHART_TYPES)}`"
            )
            return

        if not ctx.message.attachments:
            await ctx.send(
                "**Please upload the play record file when sending the command** (supported: `.tlog` / `.gz` / `.json` / `.crpl2`)"
            )
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith(VALID_EXTENSIONS):
            await ctx.send(
                f"Unsupported file format! Only supported: `{', '.join(VALID_EXTENSIONS)}`"
            )
            return


        status_msg = await ctx.send("Parsing, please wait...")
        try:
            file_bytes = await attachment.read()
            result = await build_report_async(
                file_bytes, attachment.filename, chart_type
            )
        except ValueError as e:
            await status_msg.edit(content=f"**Parse failed**: `{e}`")
            return
        except Exception as e:
            await status_msg.edit(content=f"**An error occurred**: `{e}`")
            return

        meta, stats = result["meta"], result["stats"]

        if result["png"] is None:
            txt_file = discord.File(
                fp=io.BytesIO(result["txt"].encode("utf-8")),
                filename=f"{meta.get('songName', 'report')}_info.txt",
            )
            await status_msg.edit(
                content=f"📊 **{meta.get('songName', 'Unknown')}**"
            )
            await ctx.send(file=txt_file)
            return

        files_to_send = [
            discord.File(
                fp=io.BytesIO(result["txt"].encode("utf-8")),
                filename="analysis_report.txt",
            ),
            discord.File(
                fp=result["png"], filename=f"chart_{result['chart_type']}.png"
            ),
        ]

        embed = discord.Embed(
            title=f"🎵 {meta.get('songName', 'Unknown Level')}",
            description=f"**Version**: `{meta.get('versionText', 'N/A')}`",
            color=0x3498DB,
        )
        embed.add_field(
            name="Total Hits",
            value=f"{stats.get('totalHits', 0):,}",
            inline=True,
        )
        embed.add_field(
            name="UR (Unstable Rate)",
            value=f"{stats.get('ur', 0):.2f}",
            inline=True,
        )
        embed.add_field(
            name="XACC", value=f"{stats.get('xacc', 0):.2f}%", inline=True
        )
        embed.add_field(
            name="Mean", value=f"{stats.get('mean', 0):.2f} ms", inline=True
        )
        embed.add_field(
            name="StdDev", value=f"{stats.get('stdDev', 0):.2f} ms", inline=True
        )
        embed.add_field(
            name="Max Combo", value=str(stats.get("maxCombo", 0)), inline=True
        )

        await status_msg.delete()
        await ctx.send(embed=embed, files=files_to_send)


async def setup(bot):
    await bot.add_cog(AnalyzeCog(bot))
