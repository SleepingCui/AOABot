from .constants import MARGIN_MAP, DISPLAY_ORDER, JD_WEIGHTS
from .decode import decode_file
from .parsing import (
    load_file,
    parse_tlog_data,
    parse_crpl2_data,
    parse_crpl2_full,
    decrypt_crpl2,
    convert_to_ms,
    read_vlq,
    read_string,
)
from .stats import calculate_stats
from .text_report import generate_info_txt

__version__ = "1.0.0"


def analyze(file_path):
    meta = load_file(file_path)
    stats = calculate_stats(meta)
    return meta, stats


__all__ = [
    "MARGIN_MAP",
    "DISPLAY_ORDER",
    "JD_WEIGHTS",
    "load_file",
    "parse_tlog_data",
    "parse_crpl2_data",
    "parse_crpl2_full",
    "decrypt_crpl2",
    "convert_to_ms",
    "read_vlq",
    "read_string",
    "calculate_stats",
    "generate_info_txt",
    "decode_file",
    "analyze",
    "__version__",
]
