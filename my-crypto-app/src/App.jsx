import { HashRouter as Router, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import FollowList from "./Followlist";
import "./App.css";
import PriceSearch from "./Pricesearch";
import PnLBalance from "./Pnlbalance";
import Trade from "./Trade";
import Reset from "./Reset";
import SetUidGuard from "./SetUidGuard"; 

// ✅ 修正：解析 hash 中的 query string
function getUserIdFromHash() {
  const hash = window.location.hash || "";
  const queryIndex = hash.indexOf("?");
  if (queryIndex === -1) return null;

  const query = hash.slice(queryIndex + 1); // 去掉 "?user_id=..."
  const params = new URLSearchParams(query);
  const uid = params.get("user_id");

  return uid && uid !== "null" ? uid : null;
}

// 首頁元件
function Home() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const hash = window.location.hash || "";
    const queryIndex = hash.indexOf("?");
    if (queryIndex !== -1) {
      const query = hash.slice(queryIndex + 1);
      const params = new URLSearchParams(query);
      const target = params.get("target");
      const uid = params.get("user_id");

      console.log("✅ 抓到 user_id：", uid);

      if (uid) {
        localStorage.setItem("user_id", uid);
        fetch("/set_uid", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ uid }),
          credentials: "include"
        });
      }

      // ✅ 自動跳轉
      if (target) {
        const finalUid = uid || localStorage.getItem("user_id") || "test_user_001";
        window.location.hash = `/${target}?user_id=${finalUid}`;
      }
    }
  }, []);

  // ✅ 點按鈕跳轉功能頁，保留 user_id
  const goTo = (path) => {
    const user_id = localStorage.getItem("user_id") || "test_user_001";
    window.location.hash = `${path}?user_id=${user_id}`;
  };

  return (
    <div>
      <h1 className="title">幣哩幣哩</h1>
      <div className="crypto-glass home">
        <div className="main-buttons">
          <button className="glass-btn" onClick={() => goTo("/followlist")}>追蹤清單</button>
          <button className="glass-btn" onClick={() => goTo("/pricesearch")}>幣價查詢</button>
          <button className="glass-btn" onClick={() => goTo("/pnlbalance")}>損益&餘額查詢</button>
          <button className="glass-btn" onClick={() => goTo("/trade")}>Trade</button>
          <button className="glass-btn danger" onClick={() => goTo("/reset")}>重置</button>
        </div>
      </div>
    </div>
  );
}

// App 主程式
export default function App() {
  return (
    <Router>
      <SetUidGuard /> {/* ✅ 自動補 user_id */}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/followlist" element={<FollowList />} />
        <Route path="/pricesearch" element={<PriceSearch />} />
        <Route path="/pnlbalance" element={<PnLBalance />} />
        <Route path="/trade" element={<Trade />} />
        <Route path="/reset" element={<Reset />} />
      </Routes>
    </Router>
  );
}
