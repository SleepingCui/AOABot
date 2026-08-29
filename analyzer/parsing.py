import gzip
import json
import math
import os
import struct
from datetime import datetime
from hashlib import sha256
from Crypto.Cipher import AES


def read_vlq(data, offset):
  length = 0
  shift = 0
  while True:
    if offset >= len(data):
      raise EOFError("Unexpected EOF while reading VLQ")
    b = data[offset]
    offset += 1
    length |= (b & 0x7F) << shift
    shift += 7
    if not (b & 0x80):
      break
  return length, offset


def read_string(data, offset):
  length, offset = read_vlq(data, offset)
  s = data[offset : offset + length].decode("utf-8", errors="replace")
  return s, offset + length


def parse_v1(data, offset):
  offsets = []
  while offset + 12 <= len(data):
    timing, margin_code = struct.unpack_from("<di", data, offset)
    offsets.append([round(timing, 4), margin_code])
    offset += 12
  return offsets


def parse_v2(data, offset):
  offsets = []
  prev_timing_bits = 0
  while offset < len(data):
    if offset + 8 > len(data):
      break
    (xor_bits,) = struct.unpack_from("<q", data, offset)
    offset += 8

    actual_bits = (xor_bits ^ prev_timing_bits) & 0xFFFFFFFFFFFFFFFF
    prev_timing_bits = actual_bits

    packed = struct.pack("<Q", actual_bits)
    (timing,) = struct.unpack("<d", packed)

    margin_code = 0
    shift = 0
    bytes_read = 0
    try:
      while True:
        if offset >= len(data):
          break
        b = data[offset]
        offset += 1
        bytes_read += 1
        margin_code |= (b & 0x7F) << shift
        shift += 7
        if bytes_read > 5:
          break
        if not (b & 0x80):
          break
    except Exception:
      break

    offsets.append([round(timing, 4), margin_code])
  return offsets


def convert_to_ms(offsets, is_angle, bpm, speed, pitch):
  if not is_angle:
    return offsets
  if bpm is None or speed is None or pitch is None or bpm * speed * pitch == 0:
    return offsets

  factor = 1000.0 / (3.0 * bpm * speed * pitch)
  res = []
  for item in offsets:
    raw_angle = float(item[0])
    ms = round(raw_angle * factor, 4)
    res.append([ms, item[1], raw_angle])
  return res


def parse_tlog_data(data, convert=True):
  offset = 0
  magic = data[offset : offset + 4].decode("ascii", errors="ignore")
  if magic != "TSMZ":
    raise ValueError(f"Invalid magic: {magic}")
  offset += 4

  version = data[offset]
  offset += 1

  (timestamp,) = struct.unpack_from("<q", data, offset)
  offset += 8

  song_name, offset = read_string(data, offset)
  level_path, offset = read_string(data, offset)

  bpm, speed, pitch, is_angle = None, None, None, False
  if version >= 4:
    bpm, speed, pitch = struct.unpack_from("<ddd", data, offset)
    offset += 24
    is_angle = data[offset] == 1
    offset += 1
  elif version == 3:
    is_angle = data[offset] == 1
    offset += 1

  if version == 1:
    offsets = parse_v1(data, offset)
  elif version >= 2:
    offsets = parse_v2(data, offset)
  else:
    raise ValueError(f"Unsupported version: {version}")

  if convert:
    offsets = convert_to_ms(offsets, is_angle, bpm, speed, pitch)

  return {
      "songName": song_name,
      "levelPath": level_path,
      "timestamp": timestamp,
      "versionText": (
          "1.8.2- (v1)" if version == 1 else f"1.9.0+ (v{version})"
      ),
      "bpm": bpm,
      "speed": speed,
      "pitch": pitch,
      "isAngle": is_angle,
      "offsets": offsets,
  }


def decrypt_crpl2(data):
  """Decrypt a CRP2 payload, stripping PKCS#7 padding."""
  if len(data) < 8 or data[:4] != b"CRP2":
    raise ValueError("Not a valid CRP2 file")

  ciphertext = data[8:]
  key = sha256(b"qwerty").digest()[:32]
  iv = sha256(b"potato").digest()[:16]

  cipher = AES.new(key, AES.MODE_CBC, iv)
  plaintext = cipher.decrypt(ciphertext)

  pad = plaintext[-1]
  if 1 <= pad <= 16 and plaintext[-pad:] == bytes([pad]) * pad:
    plaintext = plaintext[:-pad]
  return plaintext


class _BinaryReader:

  def __init__(self, buf):
    self.buf = buf
    self.offset = 0

  def read_int32(self):
    val = struct.unpack_from("<i", self.buf, self.offset)[0]
    self.offset += 4
    return val

  def read_double(self):
    val = struct.unpack_from("<d", self.buf, self.offset)[0]
    self.offset += 8
    return val

  def read_byte(self):
    val = self.buf[self.offset]
    self.offset += 1
    return val

  def read_ushort(self):
    val = struct.unpack_from("<H", self.buf, self.offset)[0]
    self.offset += 2
    return val

  def read_float(self):
    val = struct.unpack_from("<f", self.buf, self.offset)[0]
    self.offset += 4
    return val

  def read_bool(self):
    return self.read_byte() != 0

  def read_string(self):
    length, shift = 0, 0
    while True:
      b = self.read_byte()
      length |= (b & 0x7F) << shift
      if (b & 0x80) == 0:
        break
      shift += 7
    s = self.buf[self.offset : self.offset + length].decode(
        "utf-8", errors="replace"
    )
    self.offset += length
    return s

  def read_str_dict(self):
    cnt = self.read_int32()
    return {self.read_string(): self.read_string() for _ in range(cnt)}

  def read_bool_dict(self):
    cnt = self.read_int32()
    return {self.read_string(): self.read_bool() for _ in range(cnt)}

  def read_int_dict(self):
    cnt = self.read_int32()
    return {self.read_string(): self.read_int32() for _ in range(cnt)}

  def read_double_dict(self):
    cnt = self.read_int32()
    return {self.read_string(): self.read_double() for _ in range(cnt)}

  def read_list(self, fn):
    cnt = self.read_int32()
    return [fn() for _ in range(cnt)]


def parse_crpl2_full(data, filename):
  """Decode a CRP2 file into a dict of every field it stores."""
  plaintext = decrypt_crpl2(data)
  r = _BinaryReader(plaintext)

  format_version = r.read_int32()
  s = r.read_str_dict()
  b = r.read_bool_dict()
  i = r.read_int_dict()
  d = r.read_double_dict()

  # The arrays that every creplay record carries (in file order).
  key_codes = r.read_list(r.read_ushort)
  key_presses = r.read_list(r.read_int32)
  key_song_positions = r.read_list(r.read_double)
  hit_current_floor_ids = r.read_list(r.read_int32)
  hit_curr_angles = r.read_list(r.read_double)

  arrays = {
      "keyCodes": key_codes,
      "keyPresses": key_presses,
      "keySongPositions": key_song_positions,
      "hitCurrentFloorIDs": hit_current_floor_ids,
      "hitCurrAngles": hit_curr_angles,
  }

  # Extended arrays introduced on newer creplay versions; read best-effort.
  if format_version >= 2:
    for name, reader in (
        ("hitOverloadCounters", r.read_double),
        ("hitNoFailHits", r.read_int32),
        ("hitIsAutos", r.read_int32),
        ("hitNextFloorAutos", r.read_int32),
        ("hitCachedAngles", r.read_double),
        ("hitTargetExitAngles", r.read_double),
        ("hitMidspinInfiniteMargins", r.read_int32),
        ("hitRDCautos", r.read_int32),
        ("hitCurFreeRoamSections", r.read_int32),
    ):
      try:
        arrays[name] = r.read_list(reader)
      except Exception:
        break

  bpm = d.get("bpm", 100.0)

  ts = 0
  base_name = os.path.basename(filename)
  parts = base_name.split("___")
  if len(parts) >= 2 and parts[0].isdigit():
    ts = int(parts[0])
  if not ts:
    ts = int(datetime.now().timestamp())

  offsets = []
  for a in hit_curr_angles:
    ms = a * (60000.0 / (bpm * 2 * math.pi)) if bpm > 0 else 0.0
    offsets.append([round(ms, 4), 30])

  return {
      "formatVersion": format_version,
      "strDict": s,
      "boolDict": b,
      "intDict": i,
      "doubleDict": d,
      "bpm": bpm,
      "timestamp": ts,
      "arrays": arrays,
      "hitAngles": hit_curr_angles,
      "offsets": offsets,
      "songName": s.get("song_name", "Unknown"),
      "levelPath": s.get("level_path", ""),
  }


def parse_crpl2_data(data, filename):
  """Parse a CRP2 file into the common record meta/offsets shape."""
  full = parse_crpl2_full(data, filename)
  return {
      "songName": full["songName"],
      "levelPath": full["levelPath"],
      "timestamp": full["timestamp"],
      "versionText": "CRPL2",
      "offsets": full["offsets"],
  }


def load_file(file_path):
  fn = file_path.lower()
  if fn.endswith(".json"):
    with open(file_path, "r", encoding="utf-8") as f:
      data = json.load(f)
    if "offsets" not in data:
      raise ValueError("Invalid JSON: 'offsets' field missing")

    if isinstance(data["offsets"], list):
      parsed_offsets = data["offsets"]
      ver = "1.7.1+"
    elif isinstance(data["offsets"], dict):
      sorted_keys = sorted(data["offsets"].keys(), key=lambda x: int(x))
      parsed_offsets = [
          [data["offsets"][k]["v"], data["offsets"][k]["j"]] for k in sorted_keys
      ]
      ver = "1.7.0"
    else:
      raise ValueError("Unrecognized offsets format in JSON")

    parsed_offsets = convert_to_ms(
        parsed_offsets,
        data.get("isAngle") is True,
        data.get("bpm"),
        data.get("speed"),
        data.get("pitch"),
    )
    return {
        "offsets": parsed_offsets,
        "versionText": ver,
        "songName": data.get("songName", "Unknown"),
        "levelPath": data.get("levelPath", ""),
        "timestamp": data.get("timestamp", 0),
    }

  elif fn.endswith(".crpl2"):
    with open(file_path, "rb") as f:
      buf = f.read()
    return parse_crpl2_data(buf, file_path)

  else:
    with open(file_path, "rb") as f:
      buf = f.read()
    if fn.endswith(".gz") or (
        len(buf) > 2 and buf[0] == 0x1F and buf[1] == 0x8B
    ):
      buf = gzip.decompress(buf)
    return parse_tlog_data(buf)
