from flask import Blueprint, render_template, request, redirect, url_for, flash, session as flask_session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import datetime
import logging

mock_db_admin_users = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

class AdminUser(db.Model):
    __tablename__ = 'ROOT'
    account = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(255))
    level = db.Column(db.Integer, default=1)

    def __init__(self, account, password, level=1):
        self.account = account
        self.password = password
        self.level = level

class SupportedCrypto(db.Model):
    __tablename__ = 'coin_list'
    coin_id = db.Column(db.String(10), primary_key=True)
    coin_name = db.Column(db.String(50))

class User(db.Model):
    __tablename__ = 'user_list'
    user_id = db.Column(db.String(50), primary_key=True)
    balance = db.Column(db.Float, default=5000000)
    investments = db.relationship('Investment', backref='user', lazy=True)
    tracking_list = db.relationship('TrackingItem', backref='user', lazy=True)

class Investment(db.Model):
    __tablename__ = 'history_trade'
    user_id = db.Column(db.String(50), db.ForeignKey('user_list.user_id', ondelete='CASCADE'), primary_key=True)
    coin_id = db.Column(db.String(10), db.ForeignKey('coin_list.coin_id'), primary_key=True)
    trade_time = db.Column(db.DateTime, default=datetime.datetime.utcnow, primary_key=True)
    quantity = db.Column(db.Float)
    price = db.Column(db.Float)
    
    action = db.Column(db.Enum('buy', 'sell'))

class TrackingItem(db.Model):
    __tablename__ = 'follow_list'
    user_id = db.Column(db.String(50), db.ForeignKey('user_list.user_id'), primary_key=True)
    coin_id = db.Column(db.String(10), db.ForeignKey('coin_list.coin_id'), primary_key=True)
    coin = db.relationship('SupportedCrypto', backref='tracking_items')

def get_db_session():
    try:
        return db.session
    except Exception as e:
        logger.error(f"資料庫連接錯誤: {str(e)}")
        raise

def get_admin_user_by_account(db_session, account):
    try:
        return db_session.query(AdminUser).filter_by(account=account).first()
    except Exception as e:
        logger.error(f"查詢管理員帳號時發生錯誤: {str(e)}")
        raise

def add_admin_user_db(db_session, account, password):
    try:
        if db_session.query(AdminUser).filter_by(account=account).first():
            raise ValueError(f"帳號 '{account}' 已存在。")
        new_admin = AdminUser(account=account, password=password)
        db_session.add(new_admin)
        db_session.commit()
        return new_admin
    except:
        db_session.rollback()
        raise

def get_all_supported_cryptos_db(db_session):
    return db_session.query(SupportedCrypto).all()

def add_supported_crypto_db(db_session, symbol, name):
    try:
        if db_session.query(SupportedCrypto).filter_by(coin_id=symbol).first():
            raise ValueError(f"幣種符號 {symbol} 已存在。")
        new_crypto = SupportedCrypto(coin_id=symbol, coin_name=name)
        db_session.add(new_crypto)
        db_session.commit()
        return new_crypto
    except:
        db_session.rollback()
        raise

def get_supported_crypto_by_id_db(db_session, crypto_id):
    return db_session.query(SupportedCrypto).filter_by(coin_id=crypto_id).first()

def update_supported_crypto_db(db_session, crypto_id, new_symbol, new_name):
    try:
        crypto = db_session.query(SupportedCrypto).filter_by(coin_id=crypto_id).first()
        if crypto:
            if new_symbol != crypto_id and db_session.query(SupportedCrypto).filter_by(coin_id=new_symbol).first():
                raise ValueError(f"幣種符號 {new_symbol} 已被其他幣種使用。")
            crypto.coin_id = new_symbol
            crypto.coin_name = new_name
            db_session.commit()
            return crypto
        return None
    except:
        db_session.rollback()
        raise

def delete_supported_crypto_db(db_session, crypto_id):
    try:
        crypto = db_session.query(SupportedCrypto).filter_by(coin_id=crypto_id).first()
        if crypto:
            db_session.delete(crypto)
            db_session.commit()
            return True
        return False
    except:
        db_session.rollback()
        raise

def get_all_users_db(db_session):
    return db_session.query(User).all()

def get_user_by_line_id_db(db_session, line_user_id):
    return db_session.query(User).filter_by(user_id=line_user_id).first()

def get_user_investments_db(db_session, line_user_id):
    return db_session.query(Investment).filter_by(user_id=line_user_id).all()

def get_user_tracking_list_db(db_session, line_user_id):
    return db_session.query(TrackingItem).filter_by(user_id=line_user_id).all()

def delete_user_db(db_session, line_user_id):
    try:
        user = db_session.query(User).filter_by(user_id=line_user_id).first()
        if user:
            db_session.delete(user)
            db_session.commit()
            return True
        return False
    except:
        db_session.rollback()
        raise

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user_id' not in flask_session:
            flash('請先登入以訪問此頁面。', 'warning')
            return redirect(url_for('admin.login', next=request.url_root.rstrip('/') + request.full_path))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    db_session = None
    try:
        current_admin = get_admin_user_by_account(get_db_session(), flask_session.get('admin_account'))
        if not current_admin or current_admin.level != 2:
            flash('只有二級管理員可以註冊新管理員帳號。', 'danger')
            return redirect(url_for('admin.dashboard'))

        if request.method == 'POST':
            print(f"Debug: 收到的註冊表單資料: {request.form}")
            username = request.form.get('account')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            level = int(request.form.get('level', 1))
            
            if not username or not password:
                flash('請填寫所有欄位', 'danger')
                return redirect(url_for('admin.register'))
                
            if password != confirm_password:
                flash('兩次輸入的密碼不一致', 'danger')
                return redirect(url_for('admin.register'))
                
            db_session = get_db_session()
            existing_user = get_admin_user_by_account(db_session, username)
            if existing_user:
                flash('用戶名已存在', 'danger')
                return redirect(url_for('admin.register'))
                
            
            new_user = AdminUser(
                account=username,
                password=password,
                level=level
            )
            
            db_session.add(new_user)
            db_session.commit()
            flash('註冊成功，請登入', 'success')
            return redirect(url_for('admin.login'))
                
    except Exception as e:
        if db_session:
            db_session.rollback()
        flash('註冊失敗，請稍後再試', 'danger')
        print(f"註冊錯誤: {str(e)}")
        return redirect(url_for('admin.register'))
    finally:
        if db_session:
            db_session.close()
            
    return render_template('admin/register.html')

@admin_bp.route('/manage_admins')
@login_required
def manage_admins():
    db_session = None
    try:
        current_admin = get_admin_user_by_account(get_db_session(), flask_session.get('admin_account'))
        if not current_admin or current_admin.level != 2:
            flash('只有二級管理員可以管理其他管理員帳號。', 'danger')
            return redirect(url_for('admin.dashboard'))

        db_session = get_db_session()
        admins = db_session.query(AdminUser).all()
        return render_template('admin/manage_admins.html', admins=admins)
    except Exception as e:
        logger.error(f"Load manage admins page error: {str(e)}")
        flash(f'載入管理管理員頁面時發生錯誤: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))
    finally:
        if db_session:
            db_session.close()

@admin_bp.route('/delete_admin/<string:account>', methods=['POST'])
@login_required
def delete_admin(account):
    db_session = None
    print("Debug: 進入 delete_admin 函式")
    try:
        db_session = get_db_session()
        print(f"Debug: 在 delete_admin 中獲取 db_session: {db_session}")
        
        current_admin = get_admin_user_by_account(db_session, flask_session.get('admin_account'))
        print(f"Debug: current_admin: {current_admin}")
        
        if not current_admin or current_admin.level != 2:
            flash('只有二級管理員可以刪除其他管理員帳號。', 'danger')
            print("Debug: 不是二級管理員或找不到，重定向到 dashboard")
            return redirect(url_for('admin.dashboard'))

        if account == current_admin.account:
            flash('不能刪除自己的帳號。', 'danger')
            print("Debug: 嘗試刪除自己的帳號，重定向到 manage_admins")
            return redirect(url_for('admin.manage_admins'))

        print(f"Debug: 嘗試獲取要刪除的管理員帳號: {account}")
        admin_to_delete = get_admin_user_by_account(db_session, account)
        print(f"Debug: admin_to_delete: {admin_to_delete}")

        if admin_to_delete:
            print(f"Debug: 找到要刪除的管理員，等級為: {admin_to_delete.level}")
            if admin_to_delete.level == 2:
                flash('不能刪除二級管理員帳號。', 'danger')
                print("Debug: 嘗試刪除二級管理員，閃現錯誤訊息")
            else:
                print("Debug: 準備刪除一級管理員")
                db_session.delete(admin_to_delete)
                db_session.commit()
                flash(f'管理員帳號 {account} 已成功刪除。', 'success')
                print(f"Debug: 成功刪除管理員帳號: {account}")
        else:
            flash('找不到指定的管理員帳號。', 'danger')
            print(f"Debug: 找不到指定的管理員帳號: {account}")
    except Exception as e:
        print(f"Debug: 在 delete_admin 中捕獲到異常: {type(e).__name__}: {e}")
        if db_session:
            print("Debug: 異常發生，嘗試 rollback session")
            db_session.rollback()
        else:
            print("Debug: 異常發生，db_session 不存在，無法 rollback")
        logger.error(f"Delete admin error: {str(e)}")
        flash(f'刪除管理員時發生錯誤: {str(e)}', 'danger')
    finally:
        print("Debug: 進入 delete_admin 的 finally 區塊")
        if db_session:
            print(f"Debug: 在 finally 中關閉 db_session: {db_session}")
            db_session.close()
        else:
            print("Debug: 在 finally 中 db_session 不存在，無需關閉")
            
    print("Debug: 退出 delete_admin 函式")
    return redirect(url_for('admin.manage_admins'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    db_session = None

    if request.method == 'POST':
        account = request.form.get('account', '').strip()
        password = request.form.get('password', '').strip()
        next_page = request.form.get('next', '')

        print(f"[DEBUG] 輸入帳號: {account}, 密碼: {password}")

        if not account or not password:
            flash('請輸入帳號和密碼。', 'danger')
            return render_template('admin/login.html')

        try:
            db_session = get_db_session()
            admin = get_admin_user_by_account(db_session, account)

            if admin is None:
                logger.warning(f"登入失敗：帳號 {account} 不存在")
                flash('帳號不存在。', 'danger')
                return render_template('admin/login.html')

            # 嘗試驗證密碼
            if admin.password == password:
                logger.info(f"管理員 {account} 登入成功")
            else:
                logger.warning(f"登入失敗：帳號 {account} 密碼錯誤")
                flash('密碼錯誤。', 'danger')
                return render_template('admin/login.html')
                

            # 登入成功：寫入 session
            flask_session['admin_user_id'] = admin.account
            flask_session['admin_account'] = admin.account
            flask_session['admin_level'] = int(admin.level)
            logger.info(f"管理員 {admin.account} 登入成功")
            flash('登入成功!', 'success')

            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            logger.error(f"登入過程發生錯誤: {str(e)}")
            flash('登入時發生錯誤，請稍後再試。', 'danger')

        finally:
            if db_session:
                db_session.close()

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    flask_session.pop('admin_user_id', None)
    flask_session.pop('admin_account', None)
    flask_session.pop('admin_level', None)
    flash('您已成功登出。', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
def index():
    if 'admin_user_id' in flask_session:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin/dashboard.html', admin_account=flask_session.get('admin_account'))

@admin_bp.route('/cryptos', methods=['GET'])
@login_required
def manage_cryptos():
    db = get_db_session()
    try:
        cryptos = get_all_supported_cryptos_db(db)
    finally:
        db.close()
    return render_template('admin/manage_cryptos.html', cryptos=cryptos)

@admin_bp.route('/cryptos/add', methods=['GET', 'POST'])
@login_required
def add_crypto():
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').strip().upper()
        name = request.form.get('name', '').strip()
        db = get_db_session()
        try:
            if not symbol or not name:
                flash('幣種符號和名稱為必填。', 'danger')
            else:
                add_supported_crypto_db(db, symbol, name)
                flash(f'幣種 {name} ({symbol}) 已成功新增。', 'success')
                return redirect(url_for('admin.manage_cryptos'))
        except ValueError as ve:
            flash(str(ve), 'warning')
        except Exception as e:
            logger.error(f"Add crypto error: {str(e)}")
            flash(f'新增幣種時發生錯誤: {str(e)}', 'danger')
        finally:
            db.close()
    return render_template('admin/add_crypto.html')

@admin_bp.route('/cryptos/edit/<string:crypto_id>', methods=['GET', 'POST'])
@login_required
def edit_crypto(crypto_id):
    db = get_db_session()
    try:
        crypto = get_supported_crypto_by_id_db(db, crypto_id)
        if not crypto:
            flash('找不到指定的幣種。', 'danger')
            return redirect(url_for('admin.manage_cryptos'))

        if request.method == 'POST':
            new_symbol = request.form.get('symbol', '').strip().upper()
            new_name = request.form.get('name', '').strip()

            if not new_symbol or not new_name:
                flash('幣種符號和名稱為必填。', 'danger')
            else:
                try:
                    update_supported_crypto_db(db, crypto_id, new_symbol, new_name)
                    flash(f'幣種 {new_name} ({new_symbol}) 已成功更新。', 'success')
                    return redirect(url_for('admin.manage_cryptos'))
                except ValueError as ve:
                    flash(str(ve), 'warning')
                except Exception as e:
                    logger.error(f"Edit crypto error: {str(e)}")
                    flash(f'更新幣種時發生錯誤: {str(e)}', 'danger')
        return render_template('admin/edit_crypto.html', crypto=crypto)
    except Exception as e:
        logger.error(f"Load edit crypto page error: {str(e)}")
        flash(f'載入編輯頁面時發生錯誤: {str(e)}', 'danger')
        return redirect(url_for('admin.manage_cryptos'))
    finally:
        db.close()

@admin_bp.route('/cryptos/delete/<string:crypto_id>', methods=['POST'])
@login_required
def delete_crypto(crypto_id):
    db = get_db_session()
    try:
        success = delete_supported_crypto_db(db, crypto_id)
        if success:
            flash('幣種已成功刪除。', 'success')
        else:
            flash('找不到要刪除的幣種或刪除失敗。', 'danger')
    except Exception as e:
        logger.error(f"Delete crypto error: {str(e)}")
        flash(f'刪除幣種時發生錯誤: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('admin.manage_cryptos'))

@admin_bp.route('/users', methods=['GET'])
@login_required
def manage_users():
    db = get_db_session()
    try:
        users = db.query(User).all()
    finally:
        db.close()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/users/view/<string:line_user_id>')
@login_required
def view_user_details(line_user_id):
    db = get_db_session()
    try:
        user = get_user_by_line_id_db(db, line_user_id)
        if not user:
            flash('找不到指定的使用者。', 'danger')
            return redirect(url_for('admin.manage_users'))

        investments = db.query(Investment, SupportedCrypto.coin_name).\
            join(SupportedCrypto, Investment.coin_id == SupportedCrypto.coin_id).\
            filter(Investment.user_id == line_user_id).all()

        investments_formatted = [
            {
                'crypto_name': coin_name,
                'quantity': inv.quantity,
                'total_invested_value': inv.amount,
                'price_at_investment_usd': inv.price,
                'invested_at': inv.trade_time
            } for inv, coin_name in investments
        ]

        tracking_list = db.query(TrackingItem, SupportedCrypto.coin_name).\
            join(SupportedCrypto, TrackingItem.coin_id == SupportedCrypto.coin_id).\
            filter(TrackingItem.user_id == line_user_id).all()

        tracking_list_formatted = [
            {
                'crypto_name': coin_name,
                'added_at': None
            } for _, coin_name in tracking_list
        ]

    finally:
        db.close()

    return render_template('admin/view_user_details.html',
                           user=user,
                           investments=investments_formatted,
                           tracking_list=tracking_list_formatted)

@admin_bp.route('/users/delete/<string:line_user_id>', methods=['POST'])
@login_required
def delete_user_admin(line_user_id):
    db = get_db_session()
    try:
        success = delete_user_db(db, line_user_id)
        if success:
            flash(f'使用者 {line_user_id} 及其資料已成功刪除。', 'success')
        else:
            flash(f'找不到使用者 {line_user_id} 或刪除失敗。', 'danger')
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        flash(f'刪除使用者時發生錯誤: {str(e)}', 'danger')
    finally:
        db.close()
    return redirect(url_for('admin.manage_users'))

admin_base_html_template = """
<!doctype html>
<html lang="zh-Hant">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}幣哩幣哩 - 管理後台{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js"></script>
    <style>
        body { padding-top: 4.5rem; }
        .sidebar {
            position: fixed;
            top: 0;
            bottom: 0;
            left: 0;
            z-index: 100; 
            padding: 48px 0 0; 
            box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
        }
        @media (max-width: 767.98px) {
            .sidebar {
                top: 56px; 
                padding-top: 0;
            }
        }
        .sidebar-sticky {
            position: relative;
            top: 0;
            height: calc(100vh - 48px); 
            padding-top: .5rem;
            overflow-x: hidden;
            overflow-y: auto; 
        }
        .nav-link [data-feather] {
            margin-right: 4px;
            color: #999;
            vertical-align: text-bottom;
        }
        .nav-link.active [data-feather] {
            color: inherit;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-md navbar-dark bg-dark fixed-top">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('admin.dashboard') if session.admin_user_id else url_for('admin.login') }}">幣哩幣哩 管理後台</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarCollapse" aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarCollapse">
                <ul class="navbar-nav ms-auto mb-2 mb-md-0">
                    {% if session.admin_user_id %}
                        <li class="nav-item">
                            <span class="navbar-text me-3">你好, {{ session.admin_account }}</span>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('admin.logout') }}">登出</a>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('admin.login') }}">登入</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('admin.register') }}">註冊管理員</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            {% if session.admin_user_id %}
            <nav id="sidebarMenu" class="col-md-3 col-lg-2 d-md-block bg-light sidebar collapse">
                <div class="position-sticky pt-3 sidebar-sticky">
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link {% if request.endpoint == 'admin.dashboard' %}active{% endif %}" aria-current="page" href="{{ url_for('admin.dashboard') }}">
                                <i data-feather="home"></i>
                                主控台
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if 'crypto' in request.endpoint %}active{% endif %}" href="{{ url_for('admin.manage_cryptos') }}">
                                <i data-feather="dollar-sign"></i>
                                管理幣種
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if 'user' in request.endpoint and 'view_user_details' not in request.endpoint %}active{% endif %}" href="{{ url_for('admin.manage_users') }}">
                                <i data-feather="users"></i>
                                管理使用者
                            </a>
                        </li>
                        {% if session.admin_level == 2 %}
                        <li class="nav-item">
                            <a class="nav-link {% if 'manage_admins' in request.endpoint %}active{% endif %}" href="{{ url_for('admin.manage_admins') }}">
                                <i data-feather="shield"></i>
                                管理管理員
                            </a>
                        </li>
                        {% endif %}
                    </ul>
                </div>
            </nav>
            {% endif %}

            <main class="{% if session.admin_user_id %}col-md-9 ms-sm-auto col-lg-10{% else %}col-12{% endif %} px-md-4">
                <div class="pt-3"> {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                                    {{ message }}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                </div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    {% block content %}{% endblock %}
                </div>
            </main>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
      feather.replace() 
    </script>
</body>
</html>
"""

login_html_template = """
{% extends "admin_base.html" %}

{% block title %}管理員登入{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4" style="margin-top: 5vh;">
        <h2 class="text-center mb-4">管理員登入</h2>
        <div class="card">
            <div class="card-body">
                <form method="POST" action="{{ url_for('admin.login', next=request.args.get('next')) }}">
                    <div class="form-floating mb-3">
                        <input type="text" class="form-control" id="account" name="account" placeholder="Account" required>
                        <label for="account">帳號</label>
                    </div>
                    <div class="form-floating mb-3">
                        <input type="password" class="form-control" id="password" name="password" placeholder="Password" required>
                        <label for="password">密碼</label>
                    </div>
                    <button class="w-100 btn btn-lg btn-primary" type="submit">登入</button>
                </form>
                <div class="text-center mt-3">
                    <p>還沒有帳號？ <a href="{{ url_for('admin.register') }}">註冊一個管理員帳號</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

register_html_template = """
{% extends "admin_base.html" %}

{% block title %}註冊管理員帳號{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 col-lg-4" style="margin-top: 5vh;">
        <h2 class="text-center mb-4">註冊管理員帳號</h2>
        <div class="card">
            <div class="card-body">
                <form method="POST" action="{{ url_for('admin.register') }}">
                    <div class="form-floating mb-3">
                        <input type="text" class="form-control" id="username" name="account" placeholder="Username" value="{{ request.form.username or '' }}" required>
                        <label for="username">帳號 (Username)</label>
                    </div>
                    <div class="form-floating mb-3">
                        <input type="password" class="form-control" id="password" name="password" placeholder="Password" required>
                        <label for="password">密碼</label>
                    </div>
                    <div class="form-floating mb-3">
                        <input type="password" class="form-control" id="confirm_password" name="confirm_password" placeholder="Confirm Password" required>
                        <label for="confirm_password">確認密碼</label>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">管理員等級</label>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="level" id="level1" value="1" checked>
                            <label class="form-check-label" for="level1">
                                一級管理員
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="level" id="level2" value="2">
                            <label class="form-check-label" for="level2">
                                二級管理員
                            </label>
                        </div>
                    </div>
                    <button class="w-100 btn btn-lg btn-primary" type="submit">註冊</button>
                </form>
                <div class="text-center mt-3">
                    <p>已經有帳號了？ <a href="{{ url_for('admin.login') }}">前往登入</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

dashboard_html_template = """
{% extends "admin_base.html" %}

{% block title %}主控台 - {{ super() }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">主控台</h1>
</div>
<p>歡迎回來, <strong>{{ admin_account }}</strong>!</p>
<p>您的管理員等級為: **{{ session.admin_level }}**</p>
<p>請從左側選單選擇您要執行的管理功能。</p>
<div class="row mt-4">
    <div class="col-md-6 mb-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title"><i data-feather="dollar-sign"></i> 管理幣種</h5>
                <p class="card-text">新增、編輯或刪除系統支援的加密貨幣種類。</p>
                <a href="{{ url_for('admin.manage_cryptos') }}" class="btn btn-primary">前往管理幣種</a>
            </div>
        </div>
    </div>
    <div class="col-md-6 mb-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title"><i data-feather="users"></i> 管理使用者</h5>
                <p class="card-text">查詢應用程式使用者的資料、投資記錄與追蹤清單。</p>
                <a href="{{ url_for('admin.manage_users') }}" class="btn btn-primary">前往管理使用者</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

manage_cryptos_html_template = """
{% extends "admin_base.html" %}

{% block title %}管理幣種 - {{ super() }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">管理支援幣種</h1>
    <div class="btn-toolbar mb-2 mb-md-0">
        <a href="{{ url_for('admin.add_crypto') }}" class="btn btn-sm btn-primary">
            <i data-feather="plus-circle" class="align-text-bottom"></i>
            新增幣種
        </a>
    </div>
</div>

<div class="table-responsive">
    <table class="table table-striped table-hover table-sm">
        <thead class="table-dark">
            <tr>
                <th>ID</th>
                <th>符號 (Symbol)</th>
                <th>名稱 (Name)</th>
                <th class="text-center">操作</th>
            </tr>
        </thead>
        <tbody>
            {% for crypto in cryptos %}
            <tr>
                <td>{{ crypto.coin_id }}</td>
                <td>{{ crypto.coin_id }}</td>
                <td>{{ crypto.coin_name }}</td>
                <td class="text-center">
                    <a href="{{ url_for('admin.edit_crypto', crypto_id=crypto.coin_id) }}" class="btn btn-sm btn-outline-secondary me-1" title="編輯">
                        <i data-feather="edit-2"></i> 編輯
                    </a>
                    <form action="{{ url_for('admin.delete_crypto', crypto_id=crypto.coin_id) }}" method="POST" style="display: inline-block;" onsubmit="return confirm('確定要刪除「{{ crypto.coin_name }}」嗎？');">
                        <button type="submit" class="btn btn-sm btn-outline-danger" title="刪除">
                            <i data-feather="trash-2"></i> 刪除
                        </button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="4" class="text-center fst-italic">目前沒有支援的幣種。請點擊右上角「新增幣種」來加入。</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
"""

add_crypto_html_template = """
{% extends "admin_base.html" %}

{% block title %}新增幣種 - {{ super() }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">新增支援幣種</h1>
    <a href="{{ url_for('admin.manage_cryptos') }}" class="btn btn-sm btn-outline-secondary">
        <i data-feather="arrow-left"></i> 返回列表
    </a>
</div>
<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="mb-3">
                <label for="symbol" class="form-label">幣種符號 (例如 BTC)</label>
                <input type="text" class="form-control" id="symbol" name="symbol" value="{{ request.form.symbol or '' }}" required>
                <div class="form-text">請輸入大寫的幣種符號。</div>
            </div>
            <div class="mb-3">
                <label for="name" class="form-label">幣種名稱 (例如 Bitcoin)</label>
                <input type="text" class="form-control" id="name" name="name" value="{{ request.form.name or '' }}" required>
            </div>
            <button type="submit" class="btn btn-primary">
                <i data-feather="save"></i> 新增
            </button>
            <a href="{{ url_for('admin.manage_cryptos') }}" class="btn btn-secondary">取消</a>
        </form>
    </div>
</div>
{% endblock %}
"""

edit_crypto_html_template = """
{% extends "admin_base.html" %}

{% block title %}編輯幣種 - {{ super() }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">編輯幣種: {{ crypto.coin_name }}</h1>
     <a href="{{ url_for('admin.manage_cryptos') }}" class="btn btn-sm btn-outline-secondary">
        <i data-feather="arrow-left"></i> 返回列表
    </a>
</div>
<div class="card">
    <div class="card-body">
        <form method="POST">
            <div class="mb-3">
                <label for="symbol" class="form-label">幣種符號</label>
                <input type="text" class="form-control" id="symbol" name="symbol" value="{{ request.form.symbol or crypto.coin_id }}" required>
                 <div class="form-text">請輸入大寫的幣種符號。</div>
            </div>
            <div class="mb-3">
                <label for="name" class="form-label">幣種名稱</label>
                <input type="text" class="form-control" id="name" name="name" value="{{ request.form.name or crypto.coin_name }}" required>
            </div>
            <button type="submit" class="btn btn-primary">
                 <i data-feather="save"></i> 儲存變更
            </button>
            <a href="{{ url_for('admin.manage_cryptos') }}" class="btn btn-secondary">取消</a>
        </form>
    </div>
</div>
{% endblock %}
"""


manage_users_html_template = """
{% extends "admin_base.html" %}

{% block title %}管理使用者 - {{ super() }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">管理應用程式使用者</h1>
</div>
<div class="table-responsive">
    <table class="table table-striped table-hover table-sm">
        <thead class="table-dark">
            <tr>
                <th>使用者 LINE ID</th>
                <th class="text-center">操作</th>
            </tr>
        </thead>
        <tbody>
            {% for user_obj in users %}
            <tr>
                <td>{{ user_obj.user_id }}</td>
                <td class="text-center">
                    <form action="{{ url_for('admin.delete_user_admin', line_user_id=user_obj.user_id) }}" method="POST" style="display: inline-block;" onsubmit="return confirm('確定要刪除使用者 {{ user_obj.user_id }} 嗎？');">
                        <button type="submit" class="btn btn-sm btn-outline-danger" title="刪除使用者">
                            <i data-feather="user-x"></i> 刪除
                        </button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="2" class="text-center fst-italic">目前沒有應用程式使用者。</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
"""

view_user_details_html_template = """
{% extends "admin_base.html" %}

{% block title %}使用者詳情 - {{ super() }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">使用者詳情: <small class="text-muted">{{ user.user_id }}</small></h1>
    <a href="{{ url_for('admin.manage_users') }}" class="btn btn-sm btn-outline-secondary">
        <i data-feather="arrow-left"></i> 返回使用者列表
    </a>
</div>

<div class="card mb-4">
    <div class="card-header">
        <i data-feather="user"></i> 基本資料
    </div>
    <div class="card-body">
        <p><strong>LINE User ID:</strong> {{ user.user_id }}</p>
        <p><strong>註冊時間:</strong> {{ user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A' }}</p>
    </div>
</div>

<div class="card mb-4">
    <div class="card-header">
       <i data-feather="list"></i> 追蹤清單
    </div>
    <div class="card-body">
        {% if tracking_list %}
            <ul class="list-group">
            {% for item in tracking_list %}
                <li class="list-group-item">{{ item.crypto_name.capitalize() }} (加入於: {{ item.added_at.strftime('%Y-%m-%d %H:%M:%S') if item.added_at else 'N/A' }})</li>
            {% endfor %}
            </ul>
        {% else %}
            <p class="fst-italic">此使用者沒有追蹤任何幣種。</p>
        {% endif %}
    </div>
</div>

<div class="card">
    <div class="card-header">
        <i data-feather="trending-up"></i> 投資記錄
    </div>
    <div class="card-body">
        {% if investments %}
            <div class="table-responsive">
                <table class="table table-sm table-hover">
                    <thead>
                        <tr>
                            <th>幣種</th>
                            <th>數量</th>
                            <th>總投入 (TWD)</th>
                            <th>買入時單價 (USD)</th>
                            <th>投資時間</th>
                        </tr>
                    </thead>
                    <tbody>
                    {% for inv in investments %}
                        <tr>
                            <td>{{ inv.crypto_name.capitalize() }}</td>
                            <td>{{ "%.6f"|format(inv.quantity) }}</td>
                            <td>{{ "%.2f"|format(inv.total_invested_value) }}</td>
                            <td>{{ "%.2f"|format(inv.price_at_investment_usd) }}</td>
                            <td>{{ inv.invested_at.strftime('%Y-%m-%d %H:%M:%S') if inv.invested_at else 'N/A' }}</td>
                        </tr>
                    {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <p class="fst-italic">此使用者沒有任何投資記錄。</p>
        {% endif %}
    </div>
</div>
{% endblock %}
"""

manage_admins_html_template = """
{% extends "admin_base.html" %}

{% block title %}管理管理員 - {{ super() }}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">管理管理員帳號</h1>
    <div class="btn-toolbar mb-2 mb-md-0">
        <a href="{{ url_for('admin.register') }}" class="btn btn-sm btn-primary">
            <i data-feather="user-plus"></i>
            新增管理員
        </a>
    </div>
</div>

<div class="table-responsive">
    <table class="table table-striped table-hover table-sm">
        <thead class="table-dark">
            <tr>
                <th>帳號</th>
                <th>管理員等級</th>
                <th class="text-center">操作</th>
            </tr>
        </thead>
        <tbody>
            {% for admin in admins %}
            <tr>
                <td>{{ admin.account }}</td>
                <td>{{ '二級管理員' if admin.level == 2 else '一級管理員' }}</td>
                <td class="text-center">
                    {% if admin.level != 2 and admin.account != session.admin_account %}
                    <form action="{{ url_for('admin.delete_admin', account=admin.account) }}" method="POST" style="display: inline-block;" onsubmit="return confirm('確定要刪除管理員 {{ admin.account }} 嗎？');">
                        <button type="submit" class="btn btn-sm btn-outline-danger" title="刪除">
                            <i data-feather="trash-2"></i> 刪除
                        </button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="3" class="text-center fst-italic">目前沒有其他管理員帳號。</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
"""

if __name__ == '__main__':
    from flask import Flask
    app_instance = Flask(__name__, template_folder='templates')
    app_instance.secret_key = os.getenv("FLASK_SECRET_KEY", "a_very_secret_and_random_key_for_admin_testing!@#$%")

    try:
        app_instance.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+mysqlconnector://root:416458237119@localhost/bilibili_db')
        app_instance.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app_instance.config['SQLALCHEMY_ECHO'] = True
        app_instance.config['SQLALCHEMY_POOL_RECYCLE'] = 280
        app_instance.config['SQLALCHEMY_POOL_TIMEOUT'] = 20
        app_instance.config['SQLALCHEMY_POOL_SIZE'] = 10
        db.init_app(app_instance)

        with app_instance.app_context():
            db.engine.connect()
            logger.info("資料庫連接成功")
    except Exception as e:
        logger.error(f"資料庫連接失敗: {str(e)}")
        print(f"資料庫連接失敗: {str(e)}")
        print("請確保 MySQL 服務已啟動，且資料庫連接資訊正確。")
        exit(1)

    with app_instance.app_context():
        try:
            db.create_all()
            logger.info("資料庫表創建成功")

            admin = AdminUser.query.filter_by(account='admin').first()
            if not admin:
                hashed_password = generate_password_hash('123456')
                new_admin = AdminUser(account='admin', password=hashed_password, level=2)
                db.session.add(new_admin)
                db.session.commit()
                logger.info("已創建初始管理員帳號")

            initial_coins = [
                ('BTC', 'bitcoin'), ('ETH', 'ethereum'), ('USDT', 'tether'),
                ('XRP', 'ripple'), ('BNB', 'binancecoin'), ('SOL', 'solana'),
                ('USDC', 'usd-coin'), ('DOGE', 'dogecoin')
            ]
            for coin_id, coin_name in initial_coins:
                if not SupportedCrypto.query.filter_by(coin_id=coin_id).first():
                    db.session.add(SupportedCrypto(coin_id=coin_id, coin_name=coin_name))
            db.session.commit()
            logger.info("幣種列表初始化成功")
            
        except Exception as e:
            logger.error(f"資料庫初始化錯誤: {str(e)}")
            print(f"資料庫初始化錯誤: {str(e)}")
            exit(1)

    app_instance.register_blueprint(admin_bp)

    template_dir = 'templates/admin'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    templates_to_create = {
        "admin_base.html": admin_base_html_template,
        "login.html": login_html_template,
        "register.html": register_html_template,
        "dashboard.html": dashboard_html_template,
        "manage_cryptos.html": manage_cryptos_html_template,
        "add_crypto.html": add_crypto_html_template,
        "edit_crypto.html": edit_crypto_html_template,
        "manage_users.html": manage_users_html_template,
        "view_user_details.html": view_user_details_html_template,
        "manage_admins.html": manage_admins_html_template,
    }
    for filename, content in templates_to_create.items():
        filepath = os.path.join(template_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已創建模板檔案: {filepath}")

    print("Flask 應用程式即將啟動於 http://127.0.0.1:5001/admin")
    print("請確保 MySQL 資料庫已設置並運行。")
    print("初始管理員帳號：admin")
    print("初始管理員密碼：123456")
    app_instance.run(debug=True, port=5001)