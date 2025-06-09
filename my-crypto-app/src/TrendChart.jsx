// src/TrendChart.jsx
import React from "react";

export default function TrendChart({ history, coinId }) {
  if (!history || history.length === 0) return (
    <div style={{ padding: 18, color: "#bbb" }}>暫無資料</div>
  );

  const prices = history.map(d => d.price);
  const max = Math.max(...prices);
  const min = Math.min(...prices);
  const W = 200, H = 60;
  const Y_LABEL_W = 42;
  const PRICE_TAG_W = 54;

  const points = history.map((d, i) => [
    Y_LABEL_W + (i / (history.length - 1)) * (W - Y_LABEL_W - PRICE_TAG_W),
    H - 16 - ((d.price - min) / (max - min + 1e-6)) * (H - 24)
  ]);
  const pointsStr = points.map(p => p.join(",")).join(" ");
  const areaPointsStr = points
    .map(p => p.join(","))
    .concat(`${points[points.length - 1][0]},${H - 12}`, `${points[0][0]},${H - 12}`)
    .join(" ");

  const lastIdx = points.length > 0 ? points.length - 1 : 0;
  const [lastX, lastY] = points[lastIdx] || [W - PRICE_TAG_W, H / 2];
  const lastPrice = prices[lastIdx] !== undefined ? prices[lastIdx] : "";

  return (
    <div style={{ marginTop: 18, position: "relative" }}>
      <svg
        width={W}
        height={H}
        style={{
          background: "rgba(255,255,255,0.08)",
          borderRadius: 10,
          width: "100%",
          height: H,
          boxShadow: "0 2px 18px #031d39cc"
        }}
      >
        <defs>
          <linearGradient id="line-gradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#90caf9" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#e040fb" stopOpacity="0.13" />
          </linearGradient>
          <linearGradient id="dot-glow" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#e040fb" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#90caf9" stopOpacity="0.1" />
          </linearGradient>
        </defs>

        <text x={10} y={18} fontSize="0.88em" fill="#aee1fc" textAnchor="start">${max}</text>
        <text x={10} y={H-12} fontSize="0.88em" fill="#aee1fc" textAnchor="start">${min}</text>

        <polygon points={areaPointsStr} fill="url(#line-gradient)" opacity="0.41" />
        <polyline points={pointsStr} fill="none" stroke="url(#line-gradient)" strokeWidth="2.7" />

        {/*points.map(([x, y], i) => (
            <g key={i}>
                <circle cx={x} cy={y} r={6} fill="url(#dot-glow)" opacity="0.18" />
                <circle cx={x} cy={y} r={2.7} fill="#fff" stroke="#e040fb" strokeWidth={1.2} />
            </g>
         ))*/}


        <text
          x={W - PRICE_TAG_W + 4}
          y={18}
          fontSize="0.98em"
          fill="#fff"
          opacity="0.8"
          fontWeight="bold"
        >{coinId}</text>

        <g>
          <rect
            x={W - PRICE_TAG_W + 4}
            y={lastY - 10}
            width={PRICE_TAG_W - 12}
            height="20"
            rx="9"
            fill="#222c"
            stroke="#90caf9"
            strokeWidth={1.2}
            opacity="0.95"
          />
          <text
            x={W - PRICE_TAG_W + 4 + (PRICE_TAG_W - 12) / 2}
            y={lastY + 4}
            textAnchor="middle"
            fontSize="0.98em"
            fill="#5ee7ff"
            fontWeight="bold"
          >${lastPrice}</text>
        </g>
      </svg>
    </div>
  );
}
