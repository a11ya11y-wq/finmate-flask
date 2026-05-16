from core_service import create_app, db
from werkzeug.middleware.proxy_fix import ProxyFix
import os

conf_name = os.getenv('FLASK_CONFIG') or 'default'
app = create_app(config_name=conf_name)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
