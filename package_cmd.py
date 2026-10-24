"""Create a source-based double-click distribution, without installing or migrating."""
from pathlib import Path
import shutil
from build_desktop import create_seed

ROOT = Path(__file__).resolve().parent


def main():
    target = ROOT / 'dist' / 'SafetyQuiz-CMD'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('config', 'core'):
        shutil.copytree(ROOT / name, target / name, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('desktop.py', 'requirements.txt', 'requirements-launcher.txt', 'start_quiz.ps1', '시험실행.bat'):
        shutil.copy2(ROOT / name, target / name)
    create_seed(ROOT / 'db.sqlite3', target / 'seed.sqlite3')
    (target / '사용방법.txt').write_text(
        '1. ZIP을 원하는 폴더에 모두 압축 해제합니다. ZIP 안에서 직접 실행하지 마세요.\n'
        '2. 시험실행.bat을 더블클릭합니다.\n'
        '3. 첫 실행은 인터넷 연결이 필요합니다. Python과 필요한 구성 요소를 설치합니다.\n'
        '   설치 안내나 권한 확인 창이 나오면 내용을 확인하고 진행하세요.\n'
        '4. 화면에서 문제 풀기를 누릅니다. 종료하기 또는 X를 누르면 서버와 화면이 종료됩니다.\n'
        '5. 다음부터 같은 시험실행.bat으로 실행합니다.\n\n'
        'Windows 10/11 및 winget(앱 설치 관리자)이 필요합니다.\n'
        '오류가 나면 CMD 창의 안내를 확인하고 인터넷 또는 설치 상태를 확인하세요.\n'
        'DB 변경 및 마이그레이션은 자동 실행하지 않습니다.\n'
        '개인 답안은 %LOCALAPPDATA%\\SafetyMockQuiz\\db.sqlite3에 저장됩니다.\n'
        '바탕 화면 아이콘: 시험실행.bat 우클릭 → 바로가기 만들기 후 바탕 화면으로 옮기세요.\n',
        encoding='utf-8-sig')
    path = shutil.make_archive(str(ROOT / 'dist' / 'SafetyQuiz-CMD'), 'zip', ROOT / 'dist', target.name)
    print(path)


if __name__ == '__main__':
    main()
