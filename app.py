from flask import Flask, redirect, url_for
from flask_login import LoginManager
from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.loans import loans_bp
from routes.budget import budget_bp
from routes.vehicles import vehicles_bp
from routes.properties import properties_bp
from routes.travel import travel_bp
from routes.settings import settings_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '請先登入'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(loans_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(travel_bp)
    app.register_blueprint(settings_bp)

    # Context processor — inject `now` and `today` into all templates
    from datetime import datetime, date as date_type
    @app.context_processor
    def inject_globals():
        return {'now': datetime.now(), 'today': date_type.today()}

    # Jinja2 filters
    @app.template_filter('money')
    def money_filter(value):
        if value is None:
            return '-'
        return f'${value:,.0f}'

    @app.template_filter('date_fmt')
    def date_fmt_filter(value):
        if value is None:
            return '-'
        return value.strftime('%Y/%m/%d')

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
