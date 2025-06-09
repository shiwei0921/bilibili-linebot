import { useEffect } from "react";

export default function SetUidGuard() {
  useEffect(() => {
    const query = window.location.search;
    const params = new URLSearchParams(query);
    const uid = params.get("uid") || params.get("user_id");
    if (uid) {
      localStorage.setItem("user_id", uid);
      console.log("✅ 自動補上 user_id：", uid);
    }
  }, []);

  return null;
}
