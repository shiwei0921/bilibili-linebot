import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";

export default function Trade() {
  const navigate = useNavigate();

  const [allCoins, setAllCoins] = useState([]);
  const [coinId, setCoinId] = useState("");
  const [cash, setCash] = useState(0);
  const [holdings, setHoldings] = useState([]);
  const [tradeType, setTradeType] = useState("buy");
  const [amount, setAmount] = useState("");
  const [total, setTotal] = useState("");
  const [price, setPrice] = useState(0);
  const [message, setMessage] = useState("");

  // 計算手續費
  const calculateFee = () => {
    const numTotal = parseFloat(total);
    return isNaN(numTotal) ? 0 : numTotal * 0.001; // 0.1%
  };

  // 計算總成本（買入時）或淨收入（賣出時）
  const calculateFinalAmount = () => {
    const numTotal = parseFloat(total);
    const fee = calculateFee();
    
    if (isNaN(numTotal)) return 0;
    
    if (tradeType === "buy") {
      return numTotal + fee; // 買入：交易金額 + 手續費
    } else {
      return numTotal - fee; // 賣出：交易金額 - 手續費
    }
  };

  useEffect(() => {
    fetch("api/coin_list", { credentials: "include" })
      .then(r => r.json())
      .then(data => {
        setAllCoins(data);
        if (data.length > 0) setCoinId(data[0].coin_id);
      })
      .catch(err => {
        console.error("載入幣種清單失敗：", err);
        setMessage("❌ 無法取得幣種清單，請稍後再試");
      });
  }, []);

  useEffect(() => {
    if (!coinId) return;

    fetch(`api/trade_info?coin_id=${coinId}`, { credentials: "include" })
      .then(r => r.json())
      .then(data => {
        setCash(data.balance ?? 0);
        setPrice(data.coin_price ?? 0);
      })
      .catch(err => {
        console.error("載入幣價或餘額失敗：", err);
        setMessage("❌ 無法取得即時幣價或帳戶資料");
      });

    fetch(`/api/profit`, { credentials: "include" })
      .then(r => r.json())
      .then(data => {
        setHoldings(data.portfolio ?? []);
      })
      .catch(err => {
        console.error("載入持倉資料失敗：", err);
      });
  }, [coinId, message]);

  function handleAmountChange(val) {
    setAmount(val);
    if (val !== "" && !isNaN(val)) {
      setTotal((parseFloat(val) * price).toFixed(2));
    } else {
      setTotal("");
    }
  }

  function handleTotalChange(val) {
    setTotal(val);
    if (val !== "" && !isNaN(val)) {
      setAmount((parseFloat(val) / price).toFixed(6));
    } else {
      setAmount("");
    }
  }

  async function handleConfirm() {
    const numAmount = parseFloat(amount);
    const numTotal = parseFloat(total);
    const fee = calculateFee();
    const finalAmount = calculateFinalAmount();

    if (!numAmount || !numTotal || isNaN(numAmount) || isNaN(numTotal) || numAmount <= 0 || numTotal <= 0) {
      setMessage("請輸入大於0的有效數量和金額");
      return;
    }

    // 檢查餘額是否足夠（買入時需要考慮手續費）
    if (tradeType === "buy" && finalAmount > cash) {
      setMessage(`❌ 餘額不足！需要 $${finalAmount.toFixed(2)}（包含手續費 $${fee.toFixed(2)}），但您只有 $${cash.toFixed(2)}`);
      return;
    }

    try {
      const res = await fetch("/api/trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          coin_id: coinId,
          action: tradeType,
          quantity: numAmount
        })
      });

      const data = await res.json();
      if (res.ok && data.status === "success") {
        const feeText = data.transaction_fee ? `，手續費 $${data.transaction_fee}` : "";
        setMessage(`✅ 交易成功！${tradeType === "buy" ? "已買入" : "已賣出"} ${numAmount} ${coinId}${feeText}`);
        setAmount("");
        setTotal("");
      } else {
        setMessage("❌ " + (data.reason || "交易失敗"));
      }
    } catch (err) {
      console.error("交易錯誤：", err);
      setMessage("❌ 系統錯誤，請稍後再試");
    }
  }

  const holdObj = holdings.find(c => c.coin_id === coinId);
  const holdAmount = holdObj?.quantity || 0;
  const fee = calculateFee();
  const finalAmount = calculateFinalAmount();

  return (
    <div className="crypto-glass trade-page">
      <button className="glass-btn" style={{ marginBottom: 10, width: "fit-content", padding: "9px 30px" }} onClick={() => navigate("/")}>回到主頁</button>
      <h1 className="title2" style={{ marginLeft: 18 }}>Trade</h1>

      <div style={{ marginLeft: 20, marginBottom: 16, fontWeight: 500, fontSize: "1.5em", color: "#aee1fc" }}>
        目前餘額：<span style={{ color: "#5ee7ff" }}>${cash.toLocaleString("en-US", { minimumFractionDigits: 2 })}</span>
      </div>

      <div style={{ marginLeft: 20, marginBottom: 14 }}>
        <label style={{ marginRight: 8, color: "#aee1fc", fontSize: "1.5em" }}>交易幣種：</label>
        <select className="coin-select" value={coinId} onChange={e => setCoinId(e.target.value)}>
          {allCoins.map(c => (
            <option key={c.coin_id} value={c.coin_id}>{c.coin_name} ({c.coin_id})</option>
          ))}
        </select>
      </div>

      <div style={{ marginLeft: 20, marginBottom: 14, color: "#aee1fc", fontSize: "1.5em" }}>
        即時幣價：<b style={{ color: "#5ee7ff" }}>${price}</b>
      </div>

      <div style={{ marginLeft: 20, marginBottom: 14, color: "#aee1fc", fontSize: "1.5em" }}>
        目前持有：<b style={{ color: "#82ffb8" }}>{holdAmount} {coinId}</b>
      </div>

      <div style={{ marginLeft: 20, marginBottom: 14 }}>
        <label style={{ marginRight: 8, color: "#aee1fc", fontSize: "1.5em" }}>買/賣：</label>
        <select className="coin-select" value={tradeType} onChange={e => setTradeType(e.target.value)}>
          <option value="buy">買入 (Buy)</option>
          <option value="sell">賣出 (Sell)</option>
        </select>
      </div>

      <div style={{ marginLeft: 20, marginBottom: 10, display: "flex", alignItems: "center", gap: 18 }}>
        <div>
          <label style={{ marginRight: 8, color: "#aee1fc", fontSize: "1.5em" }}>數量(顆)：</label>
          <input
            type="number"
            style={{ width: 90, padding: 4, borderRadius: 6, border: "1px solid #89b", marginRight: 8, fontSize: "1.5em" }}
            value={amount}
            onChange={e => handleAmountChange(e.target.value)}
          />
        </div>
        <div>
          <label style={{ marginRight: 8, color: "#aee1fc", fontSize: "1.5em" }}>金額(美元)：</label>
          <input
            type="number"
            style={{ width: 120, padding: 4, borderRadius: 6, border: "1px solid #89b", fontSize: "1.5em" }}
            value={total}
            onChange={e => handleTotalChange(e.target.value)}
          />
        </div>
      </div>

      {/* 手續費計算區域 */}
      {total && !isNaN(parseFloat(total)) && (
        <div style={{ 
          marginLeft: 20, 
          marginBottom: 16,
          padding: "12px 16px",
          background: "rgba(255,255,255,0.08)",
          borderRadius: 8,
          border: "1px solid rgba(94,231,255,0.3)",
          maxWidth: "400px"
        }}>
          <div style={{ color: "#aee1fc", fontSize: "1.2em", marginBottom: 8, fontWeight: "bold" }}>
            📊 交易明細
          </div>
          
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ color: "#aee1fc" }}>交易金額：</span>
            <span style={{ color: "#fff", fontWeight: "bold" }}>${parseFloat(total).toFixed(2)}</span>
          </div>
          
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ color: "#aee1fc" }}>手續費 (0.1%)：</span>
            <span style={{ color: "#ffb74d", fontWeight: "bold" }}>-${fee.toFixed(2)}</span>
          </div>
          
          <div style={{ 
            borderTop: "1px solid rgba(255,255,255,0.2)", 
            paddingTop: 8, 
            marginTop: 8,
            display: "flex", 
            justifyContent: "space-between" 
          }}>
            <span style={{ color: "#aee1fc", fontWeight: "bold" }}>
              {tradeType === "buy" ? "總需支付：" : "實際收到："}
            </span>
            <span style={{ 
              color: tradeType === "buy" ? "#f44336" : "#4caf50", 
              fontWeight: "bold",
              fontSize: "1.1em"
            }}>
              {tradeType === "buy" ? "-" : "+"}${finalAmount.toFixed(2)}
            </span>
          </div>
          
          {tradeType === "buy" && finalAmount > cash && (
            <div style={{ 
              marginTop: 8, 
              color: "#f44336", 
              fontSize: "0.9em",
              fontWeight: "bold"
            }}>
              ⚠️ 餘額不足！還需要 ${(finalAmount - cash).toFixed(2)}
            </div>
          )}
        </div>
      )}

      <div style={{ marginLeft: 20, marginTop: 20 }}>
        <button 
          className="glass-btn" 
          style={{ 
            width: 120, 
            padding: "8px 0",
            opacity: (tradeType === "buy" && finalAmount > cash) ? 0.5 : 1,
            cursor: (tradeType === "buy" && finalAmount > cash) ? "not-allowed" : "pointer"
          }} 
          onClick={handleConfirm}
          disabled={tradeType === "buy" && finalAmount > cash}
        >
          Confirm
        </button>
      </div>

      {message && (
        <div style={{
          margin: "20px 0 0 20px",
          color: message.includes("成功") ? "#09e679" : "#f34b6e",
          fontWeight: 600,
          fontSize: "1.08em"
        }}>
          {message}
        </div>
      )}
    </div>
  );
}