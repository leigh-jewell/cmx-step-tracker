# Activate the virtual environment in /usr/local/venv/flask-app

activate_this = '/usr/local/venv/flask-app/bin/activate_this.py'

with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

import sys
sys.path.insert(0, "/var/www/cmx-live")
from cmx import app as application


