from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, MedicalVisit, User
from datetime import datetime, date

medical_bp = Blueprint('medical', __name__, url_prefix='/medical')

DEPARTMENTS = ['內科', '外科', '骨科', '皮膚科', '眼科', '牙科', '耳鼻喉科',
               '心臟科', '腸胃科', '婦產科', '精神科', '家醫科', '其他']


@medical_bp.route('/')
@login_required
def index():
    view_user_id = request.args.get('user_id', current_user.id, type=int)
    view_user = User.query.get(view_user_id) or current_user
    all_users = User.query.all()

    records = MedicalVisit.query.filter_by(user_id=view_user.id)\
        .order_by(MedicalVisit.visit_date.desc()).all()

    # 即將回診
    upcoming = [r for r in records if r.days_until_next_visit() is not None and 0 <= r.days_until_next_visit() <= 60]
    upcoming.sort(key=lambda r: r.next_visit_date)

    total_cost = sum(r.cost or 0 for r in records)

    return render_template('medical/index.html',
        view_user=view_user, all_users=all_users,
        records=records,
        upcoming=upcoming,
        total_cost=total_cost,
        departments=DEPARTMENTS,
        today=date.today()
    )


@medical_bp.route('/add', methods=['POST'])
@login_required
def add():
    try:
        user_id = request.form.get('user_id', current_user.id, type=int)
        record = MedicalVisit(
            user_id=user_id,
            visit_date=datetime.strptime(request.form['visit_date'], '%Y-%m-%d').date() if request.form.get('visit_date') else date.today(),
            hospital=request.form.get('hospital', '').strip(),
            department=request.form.get('department', '').strip(),
            doctor=request.form.get('doctor', '').strip(),
            reason=request.form.get('reason', '').strip(),
            diagnosis=request.form.get('diagnosis', '').strip(),
            medication=request.form.get('medication', '').strip(),
            next_visit_date=datetime.strptime(request.form['next_visit_date'], '%Y-%m-%d').date() if request.form.get('next_visit_date') else None,
            cost=float(request.form['cost']) if request.form.get('cost') else None,
            notes=request.form.get('notes', '').strip()
        )
        db.session.add(record)
        db.session.commit()
        flash('就診記錄已新增', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'新增失敗：{str(e)}', 'error')
    return redirect(url_for('medical.index'))


@medical_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    r = MedicalVisit.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    flash('已刪除', 'success')
    return redirect(url_for('medical.index'))
