import asyncio
import io
import logging
import os

import discord
from discord.ext import commands

from analyzer import decode_file
from services.analyzer import VALID_CHART_TYPES, build_report_async

logger = logging.getLogger(__name__)

VALID_EXTENSIONS = (".tlog", ".gz", ".json", ".crpl2")
DECODE_EXTENSIONS = (".tlog", ".gz", ".crpl2")


class AnalyzeCog(commands.Cog, name="Analyze"):
    """ADOFAI record analysis commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="analyze", aliases=["an", "adofai"])
    async def analyze_record(self, ctx, chart_type: str = "combined"):
        """Analyze an uploaded play record file and generate offset charts."""
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
        logger.info("%s requested analysis: %s (chart=%s) in %s",ctx.author, attachment.filename, chart_type, ctx.channel,)
        try:
            file_bytes = await attachment.read()
            result = await build_report_async(
                file_bytes, attachment.filename, chart_type
            )
        except ValueError as e:
            logger.warning("Parse failed for %s: %s", attachment.filename, e)
            await status_msg.edit(content=f"**Parse failed**: `{e}`")
            return
        except Exception as e:
            logger.exception("Err analyzing %s (chart=%s)", attachment.filename, chart_type)
            await status_msg.edit(content=f"**An error occurred**: `{e}`")
            return

        meta, stats = result["meta"], result["stats"]
        logger.info(f"done: {attachment.filename}")

        if result["png"] is None:
            txt_file = discord.File(
                fp=io.BytesIO(result["txt"].encode("utf-8")),
                filename=f"{meta.get('songName', 'report')}_info.txt",
            )
            await status_msg.edit(
                content=f"**{meta.get('songName', 'Unknown')}**"
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
            title={meta.get('songName', 'Unknown Level')},
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

    @commands.command(name="decode", aliases=["dc"])
    async def decode_record(self, ctx):
        """Decode an uploaded tlog/tlog.gz/crpl2 file and return its raw JSON."""
        if not ctx.message.attachments:
            await ctx.send(
                "**Please upload the play record file when sending the command** "
                "(supported: `.tlog` / `.tlog.gz` / `.crpl2`)"
            )
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith(DECODE_EXTENSIONS):
            await ctx.send(
                f"Unsupported file format! Only supported: `{' / '.join(DECODE_EXTENSIONS)}`"
            )
            return

        status_msg = await ctx.send("Decoding, please wait...")
        logger.info("%s requested decode: %s in %s", ctx.author, attachment.filename, ctx.channel)
        try:
            file_bytes = await attachment.read()
            result = await asyncio.to_thread(
                decode_file, file_bytes, attachment.filename
            )
        except ValueError as e:
            logger.warning("Decode failed for %s: %s", attachment.filename, e)
            await status_msg.edit(content=f"**Decode failed**: `{e}`")
            return
        except Exception as e:
            logger.exception("Err decoding %s", attachment.filename)
            await status_msg.edit(content=f"**An error occurred**: `{e}`")
            return

        meta = result["meta"]
        base = os.path.splitext(attachment.filename)[0]
        json_file = discord.File(
            fp=io.BytesIO(result["text"].encode("utf-8")),
            filename=f"{base}_decoded.json",
        )
        await status_msg.edit(
            content=(
                f"Done — `{attachment.filename}`\n"
                f"Song: `{meta.get('songName', 'Unknown')}` | "
                f"Format: `{meta.get('versionText', 'N/A')}` | "
                f"Entries: `{meta.get('total', 0):,}`"
            )
        )
        await ctx.send(file=json_file)


async def setup(bot):
    await bot.add_cog(AnalyzeCog(bot))
