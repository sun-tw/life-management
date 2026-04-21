from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Country
from datetime import datetime

countries_bp = Blueprint('countries', __name__, url_prefix='/countries')

CONTINENTS = ['亞洲', '歐洲', '北美洲', '南美洲', '非洲', '大洋洲', '中東']

# 常用國家預設清單
DEFAULT_COUNTRIES = [
    ('日本', 'Japan', '亞洲', '🇯🇵'), ('韓國', 'South Korea', '亞洲', '🇰🇷'),
    ('泰國', 'Thailand', '亞洲', '🇹🇭'), ('越南', 'Vietnam', '亞洲', '🇻🇳'),
    ('新加坡', 'Singapore', '亞洲', '🇸🇬'), ('馬來西亞', 'Malaysia', '亞洲', '🇲🇾'),
    ('印尼', 'Indonesia', '亞洲', '🇮🇩'), ('菲律賓', 'Philippines', '亞洲', '🇵🇭'),
    ('印度', 'India', '亞洲', '🇮🇳'), ('香港', 'Hong Kong', '亞洲', '🇭🇰'),
    ('法國', 'France', '歐洲', '🇫🇷'), ('義大利', 'Italy', '歐洲', '🇮🇹'),
    ('西班牙', 'Spain', '歐洲', '🇪🇸'), ('德國', 'Germany', '歐洲', '🇩🇪'),
    ('英國', 'United Kingdom', '歐洲', '🇬🇧'), ('荷蘭', 'Netherlands', '歐洲', '🇳🇱'),
    ('瑞士', 'Switzerland', '歐洲', '🇨🇭'), ('奧地利', 'Austria', '歐洲', '🇦🇹'),
    ('希臘', 'Greece', '歐洲', '🇬🇷'), ('葡萄牙', 'Portugal', '歐洲', '🇵🇹'),
    ('美國', 'United States', '北美洲', '🇺🇸'), ('加拿大', 'Canada', '北美洲', '🇨🇦'),
    ('墨西哥', 'Mexico', '北美洲', '🇲🇽'), ('巴西', 'Brazil', '南美洲', '🇧🇷'),
    ('澳洲', 'Australia', '大洋洲', '🇦🇺'), ('紐西蘭', 'New Zealand', '大洋洲', '🇳🇿'),
    ('土耳其', 'Turkey', '中東', '🇹🇷'), ('以色列', 'Israel', '中東', '🇮🇱'),
    ('南非', 'South Africa', '非洲', '🇿🇦'), ('埃及', 'Egypt', '非洲', '🇪🇬'),
]


@countries_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'bucket')  # bucket | visited
    countries = Country.query.order_by(Country.continent, Country.name).all()

    visited = [c for c in countries if c.visited]
    bucket = [c for c in countries if c.want_to_visit and not c.visited]

    by_continent_visited = {}
    for c in visited:
        by_continent_visited.setdefault(c.continent or '其他', []).append(c)

    by_continent_bucket = {}
    for c in bucket:
        by_continent_bucket.setdefault(c.continent or '其他', []).append(c)

    return render_template('countries/index.html',
        tab=tab,
        visited=visited,
        bucket=bucket,
        by_continent_visited=by_continent_visited,
        by_continent_bucket=by_continent_bucket,
        continents=CONTINENTS,
        all_countries=countries,
    )


@countries_bp.route('/add', methods=['POST'])
@login_required
def add():
    try:
        c = Country(
            name=request.form['name'].strip(),
            name_en=request.form.get('name_en', '').strip(),
            continent=request.form.get('continent', ''),
            visited='visited' in request.form,
            want_to_visit='want_to_visit' in request.form,
            visited_year=int(request.form['visited_year']) if request.form.get('visited_year') else None,
            flag_emoji=request.form.get('flag_emoji', '').strip(),
            notes=request.form.get('notes', '').strip()
        )
        db.session.add(c)
        db.session.commit()
        flash(f'已新增「{c.name}」', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'新增失敗：{str(e)}', 'error')
    return redirect(url_for('countries.index', tab=request.form.get('tab', 'bucket')))


@countries_bp.route('/toggle/<int:id>', methods=['POST'])
@login_required
def toggle(id):
    c = Country.query.get_or_404(id)
    field = request.form.get('field')
    if field == 'visited':
        c.visited = not c.visited
        if c.visited and not c.visited_year:
            from datetime import date
            c.visited_year = date.today().year
    elif field == 'want_to_visit':
        c.want_to_visit = not c.want_to_visit
    db.session.commit()
    return redirect(url_for('countries.index', tab=request.form.get('tab', 'bucket')))


@countries_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    c = Country.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash('已刪除', 'success')
    return redirect(url_for('countries.index'))


@countries_bp.route('/seed', methods=['POST'])
@login_required
def seed():
    """新增常用國家預設清單（只新增不存在的）"""
    existing = {c.name for c in Country.query.all()}
    added = 0
    for name, name_en, continent, flag in DEFAULT_COUNTRIES:
        if name not in existing:
            db.session.add(Country(
                name=name, name_en=name_en, continent=continent,
                flag_emoji=flag, visited=False, want_to_visit=True
            ))
            added += 1
    db.session.commit()
    flash(f'已新增 {added} 個國家到清單', 'success')
    return redirect(url_for('countries.index'))
