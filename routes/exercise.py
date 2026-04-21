from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, ExerciseRecord, User
from datetime import datetime, date

exercise_bp = Blueprint('exercise', __name__, url_prefix='/exercise')

EXERCISE_TYPES = ['跑步', '健走', '游泳', '重訓', '瑜珈', '自行車', '球類', '登山', '其他']


@exercise_bp.route('/')
@login_required
def index():
    view_user_id = request.args.get('user_id', current_user.id, type=int)
    view_user = User.query.get(view_user_id) or current_user
    all_users = User.query.all()

    records = ExerciseRecord.query.filter_by(user_id=view_user.id)\
        .order_by(ExerciseRecord.exercise_date.desc()).all()

    # 統計
    total_sessions = len(records)
    total_minutes = sum(r.duration_minutes or 0 for r in records)
    total_km = sum(r.distance_km or 0 for r in records)
    total_calories = sum(r.calories or 0 for r in records)

    # 按類型統計
    type_stats = {}
    for r in records:
        type_stats[r.exercise_type] = type_stats.get(r.exercise_type, 0) + 1

    return render_template('exercise/index.html',
        view_user=view_user, all_users=all_users,
        records=records,
        total_sessions=total_sessions,
        total_minutes=total_minutes,
        total_km=round(total_km, 1),
        total_calories=total_calories,
        type_stats=type_stats,
        exercise_types=EXERCISE_TYPES,
        today=date.today()
    )


@exercise_bp.route('/add', methods=['POST'])
@login_required
def add():
    try:
        user_id = request.form.get('user_id', current_user.id, type=int)
        record = ExerciseRecord(
            user_id=user_id,
            exercise_date=datetime.strptime(request.form['exercise_date'], '%Y-%m-%d').date() if request.form.get('exercise_date') else date.today(),
            exercise_type=request.form.get('exercise_type', '其他'),
            duration_minutes=int(request.form['duration_minutes']) if request.form.get('duration_minutes') else None,
            distance_km=float(request.form['distance_km']) if request.form.get('distance_km') else None,
            calories=int(request.form['calories']) if request.form.get('calories') else None,
            notes=request.form.get('notes', '').strip()
        )
        db.session.add(record)
        db.session.commit()
        flash('運動記錄已新增', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'新增失敗：{str(e)}', 'error')
    return redirect(url_for('exercise.index'))


@exercise_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    r = ExerciseRecord.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    flash('已刪除', 'success')
    return redirect(url_for('exercise.index'))
