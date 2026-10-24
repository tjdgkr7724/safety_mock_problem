import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Question


class Command(BaseCommand):
    help = '프로젝트에 포함된 문제 데이터를 DB에 저장합니다.'

    def handle(self, *args, **options):
        records = json.loads((Path(settings.BASE_DIR) / 'data/questions.json').read_text(encoding='utf-8'))
        if len(records) != 100 or len({r['number'] for r in records}) != 100:
            raise CommandError('문항 수 또는 번호 오류')
        with transaction.atomic():
            for record in records:
                number = record.pop('number')
                Question.objects.update_or_create(number=number, defaults=record)
        self.stdout.write(self.style.SUCCESS('100문항 저장 완료'))
