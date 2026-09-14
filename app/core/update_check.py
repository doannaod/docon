"""Arka planda güncelleme kontrolü (GitHub Releases). İndirme yapmaz, sade bir bildirim üretir.

Ağ hatası, sürüm yoksa vb. her durumda sessizce None döner — kullanıcıyı rahatsız etmez.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

REPO = "doannaod/docon"
RELEASES_URL = f"https://github.com/{REPO}/releases/latest"
_API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
_TIMEOUT_SEC = 5


def _parse_version(v: str) -> tuple[int, ...]:
    v = v.strip().lstrip("vV")
    parts = []
    for p in v.split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def _latest_release_tag() -> str | None:
    req = urllib.request.Request(
        _API_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": "DonusumProgrami"}
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SEC) as r:
            data = json.load(r)
        tag = data.get("tag_name")
        return tag if isinstance(tag, str) else None
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None


def check_for_update(current_version: str) -> str | None:
    """Yeni bir sürüm varsa GitHub'daki tag'ini (ör. 'v0.3.0') döndürür, yoksa None."""
    tag = _latest_release_tag()
    if not tag:
        return None
    return tag if _parse_version(tag) > _parse_version(current_version) else None
