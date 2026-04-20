from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, Vehicle, Property, Insurance, Loan
from datetime import date

assets_bp = Blueprint('assets', __name__, url_prefix='/assets')

INSURANCE_TYPES = ['壽險', '醫療', '車險', '房屋', '意外', '投資型', '其他']


@assets_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'vehicles')

    # ── 車輛 ─────────────────────────────────────────────────────────
    vehicles = Vehicle.query.all()
    loans    = Loan.query.filter_by(status='active').all()

    # ── 房產 ─────────────────────────────────────────────────────────
    properties = Property.query.all()

    # ── 保險 ─────────────────────────────────────────────────────────
    policies = Insurance.query.order_by(Insurance.name).all()
    total_policies = len(policies)
    total_annual   = sum(p.annual_premium() for p in policies)
    expiring_soon  = [p for p in policies
                      if p.days_until_expiry() is not None and p.days_until_expiry() <= 90]
    grouped = {t: [p for p in policies if p.insurance_type == t] for t in INSURANCE_TYPES}

    # ── 統計（頁面頂部摘要列） ────────────────────────────────────────
    active_loans_total = sum(l.current_balance for l in loans)

    return render_template(
        'assets/index.html',
        tab=tab,
        # vehicles
        vehicles=vehicles,
        loans=loans,
        today=date.today(),
        # properties
        properties=properties,
        property_statuses=['持有中', '已售出', '交屋中', '出租中'],
        # insurance
        policies=policies,
        grouped=grouped,
        insurance_types=INSURANCE_TYPES,
        total_policies=total_policies,
        total_annual=total_annual,
        expiring_soon=expiring_soon,
    )
