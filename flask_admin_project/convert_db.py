import mysql.connector
from werkzeug.security import generate_password_hash
import time
import sys
import socket
import subprocess

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def check_xampp_mysql():
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'], capture_output=True, text=True)
        print("\n=== XAMPP MySQL 進程狀態 ===")
        print(result.stdout)
        return "mysqld.exe" in result.stdout
    except Exception as e:
        print(f"檢查進程時發生錯誤: {e}")
        return False

def setup_mysql_database():
    """設置 MySQL 資料庫"""
    try:
        if not check_xampp_mysql():
            print("請先啟動 XAMPP 的 MySQL 服務")
            return False

        if not check_port(3306):
            print("端口 3306 已被占用，請檢查是否有其他 MySQL 實例正在運行")
            return False

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678",
            port=3306
        )
        cursor = conn.cursor()
        print("成功連接到 MySQL 資料庫")

        cursor.execute("CREATE DATABASE IF NOT EXISTS beli")
        cursor.execute("USE beli")
        print("成功創建/選擇資料庫 beli")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ROOT (
                account VARCHAR(50) PRIMARY KEY,
                password VARCHAR(255),
                level INTEGER DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coin_list (
                coin_id VARCHAR(10) PRIMARY KEY,
                coin_name VARCHAR(50)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_list (
                user_id VARCHAR(50) PRIMARY KEY,
                balance FLOAT DEFAULT 5000000
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history_trade (
                user_id VARCHAR(50),
                coin_id VARCHAR(10),
                trade_time TIMESTAMP,
                quantity FLOAT,
                price FLOAT,
                amount FLOAT,
                action ENUM('buy', 'sell'),
                PRIMARY KEY (user_id, coin_id, trade_time),
                FOREIGN KEY (user_id) REFERENCES user_list(user_id),
                FOREIGN KEY (coin_id) REFERENCES coin_list(coin_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS follow_list (
                user_id VARCHAR(50),
                coin_id VARCHAR(10),
                PRIMARY KEY (user_id, coin_id),
                FOREIGN KEY (user_id) REFERENCES user_list(user_id),
                FOREIGN KEY (coin_id) REFERENCES coin_list(coin_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price (
                coin_id VARCHAR(10) PRIMARY KEY,
                price FLOAT,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (coin_id) REFERENCES coin_list(coin_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                coin_id VARCHAR(10),
                price FLOAT,
                receiving_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (coin_id, receiving_time),
                FOREIGN KEY (coin_id) REFERENCES coin_list(coin_id)
            )
        ''')

        # 插入預設管理員帳號（帳號：admin，密碼：123456）
        admin_password = generate_password_hash('123456', method='pbkdf2:sha256')
        cursor.execute('''
            INSERT INTO ROOT (account, password, level)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE password = VALUES(password), level = VALUES(level)
        ''', ('admin', admin_password, 2))

        default_coins = [
            ('BTC', 'bitcoin'),
            ('ETH', 'ethereum'),
            ('USDT', 'tether'),
            ('XRP', 'ripple'),
            ('BNB', 'binancecoin'),
            ('SOL', 'solana'),
            ('USDC', 'usd-coin'),
            ('DOGE', 'dogecoin')
        ]
        cursor.executemany('''
            INSERT IGNORE INTO coin_list (coin_id, coin_name)
            VALUES (%s, %s)
        ''', default_coins)

        conn.commit()
        conn.close()
        print("MySQL 資料庫設定完成！")
    except Exception as e:
        print(f"設定 MySQL 資料庫時發生錯誤: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup_mysql_database() 