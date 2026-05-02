from core_service import create_app, db
from werkzeug.middleware.proxy_fix import ProxyFix

app = create_app(config_name="development")

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
