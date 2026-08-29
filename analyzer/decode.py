import gzip
import json

from .parsing import (
    parse_tlog_data,
    parse_crpl2_full,
)


def _decompress_if_gzip(buf):
    if len(buf) > 2 and buf[0] == 0x1F and buf[1] == 0x8B:
        return gzip.decompress(buf)
    return buf


def _decode_tlog(buf, filename):
    buf = _decompress_if_gzip(buf)

    meta = parse_tlog_data(buf, convert=False)
    data = {
        "songName": meta["songName"],
        "levelPath": meta["levelPath"],
        "timestamp": meta["timestamp"],
        "offsets": meta["offsets"],
    }
    summary = {
        "songName": meta["songName"],
        "versionText": meta["versionText"],
        "total": len(meta["offsets"]),
    }
    return data, summary


def _decode_crpl2(buf, filename):
    full = parse_crpl2_full(buf, filename)
    arrays = full["arrays"]
    data = {
        "FormatVersion": full["formatVersion"],
        "CompactCreplayfile": {
            "s": full["strDict"],
            "b": full["boolDict"],
            "i": full["intDict"],
            "d": full["doubleDict"],
            **arrays,
        },
    }
    summary = {
        "songName": full["songName"],
        "versionText": "CRPL2",
        "total": len(arrays.get("hitCurrAngles", [])),
    }
    return data, summary


def decode_file(file_bytes: bytes, filename: str) -> dict:
    """Decode a play-record file into its original JSON structure.

    Returns {"text": pretty-printed JSON, "data": decoded dict, "meta": summary}.
    Raises ValueError for unsupported or malformed input.
    """
    fn = filename.lower()
    if fn.endswith(".crpl2"):
        data, summary = _decode_crpl2(file_bytes, filename)
    elif fn.endswith((".tlog", ".gz")):
        data, summary = _decode_tlog(file_bytes, filename)
    else:
        raise ValueError(
            "Unsupported format: only `.tlog` / `.tlog.gz` / `.crpl2` can be decoded"
        )

    summary["filename"] = filename
    return {
        "text": json.dumps(data, indent=2, ensure_ascii=False),
        "data": data,
        "meta": summary,
    }
