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
from routes.transactions import transactions_bp
from routes.insurance import insurance_bp
from routes.documents import documents_bp
from routes.goals import goals_bp
from routes.investments import investments_bp
from routes.health import health_bp
from routes.contacts import contacts_bp
from routes.networth import networth_bp
from routes.timeline import timeline_bp
from routes.assets import assets_bp
from routes.life_hub import life_hub_bp
from routes.data_hub import data_hub_bp
from routes.exercise import exercise_bp
from routes.medical import medical_bp
from routes.countries import countries_bp

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
    for bp in [auth_bp, dashboard_bp, loans_bp, budget_bp, vehicles_bp,
               properties_bp, travel_bp, settings_bp, transactions_bp,
               insurance_bp, documents_bp, goals_bp, investments_bp,
               health_bp, contacts_bp, networth_bp, timeline_bp,
               assets_bp, life_hub_bp, data_hub_bp,
               exercise_bp, medical_bp, countries_bp]:
        app.register_blueprint(bp)

    # Context processor
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
