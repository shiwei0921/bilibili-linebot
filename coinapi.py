print(" 正在執行 Janice 合併請求版 coinapi.py", flush=True)

import requests
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import schedule
import time

#  資料庫連線
DB_NAME = 'beli'
DB_URL = f'mysql+pymysql://root:12345678@localhost/{DB_NAME}'

#  測試資料庫連線
try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print(" 成功連接到資料庫！", flush=True)
except Exception as e:
    print(f" 資料庫連線失敗：{e}", flush=True)
    exit(1)

# CoinGecko ID → 縮寫（symbol）對照表
coin_symbol_map = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'tether': 'USDT',
    'ripple': 'XRP',
    'binancecoin': 'BNB',
    'solana': 'SOL',
    'usd-coin': 'USDC',
    'dogecoin': 'DOGE'
}

#  幣價抓取與寫入
def fetch_and_save():
    coins = list(coin_symbol_map.keys())
    vs_currency = 'usd'
    now = datetime.now().replace(second=0, microsecond=0)

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': ','.join(coins),
        'vs_currencies': vs_currency,
        'include_24hr_vol': 'true'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; JaniceBot/1.0)'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            print("f API error {response.status_code}: {response.text}", flush=True)
            return
        data = response.json()
    except Exception as e:
        print(f" 發生 API 錯誤：{e}", flush=True)
        return

    try:
        with engine.begin() as conn:  #  使用單一交易連線
            for coin in coins:
                symbol = coin_symbol_map[coin]
                price = data[coin][vs_currency]

                #  更新或插入 price 資料
                sql_price = text("""
                    INSERT INTO price (coin_id, price, update_time)
                    VALUES (:coin_id, :price, :update_time)
                    ON DUPLICATE KEY UPDATE
                        price = VALUES(price),
                        update_time = VALUES(update_time)
                """)
                conn.execute(sql_price, {
                    'coin_id': symbol,
                    'price': price,
                    'update_time': now
                })

                # 新增一筆至 price_history
                sql_history = text("""
                    INSERT INTO price_history (coin_id, price, receiving_time)
                    VALUES (:coin_id, :price, :receiving_time)
                """)
                conn.execute(sql_history, {
                    'coin_id': symbol,
                    'price': price,
                    'receiving_time': now
                })

                print(f"[{now}]  Inserted/Updated: {symbol}, Price: {price}", flush=True)
    except Exception as e:
        print(f"[{now}]  寫入失敗：{e}", flush=True)
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] Global insert error: {e}\n")

#  立即執行一次
fetch_and_save()

#  每 5 分鐘排程
schedule.every(5).minutes.do(fetch_and_save)

print(" 開始監控中，每 5 分鐘更新幣價...", flush=True)

while True:
    schedule.run_pending()
    time.sleep(1)

