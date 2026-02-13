import httpx
from typing import Any, Dict, Optional, List
from core.logger import get_emulation_logger

class AmberFetcher:
    """
    Project Amber (gi.yatta.moe) API 获取器。
    
    负责获取角色详情及全局成长曲线表。
    """

    BASE_URL = "https://gi.yatta.moe/api/v2/chs"
    STATIC_URL = "https://gi.yatta.moe/api/v2/static"

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def _get(self, url: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=self.timeout, verify=False) as client:
                response = client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                if data.get("response") == 200:
                    return data.get("data", {})
                return None
        except Exception as e:
            get_emulation_logger().log_error(f"Fetcher 请求失败 [{url}]: {str(e)}", sender="Fetcher")
            return None

    def find_avatar_id(self, name: str) -> Optional[str]:
        """通过名称查找 ID。"""
        get_emulation_logger().log_info(f"正在查找角色 ID: {name}...", sender="Fetcher")
        data = self._get(f"{self.BASE_URL}/avatar")
        if not data: return None
        items = data.get("items", {})
        for avatar_id, details in items.items():
            if details.get("name") == name:
                return str(avatar_id)
        return None

    def fetch_avatar_detail(self, avatar_id: str, vh: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取角色详情。"""
        params = {"vh": vh} if vh else None
        return self._get(f"{self.BASE_URL}/avatar/{avatar_id}", params=params)

    def fetch_growth_curves(self, vh: Optional[str] = "63F3") -> Optional[Dict[str, Any]]:
        """获取全量成长曲线表。"""
        params = {"vh": vh} if vh else None
        return self._get(f"{self.STATIC_URL}/avatarCurve", params=params)
