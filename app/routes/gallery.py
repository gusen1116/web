from __future__ import annotations
from flask import Blueprint, render_template, abort, redirect, url_for
from typing import Dict, List
from urllib.parse import unquote

from app.services.gallery_service import get_all_photos, get_photo_by_id

# 블루프린트 이름 고정 (register_blueprints에서 gallery_bp를 import)
gallery_bp = Blueprint("gallery", __name__, url_prefix="/gallery")
__all__ = ["gallery_bp"]

def _year_from_photo(p: Dict) -> str:
    tags = p.get("tags") or []
    if tags and isinstance(tags[0], str) and tags[0].isdigit() and len(tags[0]) == 4:
        return tags[0]
    return "unknown"

@gallery_bp.route("/")
def index():
    photos: List[Dict] = get_all_photos()
    for ph in photos:
        ph["year"] = _year_from_photo(ph)

    years = sorted({int(p["year"]) for p in photos if p["year"].isdigit()}, reverse=True)
    years = [str(y) for y in years]
    return render_template("gallery/index.html", photos=photos, years=years)

@gallery_bp.route("/photo/<path:filename>")
def detail(filename: str):
    raw = unquote(filename)
    photo: Dict | None = get_photo_by_id(raw)

    if not photo:
        all_photos = get_all_photos()
        lower_map = {p.get("id", "").lower(): p for p in all_photos if p.get("id")}
        cand = lower_map.get(raw.lower())
        if cand:
            photo = cand
        else:
            base = raw.rsplit(".", 1)[0].lower()
            cand2 = next((p for p in all_photos
                          if p.get("id", "").lower().startswith(base + ".")), None)
            if cand2:
                return redirect(url_for("gallery.detail", filename=cand2["id"]), code=302)

    if not photo:
        abort(404)

    all_photos = get_all_photos()
    all_sorted = sorted(all_photos, key=lambda x: x.get("id", ""), reverse=True)
    try:
        idx = next(i for i, p in enumerate(all_sorted) if p.get("id") == photo.get("id"))
    except StopIteration:
        idx = None

    prev_photo = all_sorted[idx - 1] if (idx is not None and idx - 1 >= 0) else None
    next_photo = all_sorted[idx + 1] if (idx is not None and idx + 1 < len(all_sorted)) else None

    return render_template("gallery/detail.html",
                           photo=photo,
                           prev_photo=prev_photo,
                           next_photo=next_photo)
