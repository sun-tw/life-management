from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, User
from datetime import datetime

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/')
@login_required
def index():
    users = User.query.all()
    return render_template('settings/index.html', users=users)

@settings_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    current_user.display_name = request.form.get('display_name', current_user.display_name)
    birth_date_str = request.form.get('birth_date')
    if birth_date_str:
        current_user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    current_user.life_expectancy = int(request.form.get('life_expectancy', 82))
    current_user.avatar_color = request.form.get('avatar_color', current_user.avatar_color)
    db.session.commit()
    flash('個人資料已更新', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password')
    new_pw = request.form.get('new_password')
    confirm_pw = request.form.get('confirm_password')
    if not current_user.check_password(current_pw):
        flash('目前密碼錯誤', 'error')
    elif new_pw != confirm_pw:
        flash('新密碼與確認密碼不符', 'error')
    elif len(new_pw) < 6:
        flash('密碼至少需要 6 個字元', 'error')
    else:
        current_user.set_password(new_pw)
        db.session.commit()
        flash('密碼已更新', 'success')
    return redirect(url_for('settings.index'))
