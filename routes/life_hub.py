from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, Goal, TravelPlan, HealthRecord, User
from datetime import date

life_hub_bp = Blueprint('life_hub', __name__, url_prefix='/life')

GOAL_CATEGORIES = ['財務', '健康', '學習', '家庭', '旅遊', '事業', '其他']


@life_hub_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'goals')

    # ── 人生目標 ──────────────────────────────────────────────────────
    active_goals    = Goal.query.filter(Goal.status.in_(['進行中', '暫停'])).order_by(Goal.created_at.desc()).all()
    completed_goals = Goal.query.filter(Goal.status.in_(['已完成', '放棄'])).order_by(Goal.created_at.desc()).all()

    # ── 旅遊計劃 ──────────────────────────────────────────────────────
    plans     = TravelPlan.query.order_by(TravelPlan.start_date).all()
    upcoming  = [p for p in plans if p.status in ['計劃中', '已確認']]
    completed_trips = [p for p in plans if p.status == '已完成']

    # ── 健康記錄 ──────────────────────────────────────────────────────
    view_user_id = request.args.get('user_id', current_user.id, type=int)
    view_user    = User.query.get(view_user_id) or current_user
    all_users    = User.query.all()
    health_records = HealthRecord.query.filter_by(user_id=view_user.id)\
        .order_by(HealthRecord.record_date.desc()).limit(20).all()
    latest_health = health_records[0] if health_records else None

    # ── 頂部摘要 ─────────────────────────────────────────────────────
    total_goals       = len(active_goals)
    total_trips       = len(upcoming)
    last_health_date  = latest_health.record_date if latest_health else None

    return render_template(
        'life_hub/index.html',
        tab=tab,
        # goals
        active_goals=active_goals,
        completed_goals=completed_goals,
        goal_categories=GOAL_CATEGORIES,
        # travel
        upcoming=upcoming,
        completed_trips=completed_trips,
        # health
        view_user=view_user,
        all_users=all_users,
        health_records=health_records,
        latest_health=latest_health,
        today=date.today(),
        # summary
        total_goals=total_goals,
        total_trips=total_trips,
        last_health_date=last_health_date,
    )
