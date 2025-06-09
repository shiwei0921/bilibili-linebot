from flask import Flask, request ,render_template,redirect,jsonify,send_from_directory, session
from linebot import LineBotApi, WebhookHandler
from flask_session import Session 
from linebot.models import FollowEvent, MessageEvent, TextSendMessage
import pymysql
import os
from dotenv import load_dotenv
from threading import Timer
from datetime import datetime
from flask_cors import CORS

# 載入 .env 檔
load_dotenv(dotenv_path="pwd.env")

# 初始化 Flask app
bilibili = Flask(__name__, static_folder="dist", static_url_path="/")
CORS(bilibili, supports_credentials=True)


# ✅ 開啟 session 支援
bilibili.secret_key = "bilibili.secret_key"  # 可改成 os.getenv("SECRET_KEY") 放進 .env
bilibili.config["SESSION_TYPE"] = "filesystem"
Session(bilibili)
# LINE BOT 初始化
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))


# 資料庫連線
def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        port=int(os.getenv("DB_PORT")),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_rich_menu_id_by_name(target_name):
    menus = line_bot_api.get_rich_menu_list()
    for menu in menus:
        if menu.name == target_name:
            return menu.rich_menu_id
    return None

# ✅ 輔助函式：從網址補 session 中的 uid
def get_user_id():
    user_id = session.get("uid")
    if not user_id:
        user_id = request.args.get("user_id", "").strip()
        if user_id:
            session["uid"] = user_id
            print(" 從網址取得 user_id 並寫入 session：", user_id)
    return user_id

# ✅ 輔助函式：從網址補 session 中的 uid

@bilibili.route("/set_uid", methods=["POST"])
def set_uid():
    data = request.get_json()
    if not data or "uid" not in data:
        print(" 錯誤：set_uid 接收到空資料或缺少 uid")
        return jsonify({"error": "missing uid"}), 400

    uid = str(data.get("uid", "")).strip()
    session["uid"] = uid
    print(" 設定 session 中的 UID：", uid)
    return jsonify({"msg": "success"})

# 接收 LINE Webhook 的主路由
# ✅ LINE Webhook：處理事件，包括 FollowEvent
@bilibili.route("/webhook", methods=["GET", "POST"])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature")
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(" Webhook 處理失敗：", e)
    return "OK"

@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    print(" 新使用者加入：", user_id)

    conn = get_conn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM user_list WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO user_list (user_id, balance) VALUES (%s, %s)", (user_id, 5000000))
            conn.commit()
    conn.close()

    rich_menu_id = get_rich_menu_id_by_name("default")
    if rich_menu_id:
        line_bot_api.link_rich_menu_to_user(user_id, rich_menu_id)
        print(" Rich Menu 綁定成功")

    entry_url = f"https://a7b5-211-72-73-207.ngrok-free.app/#/?user_id={user_id}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"歡迎加入幣哩幣哩 \n請點選以下網址或按鈕或按鈕開啟功能選單：\n{entry_url}")
    )


# 使用者傳訊息事件
@handler.add(MessageEvent)
def handle_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="請點選以下按鈕選擇要使用的功能")
    )



# 子功能：新增追蹤
def add_follow(user_id, coin_id):
    print("[後端] 新增追蹤：", user_id, coin_id)
    connect = get_conn()
    cursor = connect.cursor()
    cursor.execute(
        "INSERT IGNORE INTO follow_list (user_id, coin_id) VALUES (%s, %s)",
        (user_id, coin_id)
    )
    connect.commit()

# 子功能：移除追蹤
def remove_follow(user_id, coin_id):
    connect = get_conn()
    cursor = connect.cursor()
    cursor.execute(
        "DELETE FROM follow_list WHERE user_id = %s AND coin_id = %s",
        (user_id, coin_id)
    )
    connect.commit()

# 主路由：追蹤清單頁（顯示 + 新增 + 移除）
@bilibili.route("/follow_list", methods=["GET", "POST"])
def follow_list():
    user_id = get_user_id()
    print("[後端] 有進來 /follow_list")

    if request.method == "POST":
        action = request.form.get("action")
        coin_id = request.form.get("coin_id")

        try:
            conn = get_conn()
            cursor = conn.cursor()

            if action == "add":
                cursor.execute(
                    "INSERT IGNORE INTO follow_list (user_id, coin_id) VALUES (%s, %s)",
                    (user_id, coin_id)
                )
            elif action == "remove":
                cursor.execute(
                    "DELETE FROM follow_list WHERE user_id = %s AND coin_id = %s",
                    (user_id, coin_id)
                )
            conn.commit()
            return redirect(f"/follow_list?user_id={user_id}")

        except Exception as e:
            print("❌ POST 操作失敗：", e)
            return jsonify({"error": "資料庫錯誤"}), 500

        finally:
            cursor.close()
            conn.close()

    # --- GET 方法 ---
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.coin_id, c.coin_name, p.price
            FROM follow_list f
            JOIN coin_list c ON f.coin_id = c.coin_id
            JOIN price p ON c.coin_id = p.coin_id
            WHERE f.user_id = %s
        """, (user_id,))
        tracked = cursor.fetchall()

        cursor.execute("""
            SELECT coin_id, coin_name
            FROM coin_list
            WHERE coin_id NOT IN (
                SELECT coin_id FROM follow_list WHERE user_id = %s
            )
        """, (user_id,))
        untracked = cursor.fetchall()

        return jsonify({
            "tracked": tracked,
            "untracked": untracked,
            "user_id": user_id
        })

    except Exception as e:
        print("❌ GET 查詢失敗：", e)
        return jsonify({"error": "伺服器錯誤"}), 500

    finally:
        cursor.close()
        conn.close()


#漲跌幅通知設定
def check_price_fluctuations():
    connect = get_conn()
    cursor = connect.cursor()

    cursor.execute("""
        SELECT f.user_id, f.coin_id,
               p_now.price AS current_price,
               p_prev.price AS previous_price
        FROM follow_list f
        JOIN price p_now ON f.coin_id = p_now.coin_id
        JOIN price_history p_prev ON f.coin_id = p_prev.coin_id
        WHERE p_prev.receiving_time <= NOW() - INTERVAL 5 MINUTE
            AND p_prev.receiving_time = (
              SELECT MAX(receiving_time)
              FROM price_history
              WHERE coin_id = f.coin_id AND receiving_time <= NOW() - INTERVAL 5 MINUTE
          )
    """)
    results = cursor.fetchall()

    for row in results:
        now = row["current_price"]
        before = row["previous_price"]
        if before == 0: continue  # 避免除以 0

        change = (now - before) / before
        if abs(change) >= 0.05:
            percent = round(change * 100, 2)
            msg = f"{row['coin_id']} 在 5 分鐘內漲跌 {percent}%（由 {before} → {now}）"
            line_bot_api.push_message(row["user_id"], TextSendMessage(text=msg))

def record_price_snapshot():
    connect = get_conn()
    cursor = connect.cursor()
    cursor.execute("SELECT coin_id, price FROM price")
    prices = cursor.fetchall()

    for row in prices:
        cursor.execute("""
            INSERT INTO price_history (coin_id, price, receiving_time)
            VALUES (%s, %s, NOW())
        """, (row["coin_id"], row["price"]))
    connect.commit()
#將用不到的資料刪除
def clean_old_history():
    connect = get_conn()
    cursor = connect.cursor()
    cursor.execute("""
        DELETE FROM price_history
        WHERE receiving_time < NOW() - INTERVAL 8 DAY
    """)
    connect.commit()

def schedule_price_check():
    record_price_snapshot()
    check_price_fluctuations()
    clean_old_history() 
    Timer(300, schedule_price_check).start()  # 每 5 分鐘執行一次
#獲取及時幣價
@bilibili.route("/api/current_prices", methods=["GET"])
def current_prices():
    connect = get_conn()
    cursor = connect.cursor()
    cursor.execute("SELECT coin_id, price FROM price")
    prices = cursor.fetchall()
    return jsonify(prices)

#趨勢圖
@bilibili.route("/api/price_history/<coin_id>")
def get_price_history(coin_id):
    chart_type = request.args.get("type", "1d")  # 預設為 1 天
    day_map = {"1d": 1, "3d": 3, "7d": 7}
    days = day_map.get(chart_type)

    if not days:
        return jsonify({"error": "圖表類型不支援"}), 400

    try:
        conn = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        connect = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT receiving_time AS label, price
            FROM price_history
            WHERE coin_id = %s AND receiving_time >= NOW() - INTERVAL %s DAY
            ORDER BY receiving_time ASC
        """, (coin_id, days))
        data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        print(" price_history 查詢失敗：", e)
        return jsonify({"error": "查詢失敗"}), 500



# 顯示所有幣種清單（供交易用的下拉選單使用）
@bilibili.route("/api/coin_list", methods=["GET"])
def coin_list():
    connect = get_conn()
    cursor = connect.cursor()
    cursor.execute("SELECT coin_id, coin_name FROM coin_list")
    return jsonify(cursor.fetchall())



# 查詢目前餘額 + 幣價（GET）執行交易時要確認目前餘額以及獲取即時幣價
@bilibili.route("/api/trade_info", methods=["GET"])
def get_trade_info():
    user_id = get_user_id()
    coin_id = request.args.get("coin_id")
    connect = get_conn()
    cursor = connect.cursor()

    # 查餘額
    cursor.execute("SELECT balance FROM user_list WHERE user_id = %s", (user_id,))
    balance_data = cursor.fetchone()
    balance = balance_data["balance"] if balance_data else 0

    # 查幣價
    price = None
    if coin_id:
        cursor.execute("SELECT price FROM price WHERE coin_id = %s", (coin_id,))
        price_data = cursor.fetchone()
        price = price_data["price"] if price_data else None

    return jsonify({
        "balance": round(balance, 2),
        "coin_price": round(price, 2) if price else None
    })


# 執行交易（POST）- 加入0.1%手續費
@bilibili.route("/api/trade", methods=["POST"])
def trade():
    data = request.json
    user_id = get_user_id()
    coin_id = data.get("coin_id")
    action = data.get("action")  # 'buy' 或 'sell'
    quantity = data.get("quantity")  # 優先處理數量
    total = data.get("total")    # 如果 是填金額才處理 total 金額
    connect = get_conn()
    cursor = connect.cursor()

    # 查價格
    cursor.execute("SELECT price FROM price WHERE coin_id = %s", (coin_id,))
    price_data = cursor.fetchone()
    if not price_data:
        return jsonify({"error": "幣種不存在"}), 400
    price = price_data["price"]

    # 計算交易數量與總金額
    if not quantity and total:
        quantity = float(total) / price
    else:
        quantity = float(quantity)
    total_price = price * quantity
    
    # 計算手續費 (0.1%)
    transaction_fee = total_price * 0.001
    
    # 查使用者餘額
    cursor.execute("SELECT balance FROM user_list WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()
    if not user_data:
        return jsonify({"error": "使用者不存在"}), 400
    balance = user_data["balance"]

    if action == "buy":
        # 買入時：需要支付交易金額 + 手續費
        total_cost = total_price + transaction_fee
        
        if total_cost > balance:
            return jsonify({
                "status": "fail", 
                "reason": f"餘額不足（需要 {round(total_cost, 2)}，包含手續費 {round(transaction_fee, 2)}）"
            }), 400

        # 扣款與記錄交易
        new_balance = balance - total_cost
        cursor.execute("UPDATE user_list SET balance = %s WHERE user_id = %s", (new_balance, user_id))
        cursor.execute("""
            INSERT INTO history_trade (user_id, coin_id, action, quantity, price, trade_time)
            VALUES (%s, %s, 'buy', %s, %s, %s)
        """, (user_id, coin_id, quantity, price, datetime.now()))
        
        # 記錄手續費（可選，作為交易紀錄）
        cursor.execute("""
            INSERT INTO history_trade (user_id, coin_id, action, quantity, price, trade_time)
            VALUES (%s, 'FEE', 'fee', %s, 1, %s)
        """, (user_id, transaction_fee, datetime.now()))
        
        connect.commit()

        return jsonify({
            "status": "success",
            "action": "buy",
            "new_balance": round(new_balance, 2),
            "transaction_fee": round(transaction_fee, 2),
            "total_cost": round(total_cost, 2)
        })

    elif action == "sell":
        # 查持有數量
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN action = 'buy' THEN quantity ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN action = 'sell' THEN quantity ELSE 0 END), 0) AS holding_quantity
            FROM history_trade
            WHERE user_id = %s AND coin_id = %s
        """, (user_id, coin_id))
        result = cursor.fetchone()
        holding_quantity = result["holding_quantity"]

        sell_quantity = float(data.get("quantity", 0))
        if sell_quantity > holding_quantity:
            return jsonify({"status": "fail", "reason": "持有數量不足"}), 400

        # 賣出時：獲得交易金額 - 手續費
        sell_total = sell_quantity * price
        sell_fee = sell_total * 0.001
        net_income = sell_total - sell_fee

        # 加錢與記錄交易
        new_balance = balance + net_income
        cursor.execute("UPDATE user_list SET balance = %s WHERE user_id = %s", (new_balance, user_id))
        cursor.execute("""
            INSERT INTO history_trade (user_id, coin_id, action, quantity, price, trade_time)
            VALUES (%s, %s, 'sell', %s, %s, %s)
        """, (user_id, coin_id, sell_quantity, price, datetime.now()))
        
        # 記錄手續費
        cursor.execute("""
            INSERT INTO history_trade (user_id, coin_id, action, quantity, price, trade_time)
            VALUES (%s, 'FEE', 'fee', %s, 1, %s)
        """, (user_id, sell_fee, datetime.now()))
        
        connect.commit()

        return jsonify({
            "status": "success",
            "action": "sell",
            "new_balance": round(new_balance, 2),
            "transaction_fee": round(sell_fee, 2),
            "net_income": round(net_income, 2),
            "gross_income": round(sell_total, 2)
        })

    return jsonify({"status": "fail", "reason": "操作無效"}), 400
#


    

#餘額損益表查詢
@bilibili.route("/api/profit", methods=["GET"])
def get_profit():
    user_id = get_user_id()
    connect = get_conn()
    cursor = connect.cursor()

    # 1. 查餘額
    cursor.execute("SELECT balance FROM user_list WHERE user_id = %s", (user_id,))
    balance_data = cursor.fetchone()
    balance = balance_data["balance"] if balance_data else 0

    # 2. 查交易紀錄
    cursor.execute("""
        SELECT
            t.coin_id,
            SUM(CASE WHEN t.action = 'buy' THEN t.quantity ELSE 0 END) AS total_buy_qty,
            SUM(CASE WHEN t.action = 'buy' THEN t.quantity * t.price ELSE 0 END) AS total_buy_cost,
            SUM(CASE WHEN t.action = 'sell' THEN t.quantity ELSE 0 END) AS total_sell_qty,
            SUM(CASE WHEN t.action = 'sell' THEN t.quantity * t.price ELSE 0 END) AS total_sell_income
        FROM history_trade t
        WHERE t.user_id = %s
        GROUP BY t.coin_id
    """, (user_id,))
    trades = cursor.fetchall()

    portfolio = []

    total_market_value = 0
    total_buy_cost = 0
    total_sell_income = 0
    total_net_profit = 0

    for row in trades:
        coin_id = row["coin_id"]
        total_buy_qty = row["total_buy_qty"] or 0
        total_sell_qty = row["total_sell_qty"] or 0
        quantity = total_buy_qty - total_sell_qty

        if quantity <= 0:
            continue  #  不顯示已清空的幣

        buy_cost = row["total_buy_cost"] or 0
        sell_income = row["total_sell_income"] or 0
        average_cost = (buy_cost / total_buy_qty) if total_buy_qty > 0 else 0

        # 查市價
        cursor.execute("SELECT price FROM price WHERE coin_id = %s", (coin_id,))
        price_data = cursor.fetchone()
        current_price = price_data["price"] if price_data else 0

        market_value = quantity * current_price
        net_profit = market_value + sell_income - buy_cost

        total_market_value += market_value
        total_buy_cost += buy_cost
        total_sell_income += sell_income
        total_net_profit += net_profit

        portfolio.append({
            "coin_id": coin_id,
            "quantity": round(quantity, 6),
            "average_buy_cost": round(average_cost, 2),
            "current_price": round(current_price, 2),
            "net_profit": round(net_profit, 2)
        })

    total_return_rate = (total_net_profit / total_buy_cost) * 100 if total_buy_cost > 0 else 0

    return jsonify({
        "balance": round(balance, 2),
        "portfolio": portfolio,
        "summary": {
            "total_market_value": round(total_market_value, 2),
            "total_buy_cost": round(total_buy_cost, 2),
            "total_net_profit": round(total_net_profit, 2),
            "total_return_rate": round(total_return_rate, 2)  # %
        }
    })

#reset balance

@bilibili.route("/api/reset", methods=["POST"])
def reset_user():
    data = request.get_json()
    user_id = get_user_id()
    print("[後端] 收到重置請求，user_id：", user_id)

    if not user_id:
        return jsonify({"error": "請提供 user_id"}), 400

    try:
        connect = get_conn()
        cursor = connect.cursor()

        # 刪除該使用者的所有交易紀錄
        cursor.execute("DELETE FROM history_trade WHERE user_id = %s", (user_id,))

        # 將使用者的餘額重設為 5,000,000 元
        cursor.execute("UPDATE user_list SET balance = 5000000 WHERE user_id = %s", (user_id,))

        connect.commit()
        return jsonify({"message": "已成功重置模擬投資帳號"}), 200

    except Exception as e:
        print(" reset_user 錯誤：", e)
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            cursor.close()
            connect.close()
        except:
            pass

@bilibili.route("/", defaults={"path": ""})
@bilibili.route("/<path:path>")
def serve_react(path):
    print(" 使用者請求：", path)
    full_path = os.path.join(bilibili.static_folder, path or "index.html")
    print(" 嘗試讀取檔案：", full_path)

    # 如果是靜態資源（js, css, png...）就直接回傳
    if path != "" and os.path.exists(full_path):
        return send_from_directory(bilibili.static_folder, path)
    # 否則一律送出 index.html（給 React 前端路由用）
    else:
        return send_from_directory(bilibili.static_folder, "index.html")
    

#@bilibili.route("/set_uid", methods=["POST"])
#def set_uid():
#    data = request.get_json()
#    user_id = data.get("uid")

#    try:
#        connect = get_conn()
#        cursor = connect.cursor()
#        cursor.execute("SELECT * FROM user_list WHERE user_id = %s", (user_id,))
#        result = cursor.fetchone()

#        if not result:
#            cursor.execute("INSERT INTO user_list (user_id, balance) VALUES (%s, %s)", (user_id, 5000000))
#            connect.commit()
#            return jsonify({"message": "使用者已新增"}), 200
##        else:
#            return jsonify({"message": "使用者已存在"}), 200

#    except Exception as e:
#        return jsonify({"error": str(e)}), 500

# 執行 Flask App
if __name__ == "__main__":
    schedule_price_check()
    bilibili.run(host="0.0.0.0", port=5000)

