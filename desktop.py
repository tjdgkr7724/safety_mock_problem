"""Local desktop entry point. Never creates schema or runs migrations."""
import logging
import os
from pathlib import Path
import secrets
import shutil
import sys
import threading
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server


class LocalServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


def prepare_database(root, directory):
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / 'db.sqlite3'
    if not target.exists():
        source = root / 'seed.sqlite3'
        if not source.exists():
            source = root / 'db.sqlite3'
        if not source.exists():
            raise RuntimeError('문제 DB가 없습니다. 배포 파일을 다시 받아 주세요.')
        temporary = directory / 'db.sqlite3.tmp'
        shutil.copy2(source, temporary)
        temporary.replace(target)
    return target


class ServerController:
    def __init__(self, server, thread):
        self.server = server
        self.thread = thread
        self._lock = threading.Lock()
        self._stopped = False

    def stop(self):
        with self._lock:
            if self._stopped:
                return
            self._stopped = True
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=3)


class DesktopApi:
    def __init__(self, stop_server=lambda: None):
        # pywebview recursively traverses PUBLIC attributes when exposing JS APIs.
        # Never expose the Window, server, locks or native .NET objects here.
        self._window = None
        self._stop_server = stop_server
        self._quitting = False
        self._lock = threading.Lock()

    def quit(self):
        with self._lock:
            if self._quitting:
                return
            self._quitting = True
        def close():
            try:
                self._stop_server()
            finally:
                if self._window:
                    self._window.destroy()
        # Return from JS immediately; do not wait for the GUI to close its own bridge.
        threading.Thread(target=close, name='quiz-shutdown', daemon=True).start()
        return True


def main():
    import webview
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    data_dir = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'SafetyMockQuiz'
    data_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=str(data_dir / 'desktop.log'), level=logging.ERROR)
    database = prepare_database(root, data_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
    os.environ['SAFETY_QUIZ_DB'] = str(database)
    os.environ['SAFETY_QUIZ_DESKTOP'] = '1'
    os.environ['SAFETY_QUIZ_SECRET'] = secrets.token_urlsafe(48)
    from django.core.wsgi import get_wsgi_application
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    application = StaticFilesHandler(get_wsgi_application())
    server = make_server('127.0.0.1', 0, application, server_class=LocalServer, handler_class=WSGIRequestHandler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.1), daemon=True)
    thread.start()
    controller = ServerController(server, thread)
    api = DesktopApi(controller.stop)
    try:
        api._window = webview.create_window('롤링타워 안전 모의시험', f'http://127.0.0.1:{server.server_port}/',
                                          js_api=api, width=1180, height=850, min_size=(560, 600),
                                          confirm_close=False)
        api._window.events.closed += controller.stop
        webview.start(gui='edgechromium', private_mode=True)
    finally:
        controller.stop()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        logging.exception('Desktop startup failed')
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, f'프로그램을 시작하지 못했습니다.\n\n{exc}\n\nMicrosoft Edge WebView2 Runtime 설치 여부도 확인해 주세요.', '안전 모의시험', 0x10)
            sys.exit(1)
        else:
            raise
