import json
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .models import Attempt, Question
from .services import create_questions, is_correct


def home(request):
    return render(request, 'core/home.html', {'count': Question.objects.count()})


def owned_attempt(request, pk):
    if not request.session.session_key:
        return None
    return Attempt.objects.filter(pk=pk, owner=request.session.session_key).first()


@require_POST
def start(request):
    if not request.session.session_key:
        request.session.create()
    try:
        questions = create_questions(request.session.get('previous_questions', []))
    except ValueError as exc:
        return render(request, 'core/home.html', {'error': str(exc), 'count': Question.objects.count()}, status=400)
    attempt = Attempt.objects.create(owner=request.session.session_key, questions=questions)
    request.session['previous_questions'] = [q['id'] for q in questions]
    return redirect('core:question', pk=attempt.pk, position=1)


def navigation(attempt):
    return [{'position': i + 1, 'answered': bool(str(attempt.answers.get(str(i + 1), '')).strip())} for i in range(10)]


def question(request, pk, position):
    attempt = owned_attempt(request, pk)
    if not attempt:
        return redirect('core:home')
    if attempt.submitted:
        return redirect('core:result', pk=pk)
    if not 1 <= position <= 10:
        return redirect('core:question', pk=pk, position=1)
    q = attempt.questions[position - 1]
    public = {key: q[key] for key in ('text', 'choices', 'category', 'label')}
    return render(request, 'core/question.html', {'attempt': attempt, 'q': public, 'position': position,
                  'answer': str(attempt.answers.get(str(position), '')), 'navigation': navigation(attempt),
                  'previous': position - 1, 'next': position + 1})


@require_POST
def save(request, pk, position):
    attempt = owned_attempt(request, pk)
    if not attempt:
        return JsonResponse({'error': '세션이 만료되었습니다. 시작 화면으로 돌아가세요.'}, status=403)
    if attempt.submitted or not 1 <= position <= 10:
        return JsonResponse({'error': '답안을 수정할 수 없습니다.'}, status=400)
    try:
        answer = str(json.loads(request.body)['answer']).strip()
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'error': '답안 형식 오류'}, status=400)
    if len(answer) > 2000:
        return JsonResponse({'error': '답안은 2,000자 이하로 입력하세요.'}, status=400)
    if attempt.questions[position - 1]['category'] != 'short' and answer not in ('', '0', '1', '2', '3'):
        return JsonResponse({'error': '올바른 보기를 선택하세요.'}, status=400)
    attempt.answers[str(position)] = answer
    attempt.save(update_fields=['answers'])
    return JsonResponse({'saved': True, 'answered': bool(answer)})


def confirm(request, pk):
    attempt = owned_attempt(request, pk)
    if not attempt:
        return redirect('core:home')
    if attempt.submitted:
        return redirect('core:result', pk=pk)
    missing = [x['position'] for x in navigation(attempt) if not x['answered']]
    return render(request, 'core/confirm.html', {'attempt': attempt, 'missing': missing, 'completed': 10 - len(missing)})


@require_POST
def submit(request, pk):
    attempt = owned_attempt(request, pk)
    if not attempt:
        return redirect('core:home')
    attempt.submitted = True
    attempt.save(update_fields=['submitted'])
    return redirect('core:result', pk=pk)


def result(request, pk):
    attempt = owned_attempt(request, pk)
    if not attempt:
        return redirect('core:home')
    if not attempt.submitted:
        return redirect('core:question', pk=pk, position=1)
    rows = []
    for i, q in enumerate(attempt.questions, 1):
        answer = attempt.answers.get(str(i), '')
        automatic = is_correct(q, answer)
        correct = attempt.short_override if q['category'] == 'short' and attempt.short_override is not None else automatic
        displayed = answer if q['category'] == 'short' else next((x['text'] for x in q['choices'] if str(x['id']) == str(answer)), '')
        rows.append({'position': i, 'q': q, 'answer': displayed, 'correct': correct, 'automatic': automatic,
                     'overridden': q['category'] == 'short' and attempt.short_override is not None})
    score = sum(row['correct'] for row in rows)
    return render(request, 'core/result.html', {'attempt': attempt, 'rows': rows, 'score': score, 'points': score * 10})


@require_POST
def override(request, pk):
    attempt = owned_attempt(request, pk)
    if attempt and attempt.submitted and request.POST.get('correct') in ('yes', 'no'):
        attempt.short_override = request.POST['correct'] == 'yes'
        attempt.save(update_fields=['short_override'])
    return redirect('core:result', pk=pk) if attempt else redirect('core:home')
