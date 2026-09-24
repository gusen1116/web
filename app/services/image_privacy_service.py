"""이미지 공개 전에 GPS 메타데이터를 제거하는 서비스."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass


GPS_IFD_TAG = 0x8825
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024
GPS_TEXT_MARKERS = (
    b"GPSLatitude",
    b"GPSLongitude",
    b"GPSAltitude",
    b"GPSPosition",
    b"location.ISO6709",
)

_verified_images: dict[Path, tuple[int, int, int, int, int]] = {}
_verification_lock = threading.Lock()


def _file_version(stat: os.stat_result) -> tuple[int, int, int, int, int]:
    return (stat.st_dev, stat.st_ino, stat.st_ctime_ns, stat.st_mtime_ns, stat.st_size)


class ImagePrivacyError(RuntimeError):
    """이미지를 안전하게 정리하지 못했을 때 발생한다."""


@dataclass(frozen=True)
class ImagePrivacyResult:
    source: Path
    destination: Path
    gps_removed: bool
    converted: bool = False


def _piexif_module():
    try:
        import piexif
    except ImportError as exc:
        raise ImagePrivacyError(
            "GPS 제거에 필요한 piexif가 설치되지 않았습니다. requirements.txt를 설치해 주세요."
        ) from exc
    return piexif


def _safe_filename(filename: str) -> str:
    cleaned = secure_filename(filename)
    if not cleaned or Path(cleaned).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ImagePrivacyError(f"지원하지 않는 이미지 파일입니다: {filename}")
    return cleaned


def _temporary_path(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{destination.stem}-",
        suffix=destination.suffix,
        dir=destination.parent,
        delete=False,
    )
    handle.close()
    return Path(handle.name)


def _contains_gps_text(path: Path) -> bool:
    overlap = max(len(marker) for marker in GPS_TEXT_MARKERS) - 1
    previous = b""
    with path.open("rb") as image_file:
        while chunk := image_file.read(1024 * 1024):
            searchable = previous + chunk
            if any(marker in searchable for marker in GPS_TEXT_MARKERS):
                return True
            previous = searchable[-overlap:]
    return False


def has_gps_metadata(path: str | Path) -> bool:
    """EXIF GPS IFD 또는 위치 XMP 표식이 있는지 검사한다."""

    image_path = Path(path)
    try:
        with Image.open(image_path) as image:
            exif = image.getexif()
            if exif and GPS_IFD_TAG in exif and bool(exif.get_ifd(GPS_IFD_TAG)):
                return True
    except Exception as exc:
        raise ImagePrivacyError(f"GPS 제거 결과를 검증할 수 없습니다: {image_path.name}") from exc
    return _contains_gps_text(image_path)


def _reencode_without_location_metadata(source: Path, temporary: Path) -> None:
    """Re-encode an image when lossless EXIF editing is unavailable or unsafe.

    Only the sanitized EXIF block and color profile are copied. This also drops
    location-bearing XMP chunks that cannot be safely edited in place.
    """

    try:
        with Image.open(source) as image:
            image_format = (image.format or source.suffix.lstrip(".")).upper()
            exif = image.getexif()
            if GPS_IFD_TAG in exif:
                del exif[GPS_IFD_TAG]

            # Saving the opened object directly can silently carry JPEG COM or
            # WebP XMP chunks from ``image.info``. Rebuild from pixels so only
            # the metadata explicitly supplied below reaches the output.
            clean_image = Image.frombytes(image.mode, image.size, image.tobytes())

            save_options: dict[str, object] = {}
            if exif:
                save_options["exif"] = exif.tobytes()
            if image.info.get("icc_profile"):
                save_options["icc_profile"] = image.info["icc_profile"]

            if image_format in {"JPEG", "JPG"}:
                if clean_image.mode not in ("RGB", "L"):
                    clean_image = clean_image.convert("RGB")
                save_options.update(
                    format="JPEG",
                    quality=95,
                    subsampling=0,
                    optimize=True,
                )
            elif image_format == "WEBP":
                save_options.update(format="WEBP", quality=95, method=6)
            else:
                raise ImagePrivacyError(f"재인코딩할 수 없는 이미지 형식입니다: {image_format}")

            clean_image.save(temporary, **save_options)
            clean_image.close()
    except Exception as exc:
        if isinstance(exc, ImagePrivacyError):
            raise
        raise ImagePrivacyError(f"GPS 메타데이터를 제거할 수 없습니다: {source.name}") from exc


def _jpeg_or_webp_without_gps(source: Path, temporary: Path) -> bool:
    contains_location_text = _contains_gps_text(source)
    try:
        with Image.open(source) as image:
            exif = image.getexif()
            contains_gps_ifd = bool(
                exif and GPS_IFD_TAG in exif and bool(exif.get_ifd(GPS_IFD_TAG))
            )
    except Exception as exc:
        raise ImagePrivacyError(f"EXIF를 읽을 수 없습니다: {source.name}") from exc

    if not contains_gps_ifd and not contains_location_text:
        shutil.copy2(source, temporary)
        return False

    # XMP location fields are not safely editable with piexif. Re-encoding
    # copies only explicitly allowed metadata and guarantees those fields drop.
    if contains_location_text:
        _reencode_without_location_metadata(source, temporary)
        return True

    try:
        piexif = _piexif_module()
        piexif_data = piexif.load(str(source))
        piexif_data["GPS"] = {}
        piexif_data.get("0th", {}).pop(piexif.ImageIFD.GPSTag, None)
        piexif.insert(piexif.dump(piexif_data), str(source), str(temporary))
        return True
    except Exception:
        # Keep the privacy feature functional in minimal environments where
        # piexif is unavailable. The fallback may recompress the pixels.
        _reencode_without_location_metadata(source, temporary)
        return True


def _png_without_gps(source: Path, temporary: Path) -> bool:
    try:
        with Image.open(source) as image:
            exif = image.getexif()
            gps_removed = GPS_IFD_TAG in exif and bool(exif.get_ifd(GPS_IFD_TAG))
            if not gps_removed:
                shutil.copy2(source, temporary)
                return False

            del exif[GPS_IFD_TAG]
            save_options: dict[str, object] = {"format": "PNG", "exif": exif.tobytes()}
            if image.info.get("icc_profile"):
                save_options["icc_profile"] = image.info["icc_profile"]
            if image.info.get("dpi"):
                save_options["dpi"] = image.info["dpi"]
            image.save(temporary, **save_options)
            return True
    except ImagePrivacyError:
        raise
    except Exception as exc:
        raise ImagePrivacyError(f"PNG GPS 정보를 제거할 수 없습니다: {source.name}") from exc


def _heif_to_private_jpeg(source: Path, temporary: Path) -> bool:
    """HEIF는 메타데이터만 수정할 수 없어 GPS 없는 JPEG로 정규화한다."""
    try:
        with Image.open(source) as image:
            exif = image.getexif()
            gps_removed = GPS_IFD_TAG in exif and bool(exif.get_ifd(GPS_IFD_TAG))
            image = ImageOps.exif_transpose(image)
            exif = image.getexif()
            if GPS_IFD_TAG in exif:
                del exif[GPS_IFD_TAG]
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            image.save(
                temporary,
                format="JPEG",
                quality=95,
                subsampling=0,
                optimize=True,
                exif=exif.tobytes(),
                icc_profile=image.info.get("icc_profile"),
            )
            return gps_removed
    except Exception as exc:
        raise ImagePrivacyError(f"HEIF 이미지를 안전한 JPEG로 변환할 수 없습니다: {source.name}") from exc


def sanitize_image_gps(
    source: str | Path,
    destination: str | Path | None = None,
    *,
    overwrite: bool = False,
    move_source: bool = False,
) -> ImagePrivacyResult:
    """GPS만 제거한 파일을 원자적으로 저장한다.

    JPEG와 WebP는 가능하면 압축된 이미지 데이터를 그대로 유지한다. XMP 위치
    정보가 있거나 piexif를 사용할 수 없으면 안전을 위해 재인코딩한다.
    HEIF/HEIC는 포맷 제약 때문에 GPS 없는 JPEG로 변환한다.
    """

    source_path = Path(source).resolve()
    if not source_path.is_file():
        raise ImagePrivacyError(f"이미지 파일을 찾을 수 없습니다: {source_path}")

    filename = _safe_filename(source_path.name)
    suffix = source_path.suffix.lower()
    converted = suffix in {".heic", ".heif"}
    output_name = f"{Path(filename).stem}.jpg" if converted else filename
    destination_path = Path(destination).resolve() if destination else source_path
    if destination_path.is_dir():
        destination_path = destination_path / output_name
    elif converted and destination_path.suffix.lower() not in {".jpg", ".jpeg"}:
        destination_path = destination_path.with_suffix(".jpg")

    same_file = destination_path == source_path
    if destination_path.exists() and not same_file and not overwrite:
        raise ImagePrivacyError(f"대상 파일이 이미 존재합니다: {destination_path.name}")

    temporary = _temporary_path(destination_path)
    try:
        if converted:
            gps_removed = _heif_to_private_jpeg(source_path, temporary)
        elif suffix in {".jpg", ".jpeg", ".webp"}:
            gps_removed = _jpeg_or_webp_without_gps(source_path, temporary)
        elif suffix == ".png":
            gps_removed = _png_without_gps(source_path, temporary)
        else:
            raise ImagePrivacyError(f"지원하지 않는 이미지 형식입니다: {suffix}")

        if has_gps_metadata(temporary):
            raise ImagePrivacyError(
                f"GPS 메타데이터가 남아 있어 공개 폴더로 이동하지 않았습니다: {source_path.name}"
            )

        shutil.copymode(source_path, temporary)
        os.replace(temporary, destination_path)
        if (move_source or (converted and destination is None)) and not same_file and source_path.exists():
            source_path.unlink()
        return ImagePrivacyResult(source_path, destination_path, gps_removed, converted)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def ensure_image_gps_private(path: str | Path) -> ImagePrivacyResult | None:
    """Verify a public image once per file version and remove GPS if present.

    The mtime/size cache keeps normal image requests cheap. A changed or newly
    uploaded file is checked again before Flask serves its bytes.
    """

    image_path = Path(path).resolve()
    if not image_path.is_file() or image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return None

    stat = image_path.stat()
    version = _file_version(stat)
    with _verification_lock:
        if _verified_images.get(image_path) == version:
            return ImagePrivacyResult(image_path, image_path, False, False)

        gps_found = has_gps_metadata(image_path)
        if gps_found:
            result = sanitize_image_gps(image_path, overwrite=True)
        else:
            result = ImagePrivacyResult(image_path, image_path, False, False)

        final_stat = image_path.stat()
        _verified_images[image_path] = _file_version(final_stat)
        return result


def ingest_image_file(
    source: str | Path,
    *,
    target: str,
    gallery_directory: str | Path,
    blog_directory: str | Path,
    overwrite: bool = False,
) -> ImagePrivacyResult:
    """비공개 반입 폴더의 파일을 정리한 후 공개 폴더로 이동한다."""

    destinations = {
        "gallery": Path(gallery_directory),
        "blog": Path(blog_directory),
    }
    if target not in destinations:
        raise ImagePrivacyError(f"알 수 없는 대상입니다: {target}")
    destination_directory = destinations[target].resolve()
    destination_directory.mkdir(parents=True, exist_ok=True)
    return sanitize_image_gps(
        source,
        destination_directory,
        overwrite=overwrite,
        move_source=True,
    )


def save_to_incoming(
    upload: BinaryIO,
    filename: str,
    incoming_directory: str | Path,
    target: str,
    *,
    max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    overwrite: bool = False,
) -> Path:
    """HTTP 업로드 파일을 공개 경로 밖의 반입 폴더에 원자적으로 저장한다."""

    if target not in {"gallery", "blog"}:
        raise ImagePrivacyError(f"알 수 없는 업로드 대상입니다: {target}")
    if max_bytes <= 0:
        raise ImagePrivacyError("업로드 크기 제한이 올바르지 않습니다.")

    safe_name = _safe_filename(filename)
    target_directory = Path(incoming_directory).resolve() / target
    target_directory.mkdir(parents=True, exist_ok=True)
    staged_path = target_directory / safe_name
    if staged_path.exists() and not overwrite:
        raise ImagePrivacyError(f"반입 폴더에 같은 파일이 이미 있습니다: {safe_name}")
    temporary = _temporary_path(staged_path)
    try:
        written = 0
        with temporary.open("wb") as output:
            while chunk := upload.read(1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise ImagePrivacyError(f"이미지는 {max_bytes // (1024 * 1024)}MB를 초과할 수 없습니다.")
                output.write(chunk)
        os.replace(temporary, staged_path)
        return staged_path
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def ingest_uploaded_image(
    upload: BinaryIO,
    filename: str,
    *,
    target: str,
    incoming_directory: str | Path,
    gallery_directory: str | Path,
    blog_directory: str | Path,
    max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    overwrite: bool = False,
) -> ImagePrivacyResult:
    """업로드를 비공개로 저장하고, 검증된 결과만 공개 폴더로 이동한다."""

    staged = save_to_incoming(
        upload,
        filename,
        incoming_directory,
        target,
        max_bytes=max_bytes,
        overwrite=overwrite,
    )
    return ingest_image_file(
        staged,
        target=target,
        gallery_directory=gallery_directory,
        blog_directory=blog_directory,
        overwrite=overwrite,
    )
