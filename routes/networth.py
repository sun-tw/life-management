from flask import Blueprint, render_template
from flask_login import login_required
from models import db, Loan, Investment, Vehicle, Property
from datetime import date

networth_bp = Blueprint('networth', __name__, url_prefix='/networth')

@networth_bp.route('/')
@login_required
def index():
    # 資產
    investments = Investment.query.all()
    vehicles = Vehicle.query.all()
    properties = Property.query.filter(Property.status.in_(['持有中', '出租中'])).all()

    total_investments = sum(i.current_value for i in investments)
    total_vehicle_value = 0  # 車輛通常不計市值，列出即可
    total_property_value = sum(p.estimated_value or 0 for p in properties)

    total_assets = total_investments + total_property_value

    # 負債
    loans = Loan.query.filter_by(status='active').all()
    total_liabilities = sum(l.current_balance for l in loans)
    total_monthly_payments = sum(l.monthly_payment for l in loans)

    # 淨值
    net_worth = total_assets - total_liabilities

    # 投資分組
    inv_by_type = {}
    for inv in investments:
        if inv.investment_type not in inv_by_type:
            inv_by_type[inv.investment_type] = []
        inv_by_type[inv.investment_type].append(inv)

    return render_template('networth/index.html',
        investments=investments,
        vehicles=vehicles,
        properties=properties,
        loans=loans,
        total_investments=total_investments,
        total_property_value=total_property_value,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        total_monthly_payments=total_monthly_payments,
        net_worth=net_worth,
        inv_by_type=inv_by_type,
    )
