from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Loan, BudgetYear, TravelPlan, Vehicle, Property
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # 貸款摘要
    loans = Loan.query.filter_by(status='active').all()
    total_monthly = sum(l.monthly_payment for l in loans)
    total_balance = sum(l.current_balance for l in loans)

    # 今年預算
    current_year = date.today().year
    budget = BudgetYear.query.filter_by(year=current_year).first()

    # 旅遊計劃
    travels = TravelPlan.query.filter(
        TravelPlan.status.in_(['計劃中', '已確認'])
    ).order_by(TravelPlan.start_date).limit(3).all()

    # 重要提醒
    reminders = []
    props = Property.query.all()
    for p in props:
        if p.handover_date and p.handover_date >= date.today():
            days_left = (p.handover_date - date.today()).days
            reminders.append({
                'type': 'property',
                'icon': '🏠',
                'text': f'{p.name} 交屋日期',
                'date': p.handover_date,
                'days_left': days_left,
                'urgent': days_left <= 30
            })

    vehs = Vehicle.query.all()
    for v in vehs:
        if v.insurance_due and v.insurance_due >= date.today():
            days_left = (v.insurance_due - date.today()).days
            if days_left <= 60:
                reminders.append({
                    'type': 'vehicle',
                    'icon': '🚗',
                    'text': f'{v.name} 保險到期',
                    'date': v.insurance_due,
                    'days_left': days_left,
                    'urgent': days_left <= 14
                })

    reminders.sort(key=lambda x: x['date'])

    return render_template('dashboard/index.html',
        loans=loans,
        total_monthly=total_monthly,
        total_balance=total_balance,
        budget=budget,
        travels=travels,
        reminders=reminders,
        current_year=current_year
    )
