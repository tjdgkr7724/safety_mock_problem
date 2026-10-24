import json
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from .management.commands.import_questions import parse_document
from .models import Attempt, Question
from .services import create_questions, is_correct


class QuizTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for number in range(1, 101):
            category = 'easy' if number <= 60 else 'medium' if number <= 80 else 'hard' if number <= 90 else 'short'
            Question.objects.create(number=number, category=category, text=f'문제 {number}',
                                    choices=[] if category == 'short' else ['정답 보기', '보기 B', '보기 C', '보기 D'],
                                    correct_choice=None if category == 'short' else 0, answer='5m 이상' if category == 'short' else '정답 보기',
                                    explanation='비공개 해설 내용', source='원본 PDF 10쪽', accepted_answers=['5미터 이상'] if category == 'short' else [])

    def begin(self):
        response = self.client.post(reverse('core:start'))
        self.assertEqual(response.status_code, 302)
        return Attempt.objects.latest('pk')

    def test_random_composition(self):
        previous = []
        for _ in range(40):
            questions = create_questions(previous)
            self.assertEqual(Counter(q['category'] for q in questions), {'easy': 5, 'medium': 3, 'hard': 1, 'short': 1})
            ids = [q['id'] for q in questions]
            self.assertEqual(len(set(ids)), 10)
            self.assertNotEqual(set(ids), set(previous))
            previous = ids

    def test_identical_draw_replaces_question(self):
        def sample(pool, count):
            return pool[:count]
        with patch('core.services.random.sample', side_effect=sample):
            first = create_questions()
            second = create_questions([q['id'] for q in first])
        self.assertNotEqual({q['id'] for q in first}, {q['id'] for q in second})

    def test_correct_choice_in_every_position(self):
        q = create_questions()[0]
        q.update(category='easy', correct_choice=0)
        for position in range(4):
            options = [{'id': i, 'text': str(i)} for i in range(4)]
            options.insert(position, options.pop(0))
            q['choices'] = options
            self.assertTrue(is_correct(q, options[position]['id']))
            self.assertFalse(is_correct(q, 1))

    def test_full_flow_and_answer_restoration(self):
        attempt = self.begin()
        original = attempt.questions
        for position, q in enumerate(original, 1):
            url = reverse('core:question', args=[attempt.pk, position])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, '비공개 해설 내용')
            self.assertNotIn('correct_choice', response.context['q'])
            answer = q['answer'] if q['category'] == 'short' else str(q['correct_choice'])
            saved = self.client.post(reverse('core:save', args=[attempt.pk, position]), json.dumps({'answer': answer}), content_type='application/json')
            self.assertEqual(saved.status_code, 200)
            self.assertEqual(self.client.get(url).context['answer'], answer)
        attempt.refresh_from_db()
        self.assertEqual(attempt.questions, original)
        self.assertEqual(self.client.get(reverse('core:confirm', args=[attempt.pk])).context['completed'], 10)
        self.client.post(reverse('core:submit', args=[attempt.pk]))
        result = self.client.get(reverse('core:result', args=[attempt.pk]))
        self.assertEqual(result.context['score'], 10)
        self.assertContains(result, '비공개 해설 내용')
        self.assertEqual(self.client.post(reverse('core:save', args=[attempt.pk, 1]), json.dumps({'answer': ''}), content_type='application/json').status_code, 400)
        self.client.post(reverse('core:override', args=[attempt.pk]), {'correct': 'no'})
        self.assertEqual(self.client.get(reverse('core:result', args=[attempt.pk])).context['score'], 9)
        self.client.post(reverse('core:override', args=[attempt.pk]), {'correct': 'yes'})
        self.assertEqual(self.client.get(reverse('core:result', args=[attempt.pk])).context['score'], 10)
        self.client.post(reverse('core:submit', args=[attempt.pk]))
        second = self.begin()
        self.assertNotEqual({q['id'] for q in original}, {q['id'] for q in second.questions})

    def test_unanswered_and_session_isolation(self):
        attempt = self.begin()
        self.assertEqual(self.client.get(reverse('core:confirm', args=[attempt.pk])).context['missing'], list(range(1, 11)))
        other = Client()
        self.assertRedirects(other.get(reverse('core:question', args=[attempt.pk, 1])), reverse('core:home'))
        self.assertEqual(other.post(reverse('core:save', args=[attempt.pk, 1]), json.dumps({'answer': '0'}), content_type='application/json').status_code, 403)
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('core:start')).status_code, 403)
        self.client.post(reverse('core:submit', args=[attempt.pk]))
        self.assertEqual(self.client.get(reverse('core:result', args=[attempt.pk])).context['score'], 0)

    def test_short_answer_units_and_bounds(self):
        q = dict(category='short', answer='20cm 이하', accepted_answers=['20센티미터 이하'], keyword_groups=[['20cm', '20센티미터'], ['이하']])
        for answer in ('20 cm 이하', '20CM 이하', '20센티미터 이하'):
            self.assertTrue(is_correct(q, answer))
        for answer in ('', '20m 이하', '20cm 이상', '25cm 이하', '20cm 이하 또는 30cm 이하'):
            self.assertFalse(is_correct(q, answer))

    def test_import_validation(self):
        fixture = Path(settings.BASE_DIR) / 'data' / 'questions.json'
        records = json.loads(fixture.read_text(encoding='utf-8'))
        self.assertEqual(len(records), 100)
        self.assertTrue(next(r for r in records if r['number'] == 81)['text'].startswith('5m'))
        self.assertEqual(Counter(r['category'] for r in records), {'easy': 60, 'medium': 20, 'hard': 10, 'short': 10})
