import random
import re
import unicodedata
from .models import Question


def normalize(value):
    return re.sub(r'[\s.,·:;_()\-]', '', unicodedata.normalize('NFKC', value).lower())


def is_correct(q, answer):
    if q['category'] != 'short':
        return str(answer) == str(q['correct_choice'])
    value = normalize(str(answer))
    if not value:
        return False
    if value in [normalize(x) for x in [q['answer']] + q['accepted_answers']]:
        return True
    expected = normalize(q['answer'])
    if re.findall(r'\d+', value) != re.findall(r'\d+', expected):
        return False
    if any(value.count(b) != expected.count(b) for b in ('이상', '이하', '미만', '초과')):
        return False
    return bool(q['keyword_groups']) and all(any(normalize(word) in value for word in group) for group in q['keyword_groups'])


def create_questions(previous=()):
    counts = {'easy': 5, 'medium': 3, 'hard': 1, 'short': 1}
    pools = {key: list(Question.objects.filter(category=key)) for key in counts}
    if any(len(pools[key]) < count for key, count in counts.items()):
        raise ValueError('문제 데이터가 부족합니다.')
    selected = [q for key, count in counts.items() for q in random.sample(pools[key], count)]
    if {q.pk for q in selected} == set(previous):
        remaining = [q for q in pools['easy'] if q.pk not in {x.pk for x in selected}]
        if not remaining:
            raise ValueError('새로운 시험 구성에 필요한 문제가 부족합니다.')
        index = next(i for i, q in enumerate(selected) if q.category == 'easy')
        selected[index] = random.choice(remaining)
    random.shuffle(selected)
    result = []
    for q in selected:
        options = [{'id': i, 'text': text} for i, text in enumerate(q.choices)]
        random.shuffle(options)
        result.append(dict(id=q.pk, number=q.number, category=q.category, label=q.get_category_display(), text=q.text,
                           choices=options, correct_choice=q.correct_choice, answer=q.answer, explanation=q.explanation,
                           source=q.source, accepted_answers=q.accepted_answers, keyword_groups=q.keyword_groups))
    return result
