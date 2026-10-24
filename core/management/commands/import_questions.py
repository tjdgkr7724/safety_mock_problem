import re
import zipfile
from xml.etree import ElementTree as ET
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Question

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
MARKERS = '①②③④'
GROUPS = {
    91: [['5m', '5미터'], ['이상']], 92: [['20cm', '20센티미터'], ['이하']], 93: [['pp로프', 'pp rope']],
    94: [['허가서'], ['dri'], ['전중후checksheet', '전중후체크시트', '전중후점검표'], ['sop']],
    95: [['8자매듭'], ['4개'], ['양쪽', '양끝', '양단'], ['2개씩']],
    96: [['4면'], ['완전연결'], ['모서리'], ['2m', '2미터'], ['이내']],
    97: [['작업자'], ['2명'], ['이상'], ['안전담당자'], ['1명']],
    98: [['상부'], ['파랑', '파란'], ['1년이상'], ['보조'], ['빨강', '빨간'], ['6개월이상1년미만'], ['하부'], ['노랑', '노란'], ['6개월미만']],
    99: [['2점교차체결'], ['1점이상'], ['항상체결', '체결유지'], ['동시해제금지']],
    100: [['작업중지', '작업중단']],
}


def parse_document(path):
    with open(path, 'rb') as stream, zipfile.ZipFile(stream) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
    paragraphs = [''.join(t.text or '' for t in p.iter(W + 't')).strip() for p in root.iter(W + 'p')]
    records, current = [], None
    for line in paragraphs:
        match = re.match(r'^(\d+)\.\s+(.+)$', line)
        if match:
            if current:
                records.append(current)
            n = int(match[1])
            current = dict(number=n, text=match[2], choices=[], category='easy' if n <= 60 else 'medium' if n <= 80 else 'hard' if n <= 90 else 'short')
        elif current and line:
            if line[0] in MARKERS:
                if len(current['choices']) >= 4 or line[0] != MARKERS[len(current['choices'])]:
                    raise ValueError(f'{current["number"]}번 보기 형식 오류')
                current['choices'].append(line[1:].strip())
            else:
                for prefix, field in [('정답:', 'answer'), ('해설:', 'explanation'), ('근거:', 'source')]:
                    if line.startswith(prefix):
                        current[field] = line.split(':', 1)[1].strip()
    if current:
        records.append(current)
    if [r['number'] for r in records] != list(range(1, 101)):
        raise ValueError('1~100번 문항이 순서대로 있어야 합니다.')
    for r in records:
        for field in ('answer', 'explanation', 'source'):
            if not r.get(field):
                raise ValueError(f'{r["number"]}번 {field} 누락')
        if r['category'] != 'short':
            if len(r['choices']) != 4 or r['answer'][0] not in MARKERS:
                raise ValueError(f'{r["number"]}번 보기/정답 형식 오류')
            r['correct_choice'] = MARKERS.index(r['answer'][0])
            r['answer'] = r['answer'][1:].strip()
            if r['answer'] != r['choices'][r['correct_choice']]:
                raise ValueError(f'{r["number"]}번 정답과 보기 불일치')
        else:
            if r['choices']:
                raise ValueError(f'{r["number"]}번 단답형 보기 오류')
            r['correct_choice'] = None
        r['accepted_answers'] = {91: ['5미터 이상'], 92: ['20센티미터 이하'], 93: ['PP 로프'], 100: ['작업 중단']}.get(r['number'], [])
        r['keyword_groups'] = GROUPS.get(r['number'], [])
        if r['number'] == 81:
            r['text'] = re.sub(r'^4m', '5m', r['text'])
    return records


class Command(BaseCommand):
    help = 'Word 100문항을 검증하고 DB에 저장합니다. 원본은 수정하지 않습니다.'

    def add_arguments(self, parser):
        parser.add_argument('path')

    def handle(self, *args, **options):
        try:
            records = parse_document(options['path'])
            with transaction.atomic():
                for record in records:
                    number = record.pop('number')
                    Question.objects.update_or_create(number=number, defaults=record)
        except (OSError, ValueError, IndexError, zipfile.BadZipFile, ET.ParseError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS('100문항 저장 완료 (81번 질문 5m 적용).'))
