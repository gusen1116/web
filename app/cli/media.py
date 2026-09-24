"""GPS 메타데이터 제거 및 이미지 반입 관리 명령."""

from pathlib import Path

import click
from flask import Flask, current_app

from app.services.image_privacy_service import (
    ImagePrivacyError,
    SUPPORTED_EXTENSIONS,
    ingest_image_file,
    sanitize_image_gps,
)


def _directories() -> tuple[Path, Path, Path]:
    return (
        Path(current_app.config["MEDIA_INCOMING_DIR"]),
        Path(current_app.config["GALLERY_PHOTOS_DIR"]),
        Path(current_app.config["BLOG_IMAGES_DIR"]),
    )


def register_media_commands(app: Flask) -> None:
    @app.cli.command("media-process-incoming")
    @click.option("--target", type=click.Choice(["gallery", "blog", "all"]), default="all")
    @click.option("--overwrite", is_flag=True, help="같은 이름의 공개 파일을 교체합니다.")
    def process_incoming(target: str, overwrite: bool) -> None:
        """비공개 반입 폴더의 이미지를 정리하고 공개 폴더로 이동합니다."""

        incoming, gallery, blog = _directories()
        targets = ("gallery", "blog") if target == "all" else (target,)
        processed = 0
        for current_target in targets:
            source_directory = incoming / current_target
            source_directory.mkdir(parents=True, exist_ok=True)
            for source in sorted(source_directory.iterdir()):
                if source.is_symlink() or not source.is_file() or source.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                try:
                    result = ingest_image_file(
                        source,
                        target=current_target,
                        gallery_directory=gallery,
                        blog_directory=blog,
                        overwrite=overwrite,
                    )
                except ImagePrivacyError as exc:
                    raise click.ClickException(str(exc)) from exc
                processed += 1
                click.echo(f"{result.source.name} -> {result.destination}")
        click.echo(f"처리 완료: {processed}개")

    @app.cli.command("media-sanitize-existing")
    def sanitize_existing() -> None:
        """현재 갤러리 및 블로그 이미지의 GPS를 일괄 제거합니다."""

        _, gallery, blog = _directories()
        removed = 0
        checked = 0
        for directory in (gallery, blog):
            if not directory.is_dir():
                continue
            for source in sorted(directory.iterdir()):
                if not source.is_file() or source.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue
                checked += 1
                try:
                    result = sanitize_image_gps(source, overwrite=True)
                except ImagePrivacyError as exc:
                    raise click.ClickException(str(exc)) from exc
                removed += int(result.gps_removed)
        click.echo(f"검사 {checked}개, GPS 제거 {removed}개")
