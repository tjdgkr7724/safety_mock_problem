"""Build a transferable Windows folder and zip, using existing schema only."""
from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def create_seed(source, target):
    # Only distribution copy is sanitized; the project's DB is read-only.
    with closing(sqlite3.connect(f'{source.as_uri()}?mode=ro', uri=True)) as original:
        with closing(sqlite3.connect(target)) as copy:
            original.backup(copy)
    with closing(sqlite3.connect(target)) as copy:
        tables = {row[0] for row in copy.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'core_question', 'core_attempt', 'django_session'} <= tables:
            raise RuntimeError('배포 전에 필요한 DB 테이블을 준비해 주세요. 자동 마이그레이션은 하지 않습니다.')
        if copy.execute('SELECT COUNT(*) FROM core_question').fetchone()[0] != 100:
            raise RuntimeError('DB에 100문항이 필요합니다.')
        for table in tables - {'core_question', 'django_migrations', 'django_content_type', 'auth_permission', 'sqlite_sequence'}:
            copy.execute('DELETE FROM "' + table.replace('"', '""') + '"')
        copy.commit()
        copy.execute('VACUUM')


def main():
    build = ROOT / 'build' / 'desktop-assets'
    build.mkdir(parents=True, exist_ok=True)
    seed = build / 'seed.sqlite3'
    create_seed(ROOT / 'db.sqlite3', seed)
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--windowed', '--onedir',
               '--name', 'SafetyQuiz', '--collect-all', 'webview', '--collect-all', 'django',
               '--hidden-import', 'config.settings', '--hidden-import', 'config.urls',
               '--hidden-import', 'core.models', '--hidden-import', 'core.views',
               '--hidden-import', 'core.context_processors', '--hidden-import', 'core.urls',
               '--add-data', f'{ROOT / "core"}:core', '--add-data', f'{ROOT / "config"}:config',
               '--add-data', f'{seed}:.', str(ROOT / 'desktop.py')]
    subprocess.run(command, cwd=ROOT, check=True)
    folder = ROOT / 'dist' / 'SafetyQuiz'
    (folder / '사용방법.txt').write_text('1. ZIP을 폴더에 모두 압축 해제하세요.\n2. SafetyQuiz.exe를 더블클릭하세요.\n3. 종료하기 또는 창의 X를 누르면 화면과 서버가 함께 종료됩니다.\n\nPython 설치나 서버 명령은 필요하지 않습니다.\nWindows 10/11 및 Microsoft Edge WebView2 Runtime이 필요합니다.\n실행 파일과 _internal 폴더를 함께 보관하세요.\n바탕 화면에서 쓰려면 EXE의 바로가기를 만드세요.\nDB는 사용자별 %LOCALAPPDATA%\\SafetyMockQuiz에 저장됩니다.\n', encoding='utf-8-sig')
    archive = shutil.make_archive(str(ROOT / 'dist' / 'SafetyQuiz-Windows'), 'zip', ROOT / 'dist', 'SafetyQuiz')
    print(archive)


if __name__ == '__main__':
    main()
