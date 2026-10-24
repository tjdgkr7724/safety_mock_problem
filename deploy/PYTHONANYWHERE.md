# PythonAnywhere 무료 배포

1. 무료 계정 가입 후 Files에서 `safety_mock_problem.zip`을 홈 폴더에 업로드합니다.
2. Consoles → Bash에서 다음 명령을 실행합니다.

```bash
unzip -n safety_mock_problem.zip -d safety_mock_problem
cd ~/safety_mock_problem
mkvirtualenv --python=/usr/bin/python3.13 safety-quiz
pip install -r requirements.txt
python manage.py migrate
python manage.py load_questions
python manage.py createsuperuser
```

이어서 아래 비밀 설정을 생성하고 정적 파일을 수집합니다.
`YOUR_USERNAME.pythonanywhere.com`을 Web 탭에 표시되는 실제 도메인으로 바꿉니다.

```bash
python -c 'import json,secrets,pathlib; p=pathlib.Path.home()/".safety_quiz.json"; p.touch(mode=0o600,exist_ok=False); p.write_text(json.dumps({"secret_key":secrets.token_urlsafe(64),"host":"YOUR_USERNAME.pythonanywhere.com"})); p.chmod(0o600)'
export SAFETY_QUIZ_SECRET=$(python -c 'import json,pathlib; print(json.loads((pathlib.Path.home()/".safety_quiz.json").read_text())["secret_key"])')
export SAFETY_QUIZ_HOST=YOUR_USERNAME.pythonanywhere.com
python manage.py collectstatic --noinput --settings=config.settings_production
```

비밀 파일 생성은 최초 한 번만 실행합니다. 기존 파일을 덮어쓰지 않습니다.

3. Web → Add a new web app → 무료 도메인 → Manual configuration → Python 3.13을 선택합니다.
4. Virtualenv: `/home/YOUR_USERNAME/.virtualenvs/safety-quiz`
5. Source code와 Working directory: `/home/YOUR_USERNAME/safety_mock_problem`
6. Web 탭의 WSGI configuration file을 열고 내용을 `deploy/pythonanywhere_wsgi.py` 내용으로 교체합니다.
7. Static files: URL `/static/`, Directory `/home/YOUR_USERNAME/safety_mock_problem/staticfiles`
8. Security에서 Force HTTPS를 켠 뒤 Reload합니다. HTTPS 주소에서 문제 시작, 답변 저장, 제출, 관리자 로그인을 확인합니다.

로컬 DB와 응시 기록, 개인 계정은 ZIP에 포함하지 않습니다. 서버에서 문제 100개를 새로 적재합니다.
문제를 관리자에서 수정했다면 JSON 원본과 다를 수 있으므로 별도 이전이 필요합니다.
운영 중에는 서버의 `db.sqlite3`를 Files에서 정기적으로 내려받아 보관하세요.
무료 웹앱은 Web 탭에서 만료일을 확인하고 주기적으로 연장하세요.
재배포 때 DB, 비밀 파일은 덮어쓰지 마세요. 최초 설치 명령을 전부 다시 실행하지 마세요.
