from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Insurance
from datetime import datetime, date

insurance_bp = Blueprint('insurance', __name__, url_prefix='/insurance')

INSURANCE_TYPES = ['壽險', '醫療', '車險', '房屋', '意外', '投資型', '其他']
PAYMENT_FREQUENCIES = ['月繳', '季繳', '半年繳', '年繳']


@insurance_bp.route('/')
@login_required
def index():
    policies = Insurance.query.filter_by(user_id=current_user.id).order_by(Insurance.name).all() \
        if hasattr(Insurance, 'user_id') else Insurance.query.order_by(Insurance.name).all()

    total_policies = len(policies)
    total_annual = sum(p.annual_premium() for p in policies)
    expiring_soon = [p for p in policies if p.days_until_expiry() is not None and p.days_until_expiry() <= 90]

    # 按險種分組
    grouped = {}
    for t in INSURANCE_TYPES:
        grouped[t] = [p for p in policies if p.insurance_type == t]

    return render_template(
        'insurance/index.html',
        policies=policies,
        grouped=grouped,
        insurance_types=INSURANCE_TYPES,
        total_policies=total_policies,
        total_annual=total_annual,
        expiring_soon=expiring_soon
    )


@insurance_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            policy = Insurance(
                name=request.form.get('name', '').strip(),
                insurance_type=request.form.get('insurance_type', ''),
                insurer=request.form.get('insurer', '').strip(),
                policy_number=request.form.get('policy_number', '').strip(),
                insured_name=request.form.get('insured_name', '').strip(),
                beneficiary=request.form.get('beneficiary', '').strip(),
                premium_amount=float(request.form.get('premium_amount') or 0),
                payment_frequency=request.form.get('payment_frequency', '年繳'),
                start_date=_parse_date(request.form.get('start_date')),
                end_date=_parse_date(request.form.get('end_date')),
                coverage_amount=float(request.form.get('coverage_amount') or 0),
                notes=request.form.get('notes', '').strip()
            )
            if hasattr(Insurance, 'user_id'):
                policy.user_id = current_user.id
            db.session.add(policy)
            db.session.commit()
            flash('保單已新增', 'success')
            return redirect(url_for('assets.index', tab='insurance'))
        except Exception as e:
            db.session.rollback()
            flash(f'新增失敗：{str(e)}', 'error')

    return render_template(
        'insurance/form.html',
        policy=None,
        insurance_types=INSURANCE_TYPES,
        payment_frequencies=PAYMENT_FREQUENCIES,
        action='add'
    )


@insurance_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    policy = Insurance.query.get_or_404(id)

    if request.method == 'POST':
        try:
            policy.name = request.form.get('name', '').strip()
            policy.insurance_type = request.form.get('insurance_type', '')
            policy.insurer = request.form.get('insurer', '').strip()
            policy.policy_number = request.form.get('policy_number', '').strip()
            policy.insured_name = request.form.get('insured_name', '').strip()
            policy.beneficiary = request.form.get('beneficiary', '').strip()
            policy.premium_amount = float(request.form.get('premium_amount') or 0)
            policy.payment_frequency = request.form.get('payment_frequency', '年繳')
            policy.start_date = _parse_date(request.form.get('start_date'))
            policy.end_date = _parse_date(request.form.get('end_date'))
            policy.coverage_amount = float(request.form.get('coverage_amount') or 0)
            policy.notes = request.form.get('notes', '').strip()
            db.session.commit()
            flash('保單已更新', 'success')
            return redirect(url_for('assets.index', tab='insurance'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗：{str(e)}', 'error')

    return render_template(
        'insurance/form.html',
        policy=policy,
        insurance_types=INSURANCE_TYPES,
        payment_frequencies=PAYMENT_FREQUENCIES,
        action='edit'
    )


@insurance_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    policy = Insurance.query.get_or_404(id)
    try:
        db.session.delete(policy)
        db.session.commit()
        flash('保單已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除失敗：{str(e)}', 'error')
    return redirect(url_for('assets.index', tab='insurance'))


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None
