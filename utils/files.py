import logging
import os
import tempfile
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def temp_record_file(file_bytes: bytes, filename: str):
    _, ext = os.path.splitext(filename)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        yield tmp_path
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                logger.debug("removed temp file: %s", tmp_path)
            except OSError:
                pass
