from __future__ import annotations
from flask import Blueprint, render_template, abort, redirect, url_for, jsonify, make_response
from typing import Dict, List
from urllib.parse import unquote

from app.services.gallery_service import get_all_photos, get_photo_by_id

# 블루프린트 이름 고정
gallery_bp = Blueprint("gallery", __name__, url_prefix="/gallery")
__all__ = ["gallery_bp"]

def _year_from_photo(p: Dict) -> str:
    tags = p.get("tags") or []
    if tags and isinstance(tags[0], str) and tags[0].isdigit() and len(tags[0]) == 4:
        return tags[0]
    return "unknown"

@gallery_bp.after_request
def add_header(response):
    """모든 갤러리 관련 응답에 캐시 제어 헤더 추가"""
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@gallery_bp.route("/")
def index():
    photos: List[Dict] = get_all_photos()
    for ph in photos:
        ph["year"] = _year_from_photo(ph)

    years = sorted({int(p["year"]) for p in photos if p["year"].isdigit()}, reverse=True)
    years = [str(y) for y in years]
    
    response = make_response(render_template("gallery/index.html", photos=photos, years=years))
    return response

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

    response = make_response(render_template("gallery/detail.html",
                           photo=photo,
                           prev_photo=prev_photo,
                           next_photo=next_photo))
    return response

@gallery_bp.route("/api/photo/<path:filename>/address")
def get_photo_address(filename: str):
    """특정 사진의 최신 주소 정보를 반환 (없으면 조회 시도)"""
    raw = unquote(filename)
    photo = get_photo_by_id(raw)
    if not photo or not photo.get('gps'):
        return jsonify({'error': 'GPS 정보가 없습니다'}), 404
    
    return jsonify({
        'id': photo['id'],
        'address': photo['gps'].get('address'),
        'lat': photo['gps'].get('lat'),
        'lon': photo['gps'].get('lon')
    })
