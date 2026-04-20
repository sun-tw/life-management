"""
初始化資料庫並植入預設資料
執行方式: python init_db.py
"""
from app import app
from models import db, User, Loan, Vehicle, Property, TravelPlan
from datetime import date

with app.app_context():
    db.create_all()
    print("✅ 資料庫建立完成")

    # ── 使用者 ──────────────────────────────────────────
    if not User.query.filter_by(username='admin').first():
        owner = User(
            username='admin',
            display_name='本人',
            role='admin',
            birth_date=date(1979, 1, 1),   # 請登入後至設定頁修改正確生日
            life_expectancy=82,
            avatar_color='#4338ca'
        )
        owner.set_password('life2026')
        db.session.add(owner)
        print("✅ 建立使用者：admin（本人）")

    if not User.query.filter_by(username='wife').first():
        wife = User(
            username='wife',
            display_name='太太',
            role='member',
            birth_date=None,
            life_expectancy=82,
            avatar_color='#db2777'
        )
        wife.set_password('life2026')
        db.session.add(wife)
        print("✅ 建立使用者：wife（太太）")

    db.session.flush()

    # ── 貸款 ──────────────────────────────────────────
    if Loan.query.count() == 0:
        loans = [
            Loan(
                name='Tesla Model Y 貸款',
                loan_type='車貸',
                borrower_name='本人',
                original_amount=0,      # 請登入後更新實際金額
                current_balance=0,      # 請登入後更新實際餘額
                monthly_payment=0,      # 請登入後更新月繳金額
                interest_only=False,
                end_date=date(2026, 12, 31),
                status='active',
                notes='預計今年底付款完成'
            ),
            Loan(
                name='台中門市周轉金貸款',
                loan_type='周轉金',
                borrower_name='太太',
                original_amount=1_900_000,
                current_balance=1_900_000,
                monthly_payment=0,      # 只繳息，請更新月繳利息金額
                interest_only=True,
                status='active',
                notes='台中門市，太太名下，周轉金只繳息'
            ),
            Loan(
                name='台中房子周轉金貸款',
                loan_type='周轉金',
                borrower_name='羅世琦（妹妹）',
                original_amount=7_000_000,
                current_balance=7_000_000,
                monthly_payment=0,      # 只繳息，請更新月繳利息金額
                interest_only=True,
                status='active',
                notes='台中房子，妹妹羅世琦名下，周轉金只繳息'
            ),
        ]
        for loan in loans:
            db.session.add(loan)
        db.session.flush()
        print(f"✅ 建立 {len(loans)} 筆貸款資料")

    # ── 車輛 ──────────────────────────────────────────
    if Vehicle.query.count() == 0:
        tesla_loan = Loan.query.filter_by(name='Tesla Model Y 貸款').first()
        vehicles = [
            Vehicle(
                name='吉米 Jimmy',
                vehicle_type='汽車',
                brand='Suzuki',
                model='Jimny',
                owner_name='本人',
                loan_id=None,
                notes='無貸款'
            ),
            Vehicle(
                name='Gogoro 機車',
                vehicle_type='機車',
                brand='Gogoro',
                owner_name='本人',
                loan_id=None,
                notes='無貸款'
            ),
            Vehicle(
                name='Tesla Model Y',
                vehicle_type='汽車',
                brand='Tesla',
                model='Model Y',
                owner_name='本人',
                loan_id=tesla_loan.id if tesla_loan else None,
                notes='預計 2026 年底付清貸款'
            ),
        ]
        for v in vehicles:
            db.session.add(v)
        print(f"✅ 建立 {len(vehicles)} 筆車輛資料")

    # ── 房產 ──────────────────────────────────────────
    if Property.query.count() == 0:
        store_loan = Loan.query.filter_by(name='台中門市周轉金貸款').first()
        house_loan = Loan.query.filter_by(name='台中房子周轉金貸款').first()
        properties = [
            Property(
                name='新莊房子',
                property_type='住宅',
                owner_name='本人',
                address='新北市新莊區',
                status='交屋中',
                loan_id=None,
                sale_date=date(2026, 3, 31),
                handover_date=date(2026, 9, 30),
                notes='2026 年 3 月底售出，預計 9 月完成交屋'
            ),
            Property(
                name='台中門市',
                property_type='門市',
                owner_name='太太',
                address='台中市',
                status='持有中',
                loan_id=store_loan.id if store_loan else None,
                notes='太太名下，有周轉金貸款約 190 萬，只繳息'
            ),
            Property(
                name='台中房子',
                property_type='住宅',
                owner_name='羅世琦（妹妹）',
                address='台中市',
                status='持有中',
                loan_id=house_loan.id if house_loan else None,
                notes='妹妹羅世琦名下，有周轉金貸款約 700 萬，只繳息'
            ),
        ]
        for p in properties:
            db.session.add(p)
        print(f"✅ 建立 {len(properties)} 筆房產資料")

    # ── 旅遊計劃 ──────────────────────────────────────
    if TravelPlan.query.count() == 0:
        owner = User.query.filter_by(username='admin').first()
        travels = [
            TravelPlan(
                trip_name='日本之旅',
                destination='日本',
                status='計劃中',
                notes='尚未確定日期，請更新出發與回程日期及預算',
                created_by=owner.id if owner else None
            ),
            TravelPlan(
                trip_name='歐洲之旅',
                destination='歐洲',
                status='計劃中',
                notes='尚未確定日期，請更新出發與回程日期及預算',
                created_by=owner.id if owner else None
            ),
        ]
        for t in travels:
            db.session.add(t)
        print(f"✅ 建立 {len(travels)} 筆旅遊計劃")

    db.session.commit()
    print()
    print("=" * 50)
    print("🎉 初始化完成！")
    print()
    print("預設帳號：")
    print("  本人  → 帳號: admin  密碼: life2026")
    print("  太太  → 帳號: wife   密碼: life2026")
    print()
    print("啟動伺服器：python app.py")
    print("瀏覽器開啟：http://localhost:5001")
    print()
    print("⚠️  請登入後至「設定」頁面更新你的正確生日")
    print("⚠️  請至「貸款管理」更新 Tesla 貸款的實際金額")
    print("=" * 50)
