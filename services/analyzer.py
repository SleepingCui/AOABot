
import asyncio
import io
import logging
from datetime import datetime

import matplotlib.pyplot as plt

from analyzer import analyze, generate_info_txt

logger = logging.getLogger(__name__)
from analyzer.plotting import (
    draw_distribution,
    draw_info,
    draw_pie,
    draw_scatter,
    draw_xacc,
)

from utils.files import temp_record_file

VALID_CHART_TYPES = ("combined", "scatter", "dist", "pie", "xacc", "txt")

SINGLE_CHART_MAP = {
    "scatter": draw_scatter,
    "dist": draw_distribution,
    "pie": draw_pie,
    "xacc": draw_xacc,
}


def _render_combined(meta, stats):
    auto_width = max(16, min(50, len(meta["offsets"]) / 100))
    fig = plt.figure(figsize=(auto_width, 13), facecolor="#1e1e1e")

    ts_str = (
        datetime.fromtimestamp(meta["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        if meta.get("timestamp")
        else "Unknown"
    )
    song_name = meta.get("songName") or "Unknown"
    fig.suptitle(
        f"{ts_str} - {song_name}",
        color="white",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )

    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.2])

    ax_scatter = fig.add_subplot(gs[0, :], facecolor="#0a0a0a")
    draw_scatter(ax_scatter, meta, stats)

    ax_xacc = fig.add_subplot(gs[1, :], facecolor="#0a0a0a")
    draw_xacc(ax_xacc, meta, stats)

    ax_dist = fig.add_subplot(gs[2, 0], facecolor="#0a0a0a")
    draw_distribution(ax_dist, meta, stats)

    gs_right = gs[2, 1].subgridspec(1, 2, width_ratios=[1, 1])
    ax_info = fig.add_subplot(gs_right[0, 0], facecolor="#0a0a0a")
    draw_info(ax_info, meta, stats)
    ax_pie = fig.add_subplot(gs_right[0, 1], facecolor="#0a0a0a")
    draw_pie(ax_pie, meta, stats, is_combined=True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return buffer


def _render_single(chart_type, meta, stats):
    fig, ax = plt.subplots(figsize=(12, 5), facecolor="#1e1e1e")
    ax.set_facecolor("#0a0a0a")
    SINGLE_CHART_MAP[chart_type](ax, meta, stats)

    plt.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return buffer


def build_report(file_bytes: bytes, filename: str, chart_type: str = "combined"):
    chart_type = chart_type.lower()
    if chart_type not in VALID_CHART_TYPES:
        raise ValueError(
            f"Unknown chart type `{chart_type}`. Available: `{', '.join(VALID_CHART_TYPES)}`"
        )

    logger.info("%s (chart=%s)", filename, chart_type)

    with temp_record_file(file_bytes, filename) as tmp_path:
        meta, stats = analyze(tmp_path)

    info_txt = generate_info_txt(meta, stats)

    if chart_type == "txt":
        return {
            "meta": meta,
            "stats": stats,
            "txt": info_txt,
            "png": None,
            "chart_type": chart_type,
        }

    png_buffer = (
        _render_combined(meta, stats)
        if chart_type == "combined"
        else _render_single(chart_type, meta, stats)
    )

    return {
        "meta": meta,
        "stats": stats,
        "txt": info_txt,
        "png": png_buffer,
        "chart_type": chart_type,
    }


async def build_report_async(file_bytes: bytes, filename: str, chart_type: str = "combined"):
    return await asyncio.to_thread(build_report, file_bytes, filename, chart_type)
