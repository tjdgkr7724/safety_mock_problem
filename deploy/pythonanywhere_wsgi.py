"""Paste into the WSGI configuration file linked from PythonAnywhere's Web tab."""

import json
import os
import sys
from pathlib import Path

project = Path.home() / 'safety_mock_problem'
sys.path.insert(0, str(project))

# Keep this file outside the project and deployment ZIP.
with (Path.home() / '.safety_quiz.json').open() as secret_file:
    secrets = json.load(secret_file)
os.environ['SAFETY_QUIZ_SECRET'] = secrets['secret_key']
os.environ['SAFETY_QUIZ_HOST'] = secrets['host']
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_production'

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
