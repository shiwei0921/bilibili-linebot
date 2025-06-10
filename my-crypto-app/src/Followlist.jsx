import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";

// 改進的趨勢圖元件（更大、更清楚）
function TrendChart({ history, coinId }) {
  if (!history || history.length === 0) return (
    <div style={{ padding: 24, color: "#bbb", textAlign: "center", fontSize: "1.1em" }}>暫無資料</div>
  );

  const prices = history.map(d => d.price);
  const max = Math.max(...prices);
  const min = Math.min(...prices);
  const maxIndex = prices.indexOf(max);
  const minIndex = prices.indexOf(min);
  
  // 增大圖表尺寸
  const W = 350, H = 120;
  const Y_LABEL_W = 60;
  const PRICE_TAG_W = 70;
  const PADDING = 20;

  const points = history.map((d, i) => [
    Y_LABEL_W + (i / (history.length - 1)) * (W - Y_LABEL_W - PRICE_TAG_W),
    PADDING + ((max - d.price) / (max - min + 1e-6)) * (H - PADDING * 2)
  ]);
  
  const pointsStr = points.map(p => p.join(",")).join(" ");
  const areaPointsStr = points
    .map(p => p.join(","))
    .concat(`${points[points.length - 1][0]},${H - PADDING}`, `${points[0][0]},${H - PADDING}`)
    .join(" ");

  const lastIdx = points.length > 0 ? points.length - 1 : 0;
  const [lastX, lastY] = points[lastIdx] || [W - PRICE_TAG_W, H / 2];
  const lastPrice = prices[lastIdx] !== undefined ? prices[lastIdx] : "";

  // 計算漲跌百分比
  const firstPrice = prices[0];
  const changePercent = firstPrice ? ((lastPrice - firstPrice) / firstPrice * 100).toFixed(2) : "0.00";
  const isPositive = parseFloat(changePercent) >= 0;

  return (
    <div style={{ marginTop: 24, position: "relative", background: "rgba(255,255,255,0.05)", borderRadius: 16, padding: 16 }}>
      {/* 標題和漲跌幅 */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center", 
        marginBottom: 16,
        padding: "0 8px"
      }}>
        <h3 style={{ margin: 0, color: "#fff", fontSize: "1.3em", fontWeight: "bold" }}>
          {coinId} 價格趨勢
        </h3>
        <div style={{ 
          color: isPositive ? "#4caf50" : "#f44336", 
          fontSize: "1.2em", 
          fontWeight: "bold" 
        }}>
          {isPositive ? "+" : ""}{changePercent}%
        </div>
      </div>

      <svg
        width={W}
        height={H}
        style={{
          background: "linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)",
          borderRadius: 12,
          width: "100%",
          height: H,
          boxShadow: "0 4px 20px rgba(3,29,57,0.4), inset 0 1px 0 rgba(255,255,255,0.1)"
        }}
      >
        <defs>
          <linearGradient id="line-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.9" />
            <stop offset="50%" stopColor="#3f51b5" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#e040fb" stopOpacity="0.3" />
          </linearGradient>
          <linearGradient id="area-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#e040fb" stopOpacity="0.05" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* 網格線 */}
        <defs>
          <pattern id="grid" width="40" height="20" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* Y軸標籤 - 更大更清楚 */}
        <text x={16} y={30} fontSize="1.1em" fill="#00e5ff" textAnchor="start" fontWeight="bold">
          MAX: ${max.toFixed(2)}
        </text>
        <text x={16} y={H - 16} fontSize="1.1em" fill="#ff6b6b" textAnchor="start" fontWeight="bold">
          MIN: ${min.toFixed(2)}
        </text>

        {/* 面積填充 */}
        <polygon points={areaPointsStr} fill="url(#area-gradient)" />
        
        {/* 主要趨勢線 - 更粗更明顯 */}
        <polyline 
          points={pointsStr} 
          fill="none" 
          stroke="url(#line-gradient)" 
          strokeWidth="3.5" 
          filter="url(#glow)"
        />

        {/* 標記最高點和最低點 */}
        {points[maxIndex] && (
          <g>
            <circle 
              cx={points[maxIndex][0]} 
              cy={points[maxIndex][1]} 
              r={6} 
              fill="#00e5ff" 
              stroke="#fff" 
              strokeWidth={2}
              filter="url(#glow)"
            />
            <circle 
              cx={points[maxIndex][0]} 
              cy={points[maxIndex][1]} 
              r={12} 
              fill="none" 
              stroke="#00e5ff" 
              strokeWidth={1.5}
              opacity={0.6}
            />
            {/* MAX 標籤 */}
            <rect
              x={points[maxIndex][0] - 25}
              y={points[maxIndex][1] - 25}
              width="50"
              height="18"
              rx="9"
              fill="rgba(0,229,255,0.2)"
              stroke="#00e5ff"
              strokeWidth={1}
            />
            <text
              x={points[maxIndex][0]}
              y={points[maxIndex][1] - 12}
              textAnchor="middle"
              fontSize="0.9em"
              fill="#00e5ff"
              fontWeight="bold"
            >MAX</text>
          </g>
        )}

        {points[minIndex] && (
          <g>
            <circle 
              cx={points[minIndex][0]} 
              cy={points[minIndex][1]} 
              r={6} 
              fill="#ff6b6b" 
              stroke="#fff" 
              strokeWidth={2}
              filter="url(#glow)"
            />
            <circle 
              cx={points[minIndex][0]} 
              cy={points[minIndex][1]} 
              r={12} 
              fill="none" 
              stroke="#ff6b6b" 
              strokeWidth={1.5}
              opacity={0.6}
            />
            {/* MIN 標籤 */}
            <rect
              x={points[minIndex][0] - 25}
              y={points[minIndex][1] + 8}
              width="50"
              height="18"
              rx="9"
              fill="rgba(255,107,107,0.2)"
              stroke="#ff6b6b"
              strokeWidth={1}
            />
            <text
              x={points[minIndex][0]}
              y={points[minIndex][1] + 20}
              textAnchor="middle"
              fontSize="0.9em"
              fill="#ff6b6b"
              fontWeight="bold"
            >MIN</text>
          </g>
        )}

        {/* 所有數據點 */}
        {points.map(([x, y], i) => (
          <circle 
            key={i}
            cx={x} 
            cy={y} 
            r={2.5} 
            fill="#fff" 
            stroke="#00e5ff" 
            strokeWidth={1.5}
            opacity={0.8}
          />
        ))}

        {/* 幣種名稱 */}
        <text
          x={W - PRICE_TAG_W + 8}
          y={25}
          fontSize="1.2em"
          fill="#fff"
          fontWeight="bold"
          textShadow="0 0 8px rgba(0,229,255,0.5)"
        >{coinId}</text>

        {/* 當前價格標籤 - 更大更明顯 */}
        <g>
          <rect
            x={W - PRICE_TAG_W + 8}
            y={lastY - 15}
            width={PRICE_TAG_W - 16}
            height="30"
            rx="15"
            fill="rgba(0,0,0,0.7)"
            stroke="#00e5ff"
            strokeWidth={2}
            filter="url(#glow)"
          />
          <text
            x={W - PRICE_TAG_W + 8 + (PRICE_TAG_W - 16) / 2}
            y={lastY - 2}
            textAnchor="middle"
            fontSize="0.9em"
            fill="#fff"
            opacity={0.8}
          >當前</text>
          <text
            x={W - PRICE_TAG_W + 8 + (PRICE_TAG_W - 16) / 2}
            y={lastY + 12}
            textAnchor="middle"
            fontSize="1.1em"
            fill="#00e5ff"
            fontWeight="bold"
          >${lastPrice}</text>
        </g>
      </svg>

      {/* 統計資訊 */}
      <div style={{ 
        display: "flex", 
        justifyContent: "space-around", 
        marginTop: 16, 
        padding: "12px 0",
        borderTop: "1px solid rgba(255,255,255,0.1)" 
      }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#aaa", fontSize: "0.9em" }}>最高價</div>
          <div style={{ color: "#00e5ff", fontSize: "1.1em", fontWeight: "bold" }}>${max.toFixed(2)}</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#aaa", fontSize: "0.9em" }}>最低價</div>
          <div style={{ color: "#ff6b6b", fontSize: "1.1em", fontWeight: "bold" }}>${min.toFixed(2)}</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#aaa", fontSize: "0.9em" }}>當前價</div>
          <div style={{ color: "#fff", fontSize: "1.1em", fontWeight: "bold" }}>${lastPrice}</div>
        </div>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#aaa", fontSize: "0.9em" }}>漲跌幅</div>
          <div style={{ 
            color: isPositive ? "#4caf50" : "#f44336", 
            fontSize: "1.1em", 
            fontWeight: "bold" 
          }}>
            {isPositive ? "+" : ""}{changePercent}%
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FollowList() {
  const [followList, setFollowList] = useState([]);
  const [showChartId, setShowChartId] = useState(null);
  const [addCoin, setAddCoin] = useState("");
  const navigate = useNavigate();
  const [selectedRange, setSelectedRange] = useState("1d");
  const [allCoins, setAllCoins] = useState([]);
  const user_id = localStorage.getItem("user_id");

  useEffect(() => {
    fetch(`api/coin_list?user_id=${user_id}`, { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        const mapped = data.map(c => ({ id: c.coin_id, name: c.coin_name }));
        setAllCoins(mapped);
      });
  }, []);

  useEffect(() => {
    fetch(`follow_list?user_id=${user_id}`, { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        const trackedCoins = data.tracked || [];
        return Promise.all(trackedCoins.map(coin =>
          fetch(`api/price_history/${coin.coin_id}?type=${selectedRange}&user_id=${user_id}`, { credentials: "include" })
            .then(res => res.json())
            .then(history => ({
              id: coin.coin_id,
              price: coin.price,
              history: Array.isArray(history) ? history.reverse() : []
            }))
            .catch(() => ({ id: coin.coin_id, price: coin.price, history: [] }))
        ));
      })
      .then(coinData => {
        setFollowList(coinData);
        setShowChartId(null);
      })
      .catch(err => console.error("fetch follow list 發生錯誤：", err));
  }, [selectedRange]);

  async function handleAddCoin() {
    if (!addCoin || followList.some(c => c.id === addCoin)) return;
    const res = await fetch(`follow_list?user_id=${user_id}`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ action: "add", coin_id: addCoin }),
      credentials: "include"
    });
    if (res.ok) window.location.reload();
  }

  async function handleRemoveCoin(coinId) {
    const res = await fetch(`follow_list?user_id=${user_id}`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ action: "remove", coin_id: coinId }),
      credentials: "include"
    });
    if (res.ok) window.location.reload();
  }

  return (
    <div className="crypto-glass follow-list">
      <button className="glass-btn" style={{ marginBottom: 10, width: "fit-content", padding: "9px 30px" }} onClick={() => navigate("/")}>回到主頁面</button>
      <h1 className="title2">追蹤清單</h1>
      <div style={{ display: "flex", gap: 12, margin: "8px 0 18px 0" }}>
        {["1d", "3d", "7d"].map(r => (
          <button key={r} className="glass-btn" style={{
            padding: "6px 16px",
            background: selectedRange === r ? "#5ee7ff" : "transparent",
            color: selectedRange === r ? "#000" : "#ccc",
            border: "1px solid #5ee7ff",
            borderRadius: 6,
            cursor: "pointer",
            fontWeight: "bold"
          }} onClick={() => setSelectedRange(r)}>
            {r === "1d" ? "1天" : r === "3d" ? "3天" : "7天"}
          </button>
        ))}
      </div>

      <div className="coin-list">
        {followList.map(coin => (
          <div className="coin-row" key={coin.id} style={{ flexDirection: "column", alignItems: "flex-start" }}>
            <div style={{ display: "flex", alignItems: "center", width: "100%", gap: 12 }}>
              <span className="coin-id">{coin.id}</span>
              <span className="coin-price">${coin.price}</span>
              <button className="trend-btn" onClick={() => setShowChartId(showChartId === coin.id ? null : coin.id)}>
                {showChartId === coin.id ? "收起趨勢圖" : "查看趨勢圖"}
              </button>
              <button className="remove-btn" style={{
                marginLeft: 8,
                background: "rgba(255,80,80,0.13)",
                color: "#ff4444",
                border: "none",
                borderRadius: 6,
                padding: "5px 12px",
                cursor: "pointer",
                fontWeight: "bold",
                fontSize: "1em"
              }} onClick={() => handleRemoveCoin(coin.id)} title="取消追蹤">
                取消
              </button>
            </div>
            {showChartId === coin.id && (
              <div className="coin-chart" style={{ width: "100%" }}>
                <TrendChart history={coin.history} coinId={coin.id} />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="add-coin-row">
        <select className="coin-select" value={addCoin} onChange={e => setAddCoin(e.target.value)}>
          <option value="">選擇幣種新增追蹤</option>
          {allCoins.filter(c => !followList.some(f => f.id === c.id)).map(c => (
            <option value={c.id} key={c.id}>{c.name} ({c.id})</option>
          ))}
        </select>
        <button type="button" className="add-btn" onClick={handleAddCoin}>加入追蹤</button>
      </div>
    </div>
  );
}