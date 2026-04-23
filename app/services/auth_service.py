"""
Auth service - WeChat authentication and JWT token generation
"""
import httpx

from app.core.config import settings
from app.core.exceptions import WeChatAuthException
from app.core.security import create_access_token


class AuthService:
    """WeChat authentication service"""

    WX_LOGIN_URL = "https://api.weixin.qq.com/sns/jscode2session"

    async def get_wechat_openid(self, code: str) -> dict:
        """Call WeChat API to get openid from login code"""
        params = {
            "appid": settings.wx_appid,
            "secret": settings.wx_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        # 调用微信 API
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.get(self.WX_LOGIN_URL, params=params)
            data = response.json()

        if data.get("errcode") and data.get("errcode") != 0:
            raise WeChatAuthException(detail=f"WeChat error: {data.get('errmsg', 'Unknown error')}")

        return {
            "openid": data.get("openid"),
            "session_key": data.get("session_key"),
        }

    def create_token(self, user_id: int, openid: str) -> str:
        """Create JWT token for user"""
        payload = {"sub": str(user_id), "openid": openid}
        return create_access_token(payload)