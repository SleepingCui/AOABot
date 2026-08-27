import math

from .constants import JD_WEIGHTS


def calculate_stats(meta):
  offsets = meta["offsets"]
  total_hits = len(offsets)
  valid_offsets = [item[0] for item in offsets if not math.isnan(item[0])]
  n = len(valid_offsets)

  mean = sum(valid_offsets) / n if n > 0 else 0.0
  var = sum((x - mean) ** 2 for x in valid_offsets) / n if n > 0 else 0.0
  std_dev = math.sqrt(var)
  ur = std_dev * 10.0

  counts = {i: 0 for i in range(13)}
  for item in offsets:
    counts[item[1]] += 1

  perf = counts[3]
  xperf = counts[12]
  auto = counts[10]

  num_std = perf + xperf + auto
  den_std = total_hits - num_std
  ratio_std = (
      f"{num_std/den_std:.2f}:1"
      if den_std > 0
      else ("∞:1" if num_std > 0 else "0:1")
  )

  num_x = xperf + auto
  den_x = total_hits - num_x
  ratio_x = (
      f"{num_x/den_x:.2f}:1"
      if den_x > 0
      else ("∞:1" if num_x > 0 else "0:1")
  )

  max_combo, cur_combo = 0, 0
  for item in offsets:
    if item[1] in (3, 12, 10):
      cur_combo += 1
      max_combo = max(max_combo, cur_combo)
    else:
      cur_combo = 0

  fail_miss_sum = counts[8] + counts[9]
  judgements = [
      fail_miss_sum,
      counts[0],
      counts[1],
      counts[2],
      counts[3] + counts[12] + counts[10],
      counts[4],
      counts[5],
  ]
  keys = [
      "failMiss",
      "tooEarly",
      "early",
      "ePerfect",
      "perfect",
      "lPerfect",
      "late",
  ]
  weighted_sum = sum(judgements[i] * JD_WEIGHTS[keys[i]] for i in range(7))
  xacc = (weighted_sum / total_hits * 100.0) if total_hits > 0 else 0.0

  skewness = (
      sum(((x - mean) / std_dev) ** 3 for x in valid_offsets) / n
      if n > 0 and std_dev > 0
      else 0.0
  )
  kurtosis = (
      sum(((x - mean) / std_dev) ** 4 for x in valid_offsets) / n - 3.0
      if n > 0 and std_dev > 0
      else 0.0
  )

  return {
      "totalHits": total_hits,
      "maxCombo": max_combo,
      "mean": mean,
      "stdDev": std_dev,
      "ur": ur,
      "ratioStd": ratio_std,
      "ratioX": ratio_x,
      "xacc": xacc,
      "counts": counts,
      "skewness": skewness,
      "kurtosis": kurtosis,
  }
