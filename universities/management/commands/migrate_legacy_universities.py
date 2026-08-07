import shutil
import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from universities.models import University


class Command(BaseCommand):
    help = (
        "기존 K-unirank SQLite의 vote_school 데이터를 "
        "새 University 테이블로 이전합니다."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--legacy-db",
            required=True,
            help="기존 SQLite DB 파일 경로",
        )
        parser.add_argument(
            "--legacy-media",
            required=False,
            help="기존 media 디렉터리 경로",
        )

    def handle(self, *args, **options):
        legacy_db = Path(options["legacy_db"]).resolve()
        legacy_media = (
            Path(options["legacy_media"]).resolve()
            if options.get("legacy_media")
            else None
        )

        if not legacy_db.exists():
            raise CommandError(f"SQLite DB를 찾을 수 없습니다: {legacy_db}")

        if legacy_media and not legacy_media.exists():
            raise CommandError(f"media 폴더를 찾을 수 없습니다: {legacy_media}")

        connection = sqlite3.connect(legacy_db)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        self._validate_legacy_table(cursor)

        cursor.execute(
            '''
            SELECT
                id,
                school_name,
                school_image,
                school_address
            FROM vote_school
            ORDER BY id
            '''
        )

        rows = cursor.fetchall()

        self.stdout.write(f"발견된 대학: {len(rows)}개")

        created_count = 0
        updated_count = 0
        copied_count = 0
        missing_count = 0
        missing_images = []

        logo_destination = (
            settings.BASE_DIR
            / "static"
            / "university"
            / "logos"
        )
        logo_destination.mkdir(parents=True, exist_ok=True)

        try:
            with transaction.atomic():
                for row in rows:
                    legacy_id = row["id"]
                    school_name = (row["school_name"] or "").strip()
                    school_image = (row["school_image"] or "").strip()
                    school_address = (row["school_address"] or "").strip()

                    if not school_name:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[SKIP] id={legacy_id} 학교명이 없습니다."
                            )
                        )
                        continue

                    logo_path = None

                    if school_image:
                        filename = Path(school_image).name
                        logo_path = f"university/logos/{filename}"

                    _, created = University.objects.update_or_create(
                        legacy_id=legacy_id,
                        defaults={
                            "name": school_name,
                            "address": school_address or None,
                            "logo_path": logo_path,
                            "is_active": True,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    if legacy_media and school_image:
                        source_file = legacy_media / school_image
                        destination_file = (
                            logo_destination / Path(school_image).name
                        )

                        if source_file.exists():
                            shutil.copy2(source_file, destination_file)
                            copied_count += 1
                        else:
                            missing_count += 1
                            missing_images.append(
                                {
                                    "legacy_id": legacy_id,
                                    "school": school_name,
                                    "path": str(source_file),
                                }
                            )
        finally:
            connection.close()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("===== Migration 완료 ====="))
        self.stdout.write(f"신규 대학: {created_count}")
        self.stdout.write(f"갱신 대학: {updated_count}")
        self.stdout.write(f"복사된 로고: {copied_count}")
        self.stdout.write(f"누락 로고: {missing_count}")

        if missing_images:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("===== 누락 이미지 ====="))
            for item in missing_images:
                self.stdout.write(
                    f"{item['legacy_id']} | "
                    f"{item['school']} | "
                    f"{item['path']}"
                )

    def _validate_legacy_table(self, cursor):
        cursor.execute(
            '''
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'vote_school'
            '''
        )

        if cursor.fetchone() is None:
            raise CommandError(
                "기존 DB에서 'vote_school' 테이블을 찾지 못했습니다."
            )

        cursor.execute("PRAGMA table_info(vote_school)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {
            "id",
            "school_name",
            "school_image",
            "school_address",
        }

        missing_columns = required_columns - columns

        if missing_columns:
            raise CommandError(
                "기존 vote_school에서 필요 컬럼이 없습니다: "
                f"{missing_columns}"
            )
