from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, HealthRecord, User
from datetime import date

health_bp = Blueprint('health', __name__, url_prefix='/health')


@health_bp.route('/')
@login_required
def index():
    # 切換用戶：預設自己，可切換到太太
    view_user_id = request.args.get('user_id', current_user.id, type=int)
    view_user = User.query.get(view_user_id) or current_user

    # 取得所有家庭成員（供切換 tab）
    all_users = User.query.all()

    records = HealthRecord.query.filter_by(user_id=view_user.id)\
        .order_by(HealthRecord.record_date.desc()).limit(20).all()

    latest = records[0] if records else None

    return render_template('health/index.html',
        view_user=view_user,
        all_users=all_users,
        records=records,
        latest=latest,
        today=date.today().isoformat()
    )


@health_bp.route('/add', methods=['POST'])
@login_required
def add():
    target_user_id = request.form.get('user_id', current_user.id, type=int)
    record = HealthRecord(
        user_id=target_user_id,
        record_date=date.fromisoformat(request.form['record_date']) if request.form.get('record_date') else date.today(),
        weight=float(request.form['weight']) if request.form.get('weight') else None,
        blood_pressure_sys=int(request.form['blood_pressure_sys']) if request.form.get('blood_pressure_sys') else None,
        blood_pressure_dia=int(request.form['blood_pressure_dia']) if request.form.get('blood_pressure_dia') else None,
        heart_rate=int(request.form['heart_rate']) if request.form.get('heart_rate') else None,
        blood_sugar=float(request.form['blood_sugar']) if request.form.get('blood_sugar') else None,
        notes=request.form.get('notes', '')
    )
    db.session.add(record)
    db.session.commit()
    flash('健康記錄已新增！', 'success')
    return redirect(url_for('life_hub.index', tab='health'))


@health_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    record = HealthRecord.query.get_or_404(id)
    user_id = record.user_id
    db.session.delete(record)
    db.session.commit()
    flash('記錄已刪除。', 'success')
    return redirect(url_for('life_hub.index', tab='health'))
