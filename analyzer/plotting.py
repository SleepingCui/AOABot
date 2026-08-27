import math

import matplotlib.pyplot as plt
import numpy as np

from .constants import MARGIN_MAP, DISPLAY_ORDER, JD_WEIGHTS
from .text_report import generate_info_txt

plt.style.use("dark_background")
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial"]
plt.rcParams["axes.unicode_minus"] = False


def draw_scatter(ax, meta, stats, outlier_quantile=0.005):
  offsets = meta["offsets"]
  if not offsets:
    return
  
  y_all = [
      item[0]
      for item in offsets
      if not math.isnan(item[0]) and item[1] not in (8, 9)
  ]
  if not y_all:
    y_all = [item[0] for item in offsets if not math.isnan(item[0])]

  if len(y_all) > 10:
    q_low = np.percentile(y_all, outlier_quantile * 100)
    q_high = np.percentile(y_all, (1 - outlier_quantile) * 100)
    margin = max(abs(q_low), abs(q_high), 25) * 1.35
    y_min, y_max = -margin, margin
  else:
    y_min, y_max = -100, 100

  ignored_count = sum(
      1
      for item in offsets
      if not math.isnan(item[0]) and (item[0] < y_min or item[0] > y_max)
  )

  by_type = {i: {"x": [], "y": []} for i in DISPLAY_ORDER}
  running_x, running_y = [], []
  r_sum, r_cnt = 0.0, 0

  for idx, item in enumerate(offsets):
    x = idx + 1
    y = item[0]
    m_type = item[1]

    if m_type in by_type:
      by_type[m_type]["x"].append(x)
      by_type[m_type]["y"].append(y)

    if not math.isnan(y):
      r_sum += y
      r_cnt += 1
      running_x.append(x)
      running_y.append(r_sum / r_cnt)

  total_pts = len(offsets)
  pt_size = max(3.5, min(10.0, 3500.0 / max(total_pts, 1)))
  alpha_val = max(0.65, min(0.95, 2500.0 / max(total_pts, 1)))

  for code in DISPLAY_ORDER:
    if (code in (10, 12)) and stats["counts"][code] == 0:
      continue
    data = by_type[code]
    if data["x"]:
      ax.scatter(
          data["x"],
          data["y"],
          c=MARGIN_MAP[code]["color"],
          label=MARGIN_MAP[code]["label"],
          s=pt_size,
          alpha=alpha_val,
          edgecolors="none",
          zorder=3,
      )

  if running_x:
    ax.plot(
        running_x,
        running_y,
        color="#FFD700",
        linewidth=1.5,
        label="Avg Curve",
        zorder=5,
    )

  ax.axhline(0, color="#FFFFFF", linestyle="-", linewidth=0.8, alpha=0.4)
  mean_val = stats["mean"]
  ax.axhline(
      mean_val,
      color="#FFD700",
      linestyle="--",
      linewidth=1.2,
      label=f"Avg: {mean_val:+.2f}ms",
      zorder=6,
  )

  ax.set_ylim(y_min, y_max)

  info_text = (
      f"Total Hits: {total_pts:,}\n"
      f"Mean: {stats['mean']:+.2f} ms\n"
      f"StdDev: {stats['stdDev']:.2f} ms\n"
      f"Ignored Outliers: {ignored_count} pts"
  )

  ax.text(
      0.98,
      0.04,
      info_text,
      transform=ax.transAxes,
      fontsize=8,
      color="#E0E0E0",
      verticalalignment="bottom",
      horizontalalignment="right",
      bbox=dict(
          boxstyle="round,pad=0.5",
          facecolor="#121212",
          alpha=0.6,
          edgecolor="#333333",
          linewidth=0.8,
      ),
      zorder=10,
  )

  ax.set_title("Offset Scatter Plot", color="white", fontsize=12)
  ax.set_xlabel("Hits", color="#aaa", fontsize=10)
  ax.set_ylabel("Offset (ms)", color="#aaa", fontsize=10)
  ax.grid(True, color="#2A2A2A", linestyle=":", alpha=0.6)

  ax.legend(
      loc="upper right",
      fontsize=8,
      framealpha=0.6,
      facecolor="#121212",
      edgecolor="none",
  )


def draw_distribution(ax, meta, stats, outlier_quantile=0.005):
  valid_offsets = [
      item[0]
      for item in meta["offsets"]
      if not math.isnan(item[0]) and item[1] not in (8, 9)
  ]
  if not valid_offsets:
    valid_offsets = [
        item[0] for item in meta["offsets"] if not math.isnan(item[0])
    ]

  if not valid_offsets:
    return

  if len(valid_offsets) > 10:
    q_low = np.percentile(valid_offsets, outlier_quantile * 100)
    q_high = np.percentile(valid_offsets, (1 - outlier_quantile) * 100)
    margin = max(abs(q_low), abs(q_high), 25) * 1.35
    x_min, x_max = -margin, margin
  else:
    x_min, x_max = -100, 100

  ignored_count = sum(
      1
      for item in meta["offsets"]
      if not math.isnan(item[0]) and (item[0] < x_min or item[0] > x_max)
  )
  filtered_data = [x for x in valid_offsets if x_min <= x <= x_max]

  counts, bins, patches = ax.hist(
      filtered_data,
      bins=60,
      range=(x_min, x_max),
      color="#4CAF50",
      alpha=0.6,
      edgecolor="#4CAF50",
      density=False,
  )

  mean, std = stats["mean"], stats["stdDev"]
  if std > 0:
    max_c = max(counts) if len(counts) > 0 else 1
    x_vals = np.linspace(x_min, x_max, 200)

    def gaussian(x):
      return (1.0 / (std * math.sqrt(2 * math.pi))) * np.exp(
          -0.5 * ((x - mean) / std) ** 2
      )

    max_pdf = gaussian(mean)
    scale = max_c / max_pdf if max_pdf > 0 else 1.0
    y_vals = gaussian(x_vals) * scale

    ax.plot(x_vals, y_vals, color="#ffb74d", linewidth=2, label="Normal Fit")
    ax.axvline(
        mean + std, color="#4FC3F7", linestyle="--", linewidth=1, label="+1σ"
    )
    ax.axvline(
        mean - std, color="#4FC3F7", linestyle="--", linewidth=1, label="-1σ"
    )

  ax.axvline(
      mean,
      color="#ffb74d",
      linestyle="--",
      linewidth=1.5,
      label=f"μ = {mean:.2f}",
  )
  ax.set_xlim(x_min, x_max)

  info_text = (
      f"Total Hits: {stats['totalHits']:,}\n"
      f"Mean (μ): {stats['mean']:+.2f} ms\n"
      f"Std Dev (σ): {stats['stdDev']:.2f} ms\n"
      f"UR: {stats['ur']:.2f}\n"
      f"Ignored Outliers: {ignored_count} pts"
  )

  ax.text(
        0.98,
        0.96,
        info_text,
        transform=ax.transAxes,
        fontsize=8,
        color="#E0E0E0",
        verticalalignment="top", 
        horizontalalignment="right",
        bbox=dict(
            boxstyle="round,pad=0.5",
            facecolor="#121212",
            alpha=0.6,
            edgecolor="#333333",
            linewidth=0.8,
        ),
        zorder=10,
    )

  ax.set_title("Normal Distribution", color="white", fontsize=12)
  ax.set_xlabel("Offset (ms)", color="#aaa", fontsize=10)
  ax.set_ylabel("Frequency", color="#aaa", fontsize=10)
  ax.grid(True, color="#252525", linestyle=":", alpha=0.6)
  ax.legend(loc="upper left", fontsize=8, framealpha=0.3)


def draw_pie(ax, meta, stats, is_combined=False):
  counts = stats["counts"]
  raw_groups = {
      "Too Early": (counts[0], "#FF2A2A"),
      "Very Early/Late": (counts[1] + counts[5], "#FF8C55"),
      "Early/Late Perfect": (counts[2] + counts[4], "#B8FF36"),
      "Perfect": (counts[3], "#00FF66"),
      "XPerfect": (counts[12], "#38E8FF"),
      "Auto": (counts[10], "#FFFFFF"),
      "Multipress": (counts[7], "#00FFFF"),
      "Overload/Miss": (counts[8] + counts[9], "#E56BFF"),
  }

  labels, values, colors = [], [], []
  total_hits = stats["totalHits"]
  if total_hits == 0:
    return

  legend_labels = []
  for k, (cnt, col) in raw_groups.items():
    if k in ("XPerfect", "Auto") and cnt == 0:
      continue
    if cnt > 0:
      labels.append(k)
      values.append(cnt)
      colors.append(col)
      pct = (cnt / total_hits) * 100.0
      legend_labels.append(f"{k:<18}: {cnt:,} ({pct:.1f}%)")

  if not values: return

  wedges, _ = ax.pie(
      values,
      colors=colors,
      startangle=140,
      radius=0.8,
      center=(0, 0),
      wedgeprops=dict(edgecolor="#121212", linewidth=1.2),
  )

  if is_combined:
    ax.legend(
        wedges,
        legend_labels,
        loc="lower right", 
        bbox_to_anchor=(1.05, -0.05),
        fontsize=6.5,  
        framealpha=0.6,
        facecolor="#121212",
        edgecolor="#333333",
        prop={"family": "monospace", "size": 6.5},  
    )
  else:
    fig = ax.get_figure()
    fig.legend(
        wedges,
        legend_labels,
        loc="lower right",  
        bbox_to_anchor=(0.98, 0.02),  
        bbox_transform=fig.transFigure,
        fontsize=7, 
        framealpha=0.6,
        facecolor="#121212",
        edgecolor="#333333",
        prop={"family": "monospace", "size": 7},
    )

  ax.set_title("Judgment Breakdown", color="white", fontsize=12)


def draw_xacc(ax, meta, stats):
  offsets = meta["offsets"]
  valid_types = [0, 1, 2, 3, 4, 5, 8, 9, 12, 10]

  xacc_data = []
  running_sum = 0.0
  running_cnt = 0

  for item in offsets:
    t = item[1]
    if t in valid_types:
      if t in (8, 9):
        w = JD_WEIGHTS["failMiss"]
      elif t == 0:
        w = JD_WEIGHTS["tooEarly"]
      elif t == 1:
        w = JD_WEIGHTS["early"]
      elif t == 2:
        w = JD_WEIGHTS["ePerfect"]
      elif t == 3:
        w = JD_WEIGHTS["perfect"]
      elif t == 12:
        w = JD_WEIGHTS["xPerfect"]
      elif t == 10:
        w = JD_WEIGHTS["auto"]
      elif t == 4:
        w = JD_WEIGHTS["lPerfect"]
      elif t == 5:
        w = JD_WEIGHTS["late"]
      else:
        w = 0.0

      running_sum += w
      running_cnt += 1
      xacc_data.append((running_sum / running_cnt) * 100.0)

  if not xacc_data:
    return

  x_vals = list(range(1, len(xacc_data) + 1))
  min_acc = min(xacc_data)

  if min_acc >= 98.0:
    y_min = max(0.0, min_acc - 0.2)
  elif min_acc >= 90.0:
    y_min = max(0.0, min_acc - 1.0)
  else:
    y_min = max(0.0, min_acc - 5.0)

  y_max = 100.15
  ax.set_ylim(y_min, y_max)
  ax.set_xlim(1, len(xacc_data))
  ax.plot(x_vals, xacc_data, color="#38E8FF", linewidth=1.8, zorder=4)
  ax.fill_between(x_vals, xacc_data, y_min, color="#38E8FF", alpha=0.12)

  final_xacc = xacc_data[-1]
  ax.set_title(
      f"XACC Trend ({final_xacc:.2f}%)", color="white", fontsize=12
  )
  ax.set_xlabel("Hits", color="#aaa", fontsize=10)
  ax.set_ylabel("XACC (%)", color="#aaa", fontsize=10)
  ax.grid(True, color="#2A2A2A", linestyle=":", alpha=0.6)


DRAW_MAP = {
    "scatter": draw_scatter,
    "dist": draw_distribution,
    "pie": draw_pie,
    "xacc": draw_xacc,
}


def draw_info(ax, meta, stats):
  ax.axis("off")

  txt_content = generate_info_txt(meta, stats, max_width=110)

  ax.text(
      0.02,
      0.98,
      txt_content,
      transform=ax.transAxes,
      fontsize=8,  
      color="#E0E0E0",
      family="monospace", 
      verticalalignment="top",
      horizontalalignment="left",
      bbox=dict(
          boxstyle="round,pad=0.6",
          facecolor="#121212",
          alpha=0.7,
          edgecolor="#333333",
          linewidth=0.8,
      ),
  )
