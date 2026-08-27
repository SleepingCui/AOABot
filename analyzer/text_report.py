import textwrap
from datetime import datetime

from .constants import MARGIN_MAP, DISPLAY_ORDER


def generate_info_txt(meta, stats, max_width=38):
  ts_str = (
      datetime.fromtimestamp(meta["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
      if meta["timestamp"]
      else "Unknown"
  )

  def wrap_field(label, val):
    prefix = f"{label:<14}: "
    indent = " " * len(prefix)
    wrapped = textwrap.wrap(str(val), width=max_width)
    if not wrapped:
      return prefix
    lines = [prefix + wrapped[0]]
    for w in wrapped[1:]:
      lines.append(indent + w)
    return "\n".join(lines)

  lines = [
      "================ Metadata ================",
      f"Version       : {meta['versionText']}",
      wrap_field("Song Name", meta["songName"]),
      wrap_field("Level Path", meta["levelPath"]),
      f"Analysis Time : {ts_str}",
      "",
      "================ Stats ================",
      f"Total Hits    : {stats['totalHits']:,}",
      f"Max Combo     : {stats['maxCombo']}",
      f"UR            : {stats['ur']:.2f}",
      f"Ratio         : {stats['ratioStd']}",
      f"XRatio        : {stats['ratioX']}",
      f"XACC          : {stats['xacc']:.2f}%",
      f"Mean (μ)      : {stats['mean']:.2f} ms",
      f"Std Dev (σ)   : {stats['stdDev']:.2f} ms",
      f"Skewness      : {stats['skewness']:.3f}",
      f"Kurtosis      : {stats['kurtosis']:.3f}",
      "",
      "============ Judgements ============",
  ]

  for code in DISPLAY_ORDER:
    cnt = stats["counts"][code]
    if code in (10, 12) and cnt == 0:
      continue
    label = MARGIN_MAP[code]["label"]
    lines.append(f"{label:<18}: {cnt:,}")

  return "\n".join(lines)
