# 안전 모의문제

## 더블클릭 CMD 배포

`시험실행.bat`을 더블클릭하면 Python 3.13 확인/설치, 전용 가상환경 생성,
Django와 pywebview 설치, WebView2 확인/설치 후 시험 전용창을 엽니다.
첫 실행은 인터넷 및 설치 승인 진행이 필요할 수 있습니다. Windows 10/11과
winget(앱 설치 관리자)이 필요하며, 없는 경우 안내 후 멈춥니다.
이후에는 구성요소를 재설치하지 않고 실행합니다. 종료하기 또는 X를 누르면
화면과 서버를 종료하고 CMD도 닫힙니다. 설치/실행 실패 시 CMD가 열려 오류를 표시합니다.
일반 runserver 브라우저가 아닌 desktop.py 전용창을 사용합니다.

전달용 ZIP 생성 (마이그레이션이나 패키지 설치는 하지 않음):

```powershell
.\.venv\Scripts\python.exe package_cmd.py
```

`dist/SafetyQuiz-CMD.zip`을 전달하세요. 수신자는 전부 압축 해제 후
`시험실행.bat`을 더블클릭합니다. Python이나 서버 명령어를 직접 입력할 필요는 없습니다.
전달용 DB는 기존 DB의 복사본에서 개인정보와 응시 기록을 비우고 만들어집니다.
원본 DB는 변경하지 않습니다.

## Windows 실행파일 배포

전용 창으로 실행하면 상단 종료하기 버튼 또는 창의 X로 화면과 서버를 함께 닫습니다.
종료 버튼은 전용 실행창에만 나타납니다. 일반 브라우저와 runserver에는 적용되지 않습니다.
다른 PC의 Python 설치 없이 실행하려면 개발 PC에서 아래 빌드 과정이 필요합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv\Scripts\python.exe build_desktop.py
```

빌드 성공 시 `dist/SafetyQuiz-Windows.zip`을 전달합니다. 받는 사람은 ZIP을 모두
압축 해제하고 `SafetyQuiz.exe`를 더블클릭합니다. `_internal` 폴더도 함께 유지해야 합니다.
바탕 화면 아이콘이 필요하면 EXE의 바로가기를 만드세요.
Windows 10/11 및 Microsoft Edge WebView2 Runtime이 필요합니다.

개발 PC에서 전용창 실행: `.\.venv\Scripts\pythonw.exe desktop.py`
단, requirements-desktop.txt 패키지가 먼저 설치되어 있어야 합니다.

DB 생성이나 마이그레이션은 실행하지 않습니다. 빌드는 기존 DB를 복제하여 배포용
복사본에서 사용자·세션·응시 기록을 비우고 100문항과 기존 스키마만 포함합니다.
원본 프로젝트 DB는 변경하지 않습니다. 수신 PC는 첫 실행 시 사용자별
`%LOCALAPPDATA%\SafetyMockQuiz\db.sqlite3`로 복사하여 사용하며 기존 DB는 덮어쓰지 않습니다.
서버는 127.0.0.1의 빈 포트를 자동 선택하므로 기존 개발 서버와 충돌하지 않습니다.
오류 발생 시 메시지에 표시된 내용을 확인하세요. 이후 실행 오류 로그는 사용자 DB 폴더의
desktop.log에 기록됩니다.

Python 3.13, Django 5.2 LTS 개발 프로젝트입니다.
한국어, Asia/Seoul 시간대, SQLite를 사용합니다.

## 설치 및 실행 (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py load_questions
.\.venv\Scripts\python.exe manage.py runserver
```

설치와 기본 마이그레이션이 완료된 현재 폴더에서는 마지막 명령만 실행하면 됩니다.
홈 화면: http://127.0.0.1:8000/

## 관리자

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

계정을 만든 뒤 http://127.0.0.1:8000/admin/ 에 접속하세요.

## 구성

- `config/`: 프로젝트 설정과 URL, WSGI/ASGI
- `core/`: 기본 앱과 홈 화면
- `core/templates/core/`: HTML 템플릿
- `data/questions.json`: 원본 Word에서 추출한 100문항 (81번 이동 거리만 5m로 보정)

## 모의시험

시작 화면의 문제 풀기 버튼으로 하 5개, 중 3개, 상 1개, 단답형 1개를 추출합니다.
시험 안에서는 문제가 중복되지 않으며, 직전 시험과 같은 10문제 구성을 방지합니다.
문제 배치와 객관식 보기 순서는 시험 시작 때 섞고 해당 회차에서는 유지합니다.
왼쪽 목록이나 이전/다음 버튼으로 이동할 수 있고 응답 상태가 표시됩니다.
답변은 자동 저장되며, 문제 이동은 저장 성공 후 진행합니다.
10번의 제출하기 버튼으로 응답 확인 화면을 연 뒤 최종 제출합니다.
미응답은 오답으로 처리하며, 제출 후 모든 정답과 해설을 확인할 수 있습니다.
단답형은 허용 답안과 핵심어로 자동 채점합니다. 같은 의미의 표현을 놓칠 수 있으므로
결과 화면에서 직접 채점을 변경할 수 있습니다. 다시 풀기는 새로운 시험을 시작합니다.
회차는 브라우저 세션에 연결되며, 쿠키 삭제 후에는 이전 회차에 접근할 수 없습니다.

## Word 문서 다시 가져오기

```powershell
.\.venv\Scripts\python.exe manage.py import_questions "C:\Users\User\OneDrive\바탕 화면\롤링타워_모의문제_100문항_정답해설.docx"
```

문서의 1~100번 번호, 보기 ①~④, 정답:, 해설:, 근거: 구조를 검증한 뒤
문제 번호를 기준으로 갱신합니다. 오류가 있으면 DB를 부분 갱신하지 않습니다.
원본 문서는 수정하지 않습니다. 재가져오기는 관리자에서 편집한 내용을 덮어씁니다.
진행 중인 시험은 시작 시 저장한 문제 내용을 계속 사용합니다.
관리자의 객관식 correct_choice는 보기 목록의 0부터 시작하는 위치입니다.
단답형 accepted_answers는 허용 표현 목록, keyword_groups는 각 그룹에서 하나 이상
포함되어야 하는 표현 목록입니다. 자동 채점은 의미 추론을 하지 않습니다.

DBeaver에서 기존 연결을 새로고침하면 core_question, core_attempt 테이블을 확인할 수 있습니다.

## 테스트

```powershell
.\.venv\Scripts\python.exe manage.py test core
```

설정 확인: `.\.venv\Scripts\python.exe manage.py check`

현재 설정은 로컬 개발용입니다. 배포 시 SECRET_KEY를 환경변수로 분리하고
DEBUG=False, ALLOWED_HOSTS와 정적 파일 설정을 적용하세요.
