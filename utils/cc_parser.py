"""
信用卡 PDF 帳單解析器
目前支援：國泰世華 CUBE 卡（電子帳單）
"""

import re
from datetime import date


# ── 自動類別對應表 ────────────────────────────────────────────────────────────
CATEGORY_RULES = [
    ('手續費',   ['國外交易手續費', '國外退貨手續費']),
    ('餐飲',    ['YOSHINOYA', 'LAWSON', 'FAMILYMART', 'FAMILY MART',
                 'SEVEN-ELEVEN', '7-ELEVEN', 'MOSBURGER', 'MINISTOP',
                 'SUPER HAZAMA', 'MATSUYA', 'YOUMEMART', 'ARISORGANICTERRACE',
                 'SOY STORIES', 'SHIZENSHIYOKUHIN', 'RAKUTENPAY',
                 '薔薇派', '太陽堂', '星巴克', 'STARBUCKS', '清水', '統一超商',
                 'CONVENI', 'MAXVALUE']),
    ('交通',    ['SUBWAY', '台灣虎航', '悠遊加值', 'AIRPORT',
                 'UNPLAN', 'JITENSIYANOIITOMO', 'JITENSIYA',
                 'TRAIN', 'BUS', 'TAXI', 'GRAB']),
    ('車輛',    ['特斯拉', 'TESLA', 'ICHARGING', 'ｉｃｈａｒｇｉｎｇ', '充電', '旭電馳']),
    ('住宿',    ['HOTEL', 'BOOKING.COM', 'AIRBNB', 'NEST', 'INN', 'HOSTEL']),
    ('訂閱服務', ['APPLE.COM', '蘋果電腦', 'CLAUDE.AI', 'CLOUDFLARE',
                  'NETFLIX', 'SPOTIFY', 'OPENAI', 'CHATGPT', 'GOOGLE']),
    ('購物',    ['DRUGELEVEN', 'DRUG', 'AIR BIC', 'COUPANG', '昇昌',
                 '富邦', 'MOMO', '博客來', 'AMAZON', 'RAKUTEN', 'UNIQLO']),
    ('醫療',    ['HOSPITAL', '醫院', '診所', '藥局', 'PHARMACY']),
    ('娛樂',    ['CINEMA', '電影', 'KTV', '遊樂', 'TICKET']),
]


def auto_categorize(description: str) -> str:
    desc_up = description.upper()
    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw.upper() in desc_up:
                return category
    return '其他'


# ── 主解析函式 ─────────────────────────────────────────────────────────────────
def parse_cathay_pdf(file_path: str):
    """
    解析國泰世華電子帳單 PDF。
    回傳: (transactions: list[dict], bill_year: int, bill_month: int, card_last4: str)
    每筆 transaction:
        date, description, amount (正數), original_amount (原始正負),
        trans_type ('expense' | 'income'), category, foreign_info
    """
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError('需要安裝 pdfplumber：pip install pdfplumber')

    with pdfplumber.open(file_path) as pdf:
        full_text = '\n'.join(
            page.extract_text() or ''
            for page in pdf.pages
        )

    # ── 偵測民國年份與帳單月份 ───────────────────────────────────────────────
    bill_year, bill_month = _detect_bill_period(full_text)

    # ── 偵測主卡末四碼（最常出現的4位數） ──────────────────────────────────
    card_counts: dict[str, int] = {}
    for m in re.finditer(r'\b(\d{4})\b', full_text):
        c = m.group(1)
        if c not in ('0000',):
            card_counts[c] = card_counts.get(c, 0) + 1
    card_last4 = max(card_counts, key=card_counts.get) if card_counts else '----'

    # ── 解析每一行 ───────────────────────────────────────────────────────────
    transactions = []
    skip_keywords = [
        '本行自動扣繳', '繳款小計', '上期帳單', '正卡本期消費',
        '本期應繳總額', '-----', '---------', '附卡', '您本月',
        '入帳', '消費日',  # 表頭
    ]

    # 正則：MM/DD  MM/DD  說明  金額  卡號四碼  [其餘]
    tx_re = re.compile(
        r'^(\d{2}/\d{2})\s+'       # 消費日
        r'(\d{2}/\d{2})\s+'        # 入帳起息日
        r'(.+?)\s+'                 # 說明（非貪婪）
        r'(-?[\d,]+)\s+'           # 新臺幣金額
        r'(\d{4})'                  # 卡號後四碼
        r'(?:\s+(.*))?$'            # 其餘（幣別/外幣金額等）
    )

    for line in full_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(kw in line for kw in skip_keywords):
            continue

        m = tx_re.match(line)
        if not m:
            continue

        tx_date_str  = m.group(1)   # MM/DD
        description  = m.group(3).strip()
        amount_str   = m.group(4).replace(',', '')
        rest         = (m.group(6) or '').strip()

        try:
            original_amount = float(amount_str)
        except ValueError:
            continue

        # 跳過金額為 0 的行
        if original_amount == 0:
            continue

        # ── 組合日期 ────────────────────────────────────────────────────────
        try:
            month_num, day_num = map(int, tx_date_str.split('/'))
        except ValueError:
            continue

        year_num = bill_year if month_num <= bill_month else bill_year - 1
        try:
            tx_date = date(year_num, month_num, day_num)
        except ValueError:
            continue

        # ── 外幣資訊（備用） ────────────────────────────────────────────────
        foreign_info = _parse_foreign_info(rest)

        transactions.append({
            'date': tx_date,
            'description': description,
            'amount': abs(original_amount),
            'original_amount': original_amount,
            'trans_type': 'income' if original_amount < 0 else 'expense',
            'category': auto_categorize(description),
            'foreign_info': foreign_info,   # e.g. "JPY 30,996"
        })

    return transactions, bill_year, bill_month, card_last4


# ── 私有輔助 ──────────────────────────────────────────────────────────────────
def _detect_bill_period(text: str):
    """從文字中找民國年月，轉換成西元年"""
    m = re.search(r'(\d{3})年(\d{1,2})月', text)
    if m:
        roc_year   = int(m.group(1))
        bill_month = int(m.group(2))
        bill_year  = roc_year + 1911
        return bill_year, bill_month
    # fallback
    today = date.today()
    return today.year, today.month


def _parse_foreign_info(rest: str) -> str:
    """從剩餘欄位提取外幣資訊，例如 'JPY 30,996'"""
    if not rest:
        return ''
    # 找到幣別代碼（2-3個大寫字母）和金額
    m = re.search(r'\b([A-Z]{3})\s+([\d,]+\.?\d*)\b', rest)
    if m:
        currency = m.group(1)
        amount   = m.group(2)
        if currency not in ('TWD', 'TW', 'IE', 'NL', 'KR', 'JP', 'US'):
            return ''
        if currency == 'TWD':
            return ''
        return f'{currency} {amount}'
    return ''
