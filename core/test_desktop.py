from contextlib import closing
import sqlite3
import socket
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase as UnitTestCase
from unittest.mock import Mock
from django.test import TestCase, override_settings
from build_desktop import create_seed
from desktop import DesktopApi, ServerController, LocalServer, prepare_database
from wsgiref.simple_server import make_server


class DesktopUnitTests(UnitTestCase):
    def test_quit_closes_owned_window(self):
        stopped = threading.Event()
        closed = threading.Event()
        api = DesktopApi(stopped.set)
        api._window = Mock()
        api._window.destroy.side_effect = closed.set
        api.quit()
        self.assertTrue(closed.wait(2))
        self.assertTrue(stopped.is_set())
        api.quit()
        api._window.destroy.assert_called_once_with()

    def test_bridge_exposes_only_quit(self):
        api = DesktopApi()
        api._window = Mock()
        public = [name for name in dir(api) if not name.startswith('_')]
        self.assertEqual(public, ['quit'])

    def test_quit_stops_actual_listener_before_closing_window(self):
        server = make_server('127.0.0.1', 0, lambda env, start: [], server_class=LocalServer)
        port = server.server_port
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()
        controller = ServerController(server, thread)
        closed = threading.Event()
        api = DesktopApi(controller.stop)
        api._window = Mock()
        api._window.destroy.side_effect = closed.set
        try:
            api.quit()
            self.assertTrue(closed.wait(2))
            self.assertFalse(thread.is_alive())
            with socket.socket() as client:
                client.settimeout(0.5)
                self.assertNotEqual(client.connect_ex(('127.0.0.1', port)), 0)
            controller.stop()  # closed event and finally can safely call stop again.
        finally:
            controller.stop()

    def test_database_copy_preserves_existing_answers(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'seed.sqlite3').write_bytes(b'seed')
            target = prepare_database(root, root / 'user')
            self.assertEqual(target.read_bytes(), b'seed')
            target.write_bytes(b'user answers')
            self.assertEqual(prepare_database(root, root / 'user').read_bytes(), b'user answers')

    def test_distribution_seed_sanitizes_only_copy(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source.sqlite3'
            with closing(sqlite3.connect(source)) as db:
                db.executescript('CREATE TABLE core_question(id INTEGER); CREATE TABLE core_attempt(id INTEGER); CREATE TABLE django_session(id INTEGER); CREATE TABLE auth_user(id INTEGER);')
                db.executemany('INSERT INTO core_question VALUES (?)', [(i,) for i in range(100)])
                db.executescript('INSERT INTO core_attempt VALUES (1); INSERT INTO django_session VALUES (1); INSERT INTO auth_user VALUES (1);')
                db.commit()
            create_seed(source, root / 'seed.sqlite3')
            with closing(sqlite3.connect(root / 'seed.sqlite3')) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM core_question').fetchone()[0], 100)
                for table in ('auth_user', 'core_attempt', 'django_session'):
                    self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0)
            with closing(sqlite3.connect(source)) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM auth_user').fetchone()[0], 1)


class DesktopTemplateTests(TestCase):
    @override_settings(DESKTOP_MODE=True)
    def test_exit_button_in_desktop(self):
        response = self.client.get('/')
        self.assertContains(response, '종료하기')
        self.assertContains(response, 'window.pywebview.api.quit()')

    @override_settings(DESKTOP_MODE=False)
    def test_browser_has_no_ineffective_exit_button(self):
        self.assertNotContains(self.client.get('/'), 'id="quit-app"')
