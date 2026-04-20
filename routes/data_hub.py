from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, Document, Contact

data_hub_bp = Blueprint('data_hub', __name__, url_prefix='/data')

DOC_TYPES      = ['護照', '房契', '保單', '駕照', '身分證', '合約', '車輛行照', '健保卡', '其他']
CONTACT_CATS   = ['醫療', '法律', '財務', '保險', '緊急', '家人', '朋友', '其他']


@data_hub_bp.route('/')
@login_required
def index():
    tab = request.args.get('tab', 'documents')

    # ── 重要文件 ──────────────────────────────────────────────────────
    docs = Document.query.order_by(
        Document.is_important.desc(), Document.doc_type
    ).all()
    expiring        = [d for d in docs if d.is_expiring_soon(90)]
    important_docs  = [d for d in docs if d.is_important]
    regular_docs    = [d for d in docs if not d.is_important]
    grouped_docs    = {}
    for t in DOC_TYPES:
        items = [d for d in regular_docs if d.doc_type == t]
        if items:
            grouped_docs[t] = items

    # ── 聯絡人 ───────────────────────────────────────────────────────
    important_contacts = Contact.query.filter_by(is_important=True).order_by(Contact.name).all()
    other_contacts     = Contact.query.filter_by(is_important=False).order_by(Contact.category, Contact.name).all()
    grouped_contacts   = {}
    for c in other_contacts:
        grouped_contacts.setdefault(c.category, []).append(c)

    return render_template(
        'data_hub/index.html',
        tab=tab,
        # documents
        docs=docs,
        expiring=expiring,
        important_docs=important_docs,
        grouped_docs=grouped_docs,
        doc_types=DOC_TYPES,
        # contacts
        important_contacts=important_contacts,
        grouped_contacts=grouped_contacts,
        contact_categories=CONTACT_CATS,
    )
