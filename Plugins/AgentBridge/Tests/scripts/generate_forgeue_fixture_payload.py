"""程式化生成 ForgeUE fixture payload 中的 4 个文件(PNG×2 + WAV + JSON)。

FBX 和 MP4 不在本脚本范围,需要手动放置(见 plan Task 1.5/1.6)。
"""
from __future__ import annotations

import json
import struct
import wave
import zlib
from pathlib import Path

PAYLOAD_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "forgeue_manifest" / "payload"


def _write_solid_png(path: Path, width: int, height: int, rgba: tuple[int, int, int, int]) -> None:
    """写一张纯色 RGBA PNG(最简编码,不用 PIL)。"""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr = _png_chunk(b"IHDR", ihdr_data)
    raw = b""
    row = bytes(rgba) * width
    for _ in range(height):
        raw += b"\x00" + row
    idat = _png_chunk(b"IDAT", zlib.compress(raw, 9))
    iend = _png_chunk(b"IEND", b"")
    path.write_bytes(sig + ihdr + idat + iend)


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    """构造一个 PNG chunk(长度 + tag + data + CRC)。"""
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return length + tag + data + crc


def _write_silent_wav(path: Path, seconds: float, sample_rate: int = 16000) -> None:
    """写一段静音 mono 16-bit WAV(用内置 wave 模块,不需 numpy)。"""
    n_frames = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * n_frames)


def _write_material_simple(path: Path) -> None:
    """最简 PBR 五字段 material.definition(spec §3.4 Option α)。"""
    payload = {
        "base_color_rgba": [0.5, 0.5, 0.5, 1.0],
        "metallic": 0.0,
        "roughness": 0.7,
        "normal_texture_ref": None,
        "emissive_color_rgba": [0.0, 0.0, 0.0, 1.0],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    """主入口:依次生成 PNG×2 + WAV + JSON 四个 fixture 文件。"""
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _write_solid_png(PAYLOAD_DIR / "tex_albedo.png", 64, 64, (128, 128, 128, 255))
    _write_solid_png(PAYLOAD_DIR / "tex_sprite_sheet.png", 128, 128, (255, 255, 255, 255))
    _write_silent_wav(PAYLOAD_DIR / "sfx_click.wav", 0.5)
    _write_material_simple(PAYLOAD_DIR / "material_simple.json")
    print(f"[generate_forgeue_fixture_payload] 4 files written under {PAYLOAD_DIR}")


if __name__ == "__main__":
    main()
