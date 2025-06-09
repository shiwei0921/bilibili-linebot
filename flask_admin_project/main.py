from flask import Flask, session, redirect, url_for
from admin import admin_bp, db, AdminUser
from dotenv import load_dotenv
import os

# 讀取 .env
load_dotenv(dotenv_path="get.env")

# 初始化 Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("SECRET_KEY")

# 設定資料庫連線資訊
db_user = os.getenv("DB_USER")
db_pwd = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{db_user}:{db_pwd}@{db_host}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db.init_app(app)

# 初始化管理員帳號
def init_admin():
    with app.app_context():
        try:
            existing = AdminUser.query.filter_by(account=os.getenv("ADMIN_ACCOUNT")).first()
            if not existing:
                print("✅ 正在建立預設管理員帳號...")
                admin = AdminUser(
                    account=os.getenv("ADMIN_ACCOUNT"),
                    password=os.getenv("ADMIN_PASSWORD"),  # ✅ 不加密
                    level=2
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ 成功建立預設管理員帳號")
            else:
                print("ℹ️ 管理員帳號已存在")
        except Exception as e:
            print("⚠️ 建立帳號錯誤：", e)
            db.session.rollback()

# 註冊後台 blueprint
app.register_blueprint(admin_bp)

@app.route("/")
def index():
    return redirect(url_for("admin.dashboard"))

# 啟動主程式
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        init_admin()
    app.run(debug=True)
