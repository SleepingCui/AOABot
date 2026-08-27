import argparse
import os
import sys
from datetime import datetime

import matplotlib.pyplot as plt

from analyzer.parsing import load_file
from analyzer.stats import calculate_stats
from analyzer.text_report import generate_info_txt
from analyzer.plotting import (
    DRAW_MAP,
    draw_scatter,
    draw_distribution,
    draw_pie,
    draw_xacc,
    draw_info,
)


def main():
  parser = argparse.ArgumentParser(
      description="ADOFAI Offset Analyzer CLI"
  )
  parser.add_argument(
      "file", help="Input play record file (.tlog, .gz, .json, .crpl2)"
  )
  parser.add_argument(
      "-o",
      "--output",
      default="output",
      help="Output file path name prefix (default: output)",
  )
  parser.add_argument(
      "-c",
      "--charts",
      nargs="+",
      choices=["scatter", "dist", "pie", "xacc"],
      default=["scatter", "dist", "pie", "xacc"],
      help="Chart types to generate (default: all of scatter dist pie xacc)",
  )
  parser.add_argument(
      "--combined",
      action="store_true",
      help="Combine all selected charts into a single large output image",
  )
  parser.add_argument(
      "--txt", action="store_true", help="Generate basic info text file (.txt)"
  )

  args = parser.parse_args()

  if not os.path.exists(args.file):
    print(f"Error: file '{args.file}' does not exist!")
    sys.exit(1)

  print(f"Reading and parsing file: {args.file} ...")
  try:
    meta = load_file(args.file)
  except Exception as e:
    print(f"Failed to parse file: {e}")
    sys.exit(1)

  stats = calculate_stats(meta)
  print("Parsing complete")

  if args.txt:
    txt_content = generate_info_txt(meta, stats)
    txt_file = f"{args.output}_info.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
      f.write(txt_content)
    print(f"Info text exported to: {txt_file}")

  charts_to_draw = [c for c in args.charts if c in DRAW_MAP]
  if not charts_to_draw:
    return

  total_hits = stats["totalHits"]
  auto_width = min(50.0, max(14.0, 10.0 + (total_hits / 500.0) * 2.5))

  if args.combined:
    fig = plt.figure(figsize=(auto_width, 13), facecolor='#1e1e1e')

    ts_str = (
        datetime.fromtimestamp(meta['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        if meta.get('timestamp')
        else 'Unknown'
    )
    song_name = meta.get('songName') or 'Unknown'

    title_text = f'{ts_str} - {song_name}'
    fig.suptitle(
        title_text,
        color='white',
        fontsize=16,
        fontweight='bold',
        y=0.98,  
    )

    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.2])

    if 'scatter' in charts_to_draw:
        ax_scatter = fig.add_subplot(gs[0, :], facecolor='#0a0a0a')
        draw_scatter(ax_scatter, meta, stats)
    if 'xacc' in charts_to_draw:
        ax_xacc = fig.add_subplot(gs[1, :], facecolor='#0a0a0a')
        draw_xacc(ax_xacc, meta, stats)
    if 'dist' in charts_to_draw:
        ax_dist = fig.add_subplot(gs[2, 0], facecolor='#0a0a0a')
        draw_distribution(ax_dist, meta, stats)
    if 'pie' in charts_to_draw:
        gs_right = gs[2, 1].subgridspec(1, 2, width_ratios=[1, 1])
        ax_info = fig.add_subplot(gs_right[0, 0], facecolor='#0a0a0a')

        draw_info(ax_info, meta, stats)
        ax_pie = fig.add_subplot(gs_right[0, 1], facecolor='#0a0a0a')
        draw_pie(ax_pie, meta, stats, is_combined=True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    out_img = f'{args.output}_combined.png'
    plt.savefig(out_img, dpi=150)
    plt.close()
    print(f'Saved to: {out_img}')

  else:
    for chart_key in charts_to_draw:
      fig_w = auto_width if chart_key in ("scatter", "xacc") else 8.0
      fig, ax = plt.subplots(figsize=(fig_w, 5), facecolor="#1e1e1e")
      ax.set_facecolor("#0a0a0a")

      DRAW_MAP[chart_key](ax, meta, stats)

      plt.tight_layout()
      out_img = f"{args.output}_{chart_key}.png"
      plt.savefig(out_img, dpi=150)
      plt.close()
      print(f"Saved to: {out_img}")


if __name__ == "__main__":
  main()
