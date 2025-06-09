CREATE TABLE user_list(
    user_id VARCHAR(50) PRIMARY KEY,
    BALANCE FLOAT DEFAULT 5000000
);

CREATE TABLE coin_list(
    coin_id VARCHAR(10) PRIMARY KEY,
    coin_name VARCHAR(50)
);

CREATE TABLE follow_list(
    user_id VARCHAR(50) ,
    coin_id VARCHAR(10) ,
    PRIMARY KEY(user_id,coin_id),
    FOREIGN KEY (user_id) REFERENCES user_list(user_id),
    FOREIGN KEY (coin_id) REFERENCES coin_list(coin_id)
);

CREATE TABLE history_trade(
    user_id VARCHAR(50) ,
    coin_id VARCHAR(10) ,
    quantity FLOAT,
    price FLOAT,
    amount FLOAT,
    action ENUM('buy', 'sell'),
    trade_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id,coin_id,trade_time),
    FOREIGN KEY (user_id) REFERENCES user_list(user_id),
    FOREIGN KEY (coin_id) REFERENCES coin_list(coin_id)
);

CREATE TABLE price (
    coin_id VARCHAR(10) PRIMARY KEY,
    price FLOAT,
    `update_time` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
    FOREIGN KEY (coin_id) REFERENCES coin_list(coin_id)
);

CREATE TABLE price_history (
    coin_id VARCHAR(10),
    price FLOAT,
    receiving_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (coin_id, receiving_time),
    FOREIGN KEY (coin_id) REFERENCES coin_list(coin_id)
);

CREATE TABLE ROOT(
    account VARCHAR(50) PRIMARY KEY,
    password VARCHAR(50)
);

INSERT INTO coin_list (coin_id, coin_name) VALUES
('BTC', 'bitcoin'),
('ETH', 'ethereum'),
('USDT', 'tether'),
('XRP', 'ripple'),
('BNB', 'binancecoin'),
('SOL', 'solana'),
('USDC', 'usd-coin'),
('DOGE', 'dogecoin')
ON DUPLICATE KEY UPDATE coin_name = VALUES(coin_name);
