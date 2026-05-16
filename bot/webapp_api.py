import json
import hashlib
import hmac
import urllib.parse
import logging
from pathlib import Path

from aiohttp import web

from config import settings
from database.crud import (
    get_active_subscription, get_user,
    check_and_increment_usage, log_usage,
    get_saved_chats, save_chat, delete_saved_chat, get_saved_chat,
    PLAN_LIMITS, DAILY_LIMITS, PLAN_STARS, PLAN_EMOJI,
)

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "webapp" / "dist"


# ─────────────────────────────────────────────
#  Auth helpers
# ─────────────────────────────────────────────

def _validate_init_data(init_data: str) -> dict | None:
    if not init_data:
        return None
    try:
        params = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = params.pop("hash", "")
        check_string = "\n".join(sorted(f"{k}={v}" for k, v in params.items()))
        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received_hash):
            return None
        return json.loads(params.get("user", "{}"))
    except Exception:
        return None


def _get_user_id(request: web.Request) -> int | None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("tma "):
        return None
    user = _validate_init_data(auth[4:])
    return user.get("id") if user else None


def _ok(data, status=200):
    return web.Response(
        text=json.dumps(data, ensure_ascii=False, default=str),
        content_type="application/json",
        status=status,
    )


def _err(msg, status=400):
    return _ok({"error": msg}, status)


# ─────────────────────────────────────────────
#  CORS middleware
# ─────────────────────────────────────────────

@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return web.Response(headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        })
    resp = await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


# ─────────────────────────────────────────────
#  API handlers
# ─────────────────────────────────────────────

async def api_me(request: web.Request):
    uid = _get_user_id(request)
    if not uid:
        return _err("auth_failed", 401)

    sub = await get_active_subscription(uid)
    user = await get_user(uid)

    if not sub:
        return _ok({
            "user_id": uid,
            "plan": "free",
            "is_trial": False,
            "bonus_requests": 0,
            "usage": {
                "chatgpt": {"used_monthly": 0, "limit_monthly": 20, "used_daily": 0, "limit_daily": 5},
                "claude":  {"used_monthly": 0, "limit_monthly": 0,  "used_daily": 0, "limit_daily": 0},
            },
        })

    lm = PLAN_LIMITS.get(sub.plan, PLAN_LIMITS["free"])
    ld = DAILY_LIMITS.get(sub.plan, DAILY_LIMITS["free"])

    return _ok({
        "user_id": uid,
        "plan": sub.plan,
        "is_trial": bool(sub.is_trial),
        "expires_at": sub.expires_at,
        "bonus_requests": user.bonus_requests if user else 0,
        "usage": {
            "chatgpt": {
                "used_monthly": sub.chatgpt_used, "limit_monthly": lm["chatgpt"],
                "used_daily": sub.daily_chatgpt_used, "limit_daily": ld["chatgpt"],
            },
            "claude": {
                "used_monthly": sub.claude_used, "limit_monthly": lm["claude"],
                "used_daily": sub.daily_claude_used, "limit_daily": ld["claude"],
            },
        },
    })


async def api_chat(request: web.Request):
    uid = _get_user_id(request)
    if not uid:
        return _err("auth_failed", 401)

    try:
        body = await request.json()
    except Exception:
        return _err("invalid_body")

    model = body.get("model", "chatgpt")
    messages = body.get("messages", [])
    mode = body.get("mode", "default")

    if model not in ("chatgpt", "claude"):
        return _err("invalid_model")
    if not messages:
        return _err("empty_messages")

    allowed, used_m, limit_m, used_d, limit_d = await check_and_increment_usage(uid, model)
    if not allowed:
        if limit_m == 0:
            return _ok({"error": "model_unavailable",
                        "message": f"{'Claude' if model == 'claude' else 'ChatGPT'} недоступен на вашем тарифе."}, 403)
        elif limit_d != -1 and used_d >= limit_d:
            return _ok({"error": "limit_reached", "limit_type": "daily",
                        "message": "Дневной лимит исчерпан. Попробуй завтра или обнови тариф."}, 429)
        else:
            return _ok({"error": "limit_reached", "limit_type": "monthly",
                        "message": "Месячный лимит исчерпан. Обнови тариф для продолжения."}, 429)

    try:
        from modes import AI_MODES
        mode_prompt = AI_MODES.get(mode, AI_MODES["default"])["prompt"]

        if model == "chatgpt":
            from services.openai_service import ask_chatgpt
            response, pt, ct = await ask_chatgpt(messages, mode_prompt)
        else:
            from services.claude_service import ask_claude
            response, pt, ct = await ask_claude(messages, mode_prompt)

        await log_usage(uid, model, pt, ct, True)
        return _ok({
            "response": response,
            "used_monthly": used_m, "limit_monthly": limit_m,
            "used_daily": used_d, "limit_daily": limit_d,
        })
    except Exception as e:
        await log_usage(uid, model, 0, 0, False)
        logger.error("Chat API error: %s", e)
        return _ok({"error": "ai_error", "message": str(e)[:300]}, 500)


async def api_chats_list(request: web.Request):
    uid = _get_user_id(request)
    if not uid:
        return _err("auth_failed", 401)
    chats = await get_saved_chats(uid)
    return _ok([{
        "id": c.id, "name": c.name, "model": c.model,
        "mode": c.mode, "created_at": c.created_at,
    } for c in chats])


async def api_chat_load(request: web.Request):
    uid = _get_user_id(request)
    if not uid:
        return _err("auth_failed", 401)
    chat_id = int(request.match_info["chat_id"])
    chat = await get_saved_chat(chat_id, uid)
    if not chat:
        return _err("not_found", 404)
    return _ok({
        "id": chat.id, "name": chat.name, "model": chat.model,
        "mode": chat.mode, "history": json.loads(chat.history),
    })


async def api_chat_save(request: web.Request):
    uid = _get_user_id(request)
    if not uid:
        return _err("auth_failed", 401)
    body = await request.json()
    chat = await save_chat(
        uid,
        body.get("name", "Чат")[:100],
        body.get("model", "chatgpt"),
        body.get("mode", "default"),
        body.get("history", []),
    )
    return _ok({"id": chat.id, "name": chat.name})


async def api_chat_delete(request: web.Request):
    uid = _get_user_id(request)
    if not uid:
        return _err("auth_failed", 401)
    chat_id = int(request.match_info["chat_id"])
    ok = await delete_saved_chat(chat_id, uid)
    return _ok({"ok": ok})


async def api_plans(request: web.Request):
    return _ok({
        "free":  {"name": "Free",  "stars": 0,                   "chatgpt_m": 20,  "chatgpt_d": 5,   "claude_m": 0,   "claude_d": 0,  "chats": 0},
        "basic": {"name": "Basic", "stars": PLAN_STARS["basic"],  "chatgpt_m": 100, "chatgpt_d": 20,  "claude_m": 0,   "claude_d": 0,  "chats": 5},
        "pro":   {"name": "Pro",   "stars": PLAN_STARS["pro"],    "chatgpt_m": 250, "chatgpt_d": 40,  "claude_m": 60,  "claude_d": 10, "chats": 30},
        "ultra": {"name": "Ultra", "stars": PLAN_STARS["ultra"],  "chatgpt_m": 700, "chatgpt_d": 100, "claude_m": 180, "claude_d": 25, "chats": -1},
    })


async def api_invoice(request: web.Request):
    uid = _get_user_id(request)
    if not uid:
        return _err("auth_failed", 401)
    body = await request.json()
    plan = body.get("plan")
    if plan not in PLAN_STARS:
        return _err("invalid_plan")

    bot = request.app["bot"]
    from aiogram.types import LabeledPrice
    from handlers.subscription import PLAN_NAMES
    stars = PLAN_STARS[plan]
    name = PLAN_NAMES.get(plan, plan)

    try:
        link = await bot.create_invoice_link(
            title=f"NEUR AI — {name}",
            description=f"Подписка {name} на 30 дней. Безлимитный доступ к ChatGPT и Claude.",
            payload=f"sub_{plan}_30",
            currency="XTR",
            prices=[LabeledPrice(label=f"NEUR AI {name}", amount=stars)],
        )
        return _ok({"invoice_url": link})
    except Exception as e:
        logger.error("Invoice error: %s", e)
        return _err(str(e)[:200], 500)


# ─────────────────────────────────────────────
#  Static / SPA
# ─────────────────────────────────────────────

async def serve_index(request: web.Request):
    index = STATIC_DIR / "index.html"
    if index.exists():
        return web.FileResponse(index)
    return web.Response(
        text="<h2>Mini App not built yet.</h2><p>Run: <code>cd webapp && npm install && npm run build</code></p>",
        content_type="text/html",
        status=503,
    )


def setup_webapp_routes(app: web.Application, bot):
    app["bot"] = bot
    app.middlewares.append(cors_middleware)  # type: ignore

    # API
    app.router.add_get("/api/me", api_me)
    app.router.add_post("/api/chat", api_chat)
    app.router.add_get("/api/chats", api_chats_list)
    app.router.add_get("/api/chats/{chat_id}", api_chat_load)
    app.router.add_post("/api/chats", api_chat_save)
    app.router.add_delete("/api/chats/{chat_id}", api_chat_delete)
    app.router.add_get("/api/plans", api_plans)
    app.router.add_post("/api/invoice", api_invoice)

    # Static assets built by Vite
    if (STATIC_DIR / "assets").exists():
        app.router.add_static("/app/assets", STATIC_DIR / "assets", name="webapp_assets")

    # SPA routes (React Router handles client-side navigation)
    app.router.add_get("/app/", serve_index)
    app.router.add_get("/app/{path:.*}", serve_index)
    app.router.add_get("/", serve_index)
