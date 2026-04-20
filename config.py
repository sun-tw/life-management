import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # 生產環境請設定 SECRET_KEY 環境變數
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'life-mgmt-change-in-production-2026'

    # 優先使用環境變數中的 DB 路徑（Railway volume 掛載在 /app/instance）
    _db_path = os.environ.get('DATABASE_PATH') or os.path.join(BASE_DIR, 'instance', 'life.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{_db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
