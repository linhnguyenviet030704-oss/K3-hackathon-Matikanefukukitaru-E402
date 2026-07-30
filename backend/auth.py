import os

import httpx
from fastapi import Header, HTTPException

from .config import supabase_anon_key, supabase_ready, supabase_url
from .schemas import CurrentUser


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not supabase_ready():
        dev_id = os.getenv("DEV_USER_ID", "local-user")
        token = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
            if token:
                dev_id = token[:128]
        return CurrentUser(id=dev_id, token=token, auth_mode="dev")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Supabase access token required")

    token = authorization.split(" ", 1)[1].strip()
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{supabase_url()}/auth/v1/user",
            headers={"apikey": supabase_anon_key() or "", "Authorization": f"Bearer {token}"},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Supabase access token")

    user = response.json()
    return CurrentUser(id=user["id"], token=token, auth_mode="supabase")
