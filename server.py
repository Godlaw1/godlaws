"""
Godlaws Foundation — Donation Server
FastAPI backend with PayPal REST API integration for accepting donations.
"""
from __future__ import annotations

import os
import sqlite3
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import uvicorn

load_dotenv()

log = logging.getLogger("godlaws")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ── Config ────────────────────────────────────────────────────────────────────
PAYPAL_CLIENT_ID = os.environ["PAYPAL_CLIENT_ID"]
PAYPAL_CLIENT_SECRET = os.environ["PAYPAL_CLIENT_SECRET"]
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8800")
PORT = int(os.getenv("PORT", "8800"))

PAYPAL_API = (
    "https://api-m.sandbox.paypal.com"
    if PAYPAL_MODE == "sandbox"
    else "https://api-m.paypal.com"
)

DB_PATH = os.path.join(os.path.dirname(__file__), "donations.db")


# ── Database ──────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paypal_order_id TEXT UNIQUE NOT NULL,
            donor_name TEXT,
            donor_email TEXT,
            amount TEXT NOT NULL,
            currency TEXT DEFAULT 'USD',
            status TEXT DEFAULT 'created',
            message TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            resource_id TEXT,
            payload TEXT,
            received_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── PayPal API ────────────────────────────────────────────────────────────────
_token_cache: dict = {"token": None, "expires": 0}


async def get_paypal_token() -> str:
    now = datetime.now(timezone.utc).timestamp()
    if _token_cache["token"] and _token_cache["expires"] > now:
        return _token_cache["token"]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_API}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        _token_cache["token"] = data["access_token"]
        _token_cache["expires"] = now + data.get("expires_in", 3600) - 60
        return data["access_token"]


async def paypal_headers() -> dict:
    token = await get_paypal_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


async def create_paypal_order(amount: str, currency: str = "USD", message: str = "") -> dict:
    headers = await paypal_headers()
    order_data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": currency, "value": amount},
                "description": f"Donation to Godlaws Foundation{': ' + message if message else ''}",
            }
        ],
        "application_context": {
            "brand_name": "Godlaws Foundation",
            "landing_page": "BILLING",
            "user_action": "PAY_NOW",
            "return_url": f"{BASE_URL}/donate/success",
            "cancel_url": f"{BASE_URL}/donate/cancel",
        },
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_API}/v2/checkout/orders",
            json=order_data,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def capture_paypal_order(order_id: str) -> dict:
    headers = await paypal_headers()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_API}/v2/checkout/orders/{order_id}/capture",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def get_paypal_order(order_id: str) -> dict:
    headers = await paypal_headers()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{PAYPAL_API}/v2/checkout/orders/{order_id}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


# ── App ───────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log.info("Godlaws donation server started on port %d (%s mode)", PORT, PAYPAL_MODE)
    yield


app = FastAPI(title="Godlaws Foundation", lifespan=lifespan)


# ── Dashboard HTML ────────────────────────────────────────────────────────────
DONATE_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Godlaws Foundation — Donate</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0a0a0a; color: #e0e0e0; min-height: 100vh;
         display: flex; flex-direction: column; align-items: center; }
  .hero { text-align: center; padding: 60px 20px 40px; max-width: 700px; }
  .hero h1 { font-size: 2.5rem; color: #fff; margin-bottom: 10px; }
  .hero .subtitle { font-size: 1.1rem; color: #888; margin-bottom: 30px; }
  .donate-card { background: #151515; border: 1px solid #2a2a2a; border-radius: 16px;
                 padding: 40px; max-width: 480px; width: 90%; }
  .donate-card h2 { margin-bottom: 24px; color: #fff; font-size: 1.4rem; }
  .amounts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
  .amount-btn { background: #1a1a2e; border: 2px solid #333; border-radius: 10px;
                padding: 14px; font-size: 1.1rem; color: #fff; cursor: pointer;
                transition: all 0.2s; }
  .amount-btn:hover, .amount-btn.active { border-color: #0070ba; background: #0070ba22; }
  .custom-amount { width: 100%; padding: 14px; background: #1a1a2e; border: 2px solid #333;
                   border-radius: 10px; color: #fff; font-size: 1rem; margin-bottom: 16px; }
  .custom-amount:focus { outline: none; border-color: #0070ba; }
  .message-input { width: 100%; padding: 12px; background: #1a1a2e; border: 2px solid #333;
                   border-radius: 10px; color: #fff; font-size: 0.95rem; margin-bottom: 20px;
                   resize: none; }
  .message-input:focus { outline: none; border-color: #0070ba; }
  .donate-btn { width: 100%; padding: 16px; background: #0070ba; color: #fff; border: none;
                border-radius: 10px; font-size: 1.1rem; font-weight: 600; cursor: pointer;
                transition: background 0.2s; }
  .donate-btn:hover { background: #005ea6; }
  .donate-btn:disabled { background: #333; cursor: not-allowed; }
  .stats { display: flex; gap: 30px; margin-top: 40px; margin-bottom: 40px; }
  .stat { text-align: center; }
  .stat .num { font-size: 1.8rem; font-weight: 700; color: #0070ba; }
  .stat .label { font-size: 0.85rem; color: #666; margin-top: 4px; }
  .recent { max-width: 480px; width: 90%; margin-bottom: 40px; }
  .recent h3 { margin-bottom: 12px; color: #888; font-size: 0.9rem; text-transform: uppercase; }
  .recent-item { background: #151515; border: 1px solid #2a2a2a; border-radius: 8px;
                 padding: 12px 16px; margin-bottom: 8px; display: flex;
                 justify-content: space-between; align-items: center; }
  .recent-item .name { color: #ccc; }
  .recent-item .amt { color: #0070ba; font-weight: 600; }
  .footer { padding: 20px; color: #444; font-size: 0.8rem; }
  .currency-select { padding: 14px; background: #1a1a2e; border: 2px solid #333;
                     border-radius: 10px; color: #fff; font-size: 1rem; margin-bottom: 16px; }
  .row { display: flex; gap: 10px; }
  .row .custom-amount { flex: 1; margin-bottom: 0; }
</style>
</head>
<body>
<div class="hero">
  <h1>Godlaws Foundation</h1>
  <p class="subtitle">Open source trading tools for everyone. Your donation helps us build free, transparent financial technology.</p>
</div>

<div class="donate-card">
  <h2>Make a Donation</h2>
  <div class="amounts">
    <button class="amount-btn" onclick="setAmount('5')">$5</button>
    <button class="amount-btn" onclick="setAmount('10')">$10</button>
    <button class="amount-btn" onclick="setAmount('25')">$25</button>
    <button class="amount-btn" onclick="setAmount('50')">$50</button>
    <button class="amount-btn" onclick="setAmount('100')">$100</button>
    <button class="amount-btn" onclick="setAmount('250')">$250</button>
  </div>
  <div class="row">
    <input type="number" class="custom-amount" id="amount" placeholder="Custom amount" min="1" step="0.01">
    <select class="currency-select" id="currency">
      <option value="USD">USD</option>
      <option value="EUR">EUR</option>
      <option value="GBP">GBP</option>
    </select>
  </div>
  <br>
  <textarea class="message-input" id="message" rows="2" placeholder="Leave a message (optional)"></textarea>
  <button class="donate-btn" id="donateBtn" onclick="donate()">Donate with PayPal</button>
</div>

<div class="stats" id="stats"></div>
<div class="recent" id="recent"></div>

<div class="footer">
  &copy; 2026 Godlaws Foundation &mdash; Apache 2.0 License &mdash; Founded by Clayd Anthoni
</div>

<script>
function setAmount(val) {
  document.getElementById('amount').value = val;
  document.querySelectorAll('.amount-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}

async function donate() {
  const amount = document.getElementById('amount').value;
  const currency = document.getElementById('currency').value;
  const message = document.getElementById('message').value;
  if (!amount || parseFloat(amount) < 1) { alert('Please enter an amount'); return; }

  const btn = document.getElementById('donateBtn');
  btn.disabled = true;
  btn.textContent = 'Redirecting to PayPal...';

  try {
    const resp = await fetch('/api/donate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({amount, currency, message})
    });
    const data = await resp.json();
    if (data.approval_url) {
      window.location.href = data.approval_url;
    } else {
      alert('Error creating donation. Please try again.');
      btn.disabled = false;
      btn.textContent = 'Donate with PayPal';
    }
  } catch(e) {
    alert('Connection error. Please try again.');
    btn.disabled = false;
    btn.textContent = 'Donate with PayPal';
  }
}

async function loadStats() {
  try {
    const resp = await fetch('/api/donations/stats');
    const data = await resp.json();
    document.getElementById('stats').innerHTML = `
      <div class="stat"><div class="num">$${data.total_amount}</div><div class="label">Total Raised</div></div>
      <div class="stat"><div class="num">${data.total_donations}</div><div class="label">Donations</div></div>
      <div class="stat"><div class="num">${data.total_donors}</div><div class="label">Donors</div></div>
    `;

    if (data.recent && data.recent.length > 0) {
      let html = '<h3>Recent Donations</h3>';
      data.recent.forEach(d => {
        const name = d.donor_name || 'Anonymous';
        html += `<div class="recent-item"><span class="name">${name}${d.message ? ' — ' + d.message : ''}</span><span class="amt">$${d.amount}</span></div>`;
      });
      document.getElementById('recent').innerHTML = html;
    }
  } catch(e) {}
}
loadStats();
</script>
</body>
</html>"""

SUCCESS_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thank You — Godlaws Foundation</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0a0a0a; color: #e0e0e0; min-height: 100vh;
         display: flex; justify-content: center; align-items: center; }
  .card { background: #151515; border: 1px solid #2a2a2a; border-radius: 16px;
          padding: 60px 40px; text-align: center; max-width: 500px; }
  .check { font-size: 4rem; margin-bottom: 20px; }
  h1 { color: #fff; margin-bottom: 10px; }
  p { color: #888; margin-bottom: 24px; line-height: 1.6; }
  a { color: #0070ba; text-decoration: none; font-weight: 600; }
  .amount { font-size: 2rem; color: #0070ba; font-weight: 700; margin: 16px 0; }
</style>
</head>
<body>
<div class="card">
  <div class="check">&#10003;</div>
  <h1>Thank You!</h1>
  <div class="amount" id="donationAmount"></div>
  <p>Your donation to Godlaws Foundation has been received. You're helping make trading tools open and accessible to everyone.</p>
  <a href="/">Back to Home</a> &nbsp;&middot;&nbsp; <a href="https://github.com/Godlaw1">View Our Projects</a>
</div>
<script>
const params = new URLSearchParams(window.location.search);
const amt = params.get('amount');
const cur = params.get('currency') || 'USD';
if (amt) document.getElementById('donationAmount').textContent = `${cur} ${amt}`;
</script>
</body>
</html>"""

CANCEL_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cancelled — Godlaws Foundation</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0a0a0a; color: #e0e0e0; min-height: 100vh;
         display: flex; justify-content: center; align-items: center; }
  .card { background: #151515; border: 1px solid #2a2a2a; border-radius: 16px;
          padding: 60px 40px; text-align: center; max-width: 500px; }
  h1 { color: #fff; margin-bottom: 10px; }
  p { color: #888; margin-bottom: 24px; }
  a { color: #0070ba; text-decoration: none; font-weight: 600; }
</style>
</head>
<body>
<div class="card">
  <h1>Donation Cancelled</h1>
  <p>No worries! You can donate anytime.</p>
  <a href="/">Back to Home</a>
</div>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home():
    return DONATE_PAGE


@app.post("/api/donate")
async def create_donation(request: Request):
    body = await request.json()
    amount = body.get("amount", "").strip()
    currency = body.get("currency", "USD").upper()
    message = body.get("message", "").strip()[:200]

    if not amount or float(amount) < 1:
        raise HTTPException(400, "Amount must be at least 1")

    # Format to 2 decimal places
    amount = f"{float(amount):.2f}"

    order = await create_paypal_order(amount, currency, message)
    order_id = order["id"]

    # Save to database
    conn = get_db()
    conn.execute(
        "INSERT INTO donations (paypal_order_id, amount, currency, status, message) VALUES (?, ?, ?, ?, ?)",
        (order_id, amount, currency, "created", message),
    )
    conn.commit()
    conn.close()

    # Find approval URL
    approval_url = next(
        (link["href"] for link in order.get("links", []) if link["rel"] == "approve"),
        None,
    )

    log.info("Donation order %s created: %s %s", order_id, currency, amount)
    return {"order_id": order_id, "approval_url": approval_url}


@app.get("/donate/success")
async def donation_success(token: str = ""):
    if not token:
        return HTMLResponse(SUCCESS_PAGE)

    try:
        result = await capture_paypal_order(token)
        status = result.get("status", "UNKNOWN")

        donor_name = ""
        donor_email = ""
        amount = ""
        currency = "USD"

        if status == "COMPLETED":
            payer = result.get("payer", {})
            donor_name = f"{payer.get('name', {}).get('given_name', '')} {payer.get('name', {}).get('surname', '')}".strip()
            donor_email = payer.get("email_address", "")

            captures = (
                result.get("purchase_units", [{}])[0]
                .get("payments", {})
                .get("captures", [{}])
            )
            if captures:
                amount = captures[0].get("amount", {}).get("value", "")
                currency = captures[0].get("amount", {}).get("currency_code", "USD")

        conn = get_db()
        conn.execute(
            """UPDATE donations SET status=?, donor_name=?, donor_email=?, completed_at=?
               WHERE paypal_order_id=?""",
            (status.lower(), donor_name, donor_email, datetime.now(timezone.utc).isoformat(), token),
        )
        conn.commit()
        conn.close()

        log.info("Donation %s captured: %s %s from %s", token, currency, amount, donor_name or "Anonymous")

        return RedirectResponse(f"/donate/thank-you?amount={amount}&currency={currency}")

    except httpx.HTTPStatusError as e:
        log.error("PayPal capture failed for %s: %s", token, e.response.text)
        return RedirectResponse("/donate/thank-you")


@app.get("/donate/thank-you", response_class=HTMLResponse)
async def thank_you():
    return SUCCESS_PAGE


@app.get("/donate/cancel", response_class=HTMLResponse)
async def donation_cancel():
    return CANCEL_PAGE


@app.get("/api/donations/stats")
async def donation_stats():
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(CAST(amount AS REAL)), 0) as total FROM donations WHERE status='completed'"
    ).fetchone()
    donors = conn.execute(
        "SELECT COUNT(DISTINCT donor_email) as cnt FROM donations WHERE status='completed' AND donor_email != ''"
    ).fetchone()
    recent = conn.execute(
        "SELECT donor_name, amount, currency, message, completed_at FROM donations WHERE status='completed' ORDER BY completed_at DESC LIMIT 10"
    ).fetchall()
    conn.close()

    return {
        "total_donations": row["cnt"],
        "total_amount": f"{row['total']:.2f}",
        "total_donors": donors["cnt"],
        "recent": [dict(r) for r in recent],
    }


@app.get("/api/donations")
async def list_donations():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, donor_name, amount, currency, status, message, created_at, completed_at FROM donations ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/webhooks/paypal")
async def paypal_webhook(request: Request):
    """Receive PayPal webhook notifications."""
    body = await request.json()
    event_type = body.get("event_type", "")
    resource = body.get("resource", {})
    resource_id = resource.get("id", "")

    conn = get_db()
    conn.execute(
        "INSERT INTO webhooks (event_type, resource_id, payload) VALUES (?, ?, ?)",
        (event_type, resource_id, str(body)),
    )
    conn.commit()

    if event_type == "CHECKOUT.ORDER.APPROVED":
        conn.execute(
            "UPDATE donations SET status='approved' WHERE paypal_order_id=?",
            (resource_id,),
        )
        conn.commit()

    elif event_type == "PAYMENT.CAPTURE.COMPLETED":
        order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id", "")
        amount = resource.get("amount", {}).get("value", "")
        if order_id:
            conn.execute(
                "UPDATE donations SET status='completed', completed_at=? WHERE paypal_order_id=?",
                (datetime.now(timezone.utc).isoformat(), order_id),
            )
            conn.commit()
            log.info("Webhook: payment captured for order %s: $%s", order_id, amount)

    conn.close()
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "godlaws-donations", "mode": PAYPAL_MODE}


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
