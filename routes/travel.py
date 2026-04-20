from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, TravelPlan, TravelItem
from datetime import datetime

travel_bp = Blueprint('travel', __name__, url_prefix='/travel')

TRAVEL_STATUSES = ['計劃中', '已確認', '已完成', '已取消']
ITEM_CATEGORIES = ['機票', '住宿', '交通', '餐飲', '活動', '購物', '保險', '其他']

@travel_bp.route('/')
@login_required
def index():
    plans = TravelPlan.query.order_by(TravelPlan.start_date).all()
    upcoming = [p for p in plans if p.status in ['計劃中', '已確認']]
    completed = [p for p in plans if p.status == '已完成']
    return render_template('travel/index.html', upcoming=upcoming, completed=completed, statuses=TRAVEL_STATUSES)

@travel_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        plan = TravelPlan(
            trip_name=request.form['trip_name'],
            destination=request.form['destination'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None,
            total_budget=float(request.form.get('total_budget', 0)),
            status=request.form.get('status', '計劃中'),
            notes=request.form.get('notes', ''),
            created_by=current_user.id
        )
        db.session.add(plan)
        db.session.commit()
        flash(f'旅遊計劃「{plan.trip_name}」已新增', 'success')
        return redirect(url_for('travel.detail', plan_id=plan.id))
    return render_template('travel/form.html', plan=None, statuses=TRAVEL_STATUSES, action='新增')

@travel_bp.route('/detail/<int:plan_id>')
@login_required
def detail(plan_id):
    plan = TravelPlan.query.get_or_404(plan_id)
    by_category = {}
    for item in plan.items:
        if item.category not in by_category:
            by_category[item.category] = []
        by_category[item.category].append(item)
    return render_template('travel/detail.html', plan=plan, by_category=by_category,
                           item_categories=ITEM_CATEGORIES, statuses=TRAVEL_STATUSES)

@travel_bp.route('/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit(plan_id):
    plan = TravelPlan.query.get_or_404(plan_id)
    if request.method == 'POST':
        plan.trip_name = request.form['trip_name']
        plan.destination = request.form['destination']
        plan.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None
        plan.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None
        plan.total_budget = float(request.form.get('total_budget', 0))
        plan.status = request.form.get('status', plan.status)
        plan.notes = request.form.get('notes', '')
        db.session.commit()
        flash(f'旅遊計劃已更新', 'success')
        return redirect(url_for('travel.detail', plan_id=plan.id))
    return render_template('travel/form.html', plan=plan, statuses=TRAVEL_STATUSES, action='編輯')

@travel_bp.route('/delete/<int:plan_id>', methods=['POST'])
@login_required
def delete(plan_id):
    plan = TravelPlan.query.get_or_404(plan_id)
    name = plan.trip_name
    db.session.delete(plan)
    db.session.commit()
    flash(f'旅遊計劃「{name}」已刪除', 'success')
    return redirect(url_for('travel.index'))

@travel_bp.route('/item/add/<int:plan_id>', methods=['POST'])
@login_required
def add_item(plan_id):
    plan = TravelPlan.query.get_or_404(plan_id)
    item = TravelItem(
        travel_id=plan_id,
        category=request.form['category'],
        description=request.form.get('description', ''),
        planned_amount=float(request.form.get('planned_amount', 0)),
        actual_amount=float(request.form['actual_amount']) if request.form.get('actual_amount') else None,
        is_booked='is_booked' in request.form,
        notes=request.form.get('notes', '')
    )
    db.session.add(item)
    db.session.commit()
    return redirect(url_for('travel.detail', plan_id=plan_id))

@travel_bp.route('/item/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = TravelItem.query.get_or_404(item_id)
    plan_id = item.travel_id
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('travel.detail', plan_id=plan_id))
