import { useEffect } from "react";

export default function SetUidGuard() {
  useEffect(() => {
    const hash = window.location.hash || "";
    const queryIndex = hash.indexOf("?");
    if (queryIndex !== -1) {
      const query = hash.slice(queryIndex + 1);
      const params = new URLSearchParams(query);
      const uid = params.get("user_id");
      if (uid) {
        localStorage.setItem("user_id", uid);
        console.log("✅ 自動補上 user_id：", uid);
      }
    }
  }, []);

  return null;
}
