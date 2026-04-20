from flask import Blueprint, render_template
from flask_login import login_required
from models import db, Loan, Property, Vehicle, TravelPlan, Insurance, Document, Goal
from datetime import date

timeline_bp = Blueprint('timeline', __name__, url_prefix='/timeline')

@timeline_bp.route('/')
@login_required
def index():
    today = date.today()
    events = []

    # 貸款還清日
    for loan in Loan.query.filter_by(status='active').all():
        pd = loan.payoff_date_estimate()
        if pd and pd >= today:
            events.append({'date': pd, 'icon': '💳', 'color': 'orange',
                'title': f'{loan.name} 還清', 'detail': f'借款人：{loan.borrower_name}', 'category': '貸款'})

    # 房產重要日期
    for p in Property.query.all():
        if p.handover_date and p.handover_date >= today:
            events.append({'date': p.handover_date, 'icon': '🏠', 'color': 'blue',
                'title': f'{p.name} 交屋', 'detail': p.address or '', 'category': '房產'})
        if p.sale_date and p.sale_date >= today:
            events.append({'date': p.sale_date, 'icon': '🏠', 'color': 'green',
                'title': f'{p.name} 售出日', 'detail': '', 'category': '房產'})

    # 車輛保險到期
    for v in Vehicle.query.all():
        if v.insurance_due and v.insurance_due >= today:
            events.append({'date': v.insurance_due, 'icon': '🚗', 'color': 'yellow',
                'title': f'{v.name} 保險到期', 'detail': '', 'category': '車輛'})
        if v.maintenance_due and v.maintenance_due >= today:
            events.append({'date': v.maintenance_due, 'icon': '🔧', 'color': 'slate',
                'title': f'{v.name} 保養提醒', 'detail': '', 'category': '車輛'})

    # 旅遊
    for t in TravelPlan.query.filter(TravelPlan.status.in_(['計劃中', '已確認'])).all():
        if t.start_date and t.start_date >= today:
            events.append({'date': t.start_date, 'icon': '✈️', 'color': 'indigo',
                'title': f'{t.trip_name} 出發', 'detail': t.destination, 'category': '旅遊'})
        if t.end_date and t.end_date >= today:
            events.append({'date': t.end_date, 'icon': '🏡', 'color': 'indigo',
                'title': f'{t.trip_name} 回程', 'detail': t.destination, 'category': '旅遊'})

    # 保險到期
    for ins in Insurance.query.all():
        if ins.end_date and ins.end_date >= today:
            events.append({'date': ins.end_date, 'icon': '🛡️', 'color': 'purple',
                'title': f'{ins.name} 到期', 'detail': ins.insured_name, 'category': '保險'})

    # 文件到期
    for doc in Document.query.all():
        if doc.expiry_date and doc.expiry_date >= today:
            events.append({'date': doc.expiry_date, 'icon': '📄', 'color': 'red',
                'title': f'{doc.name} 到期', 'detail': doc.owner_name, 'category': '文件'})

    # 目標日期
    for g in Goal.query.filter_by(status='進行中').all():
        if g.target_date and g.target_date >= today:
            events.append({'date': g.target_date, 'icon': '🎯', 'color': 'emerald',
                'title': g.title, 'detail': g.category, 'category': '目標'})

    # 排序
    events.sort(key=lambda x: x['date'])

    # 依年月分組
    grouped = {}
    for e in events:
        key = e['date'].strftime('%Y年%m月')
        if key not in grouped:
            grouped[key] = []
        days_left = (e['date'] - today).days
        e['days_left'] = days_left
        e['urgent'] = days_left <= 30
        grouped[key].append(e)

    return render_template('timeline/index.html', grouped=grouped, today=today, total=len(events))
