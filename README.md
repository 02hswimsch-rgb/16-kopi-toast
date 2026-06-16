# ☕🍳 16 Kopi & Toast

A breakfast pre-order web app for **16 Kopi & Toast** — a Hall 16 (NTU Singapore)
breakfast business. Customers pre-order the night before; the cut-off is midnight
(SGT). Payment is handled outside the app via a PayNow/PayLah! QR code shown on the
confirmation page. New orders are pushed to the owner over Telegram.

## Features

- 🎉 Dismissible **Opening Promo** banner ($4.50 → $4.00 base set).
- 🍞 Full-width hero image with a warm tint; **Roomie Set** shows an `x2` badge.
- 🧍 **Solo Set** ($4.00) and 🛏️ **Roomie Set** ($7.00 — $3.50 per person).
- Per-person egg + drink selection, with live add-on pricing.
- 🏠 Hall 16 room delivery (block/level/room) or 🛒 Prime Supermarket self-collection.
- ⏰ Pickup time picker, 6:30 AM–9:00 AM in 5-minute steps.
- 💰 Live, auto-calculated order total with a full breakdown.
- 🔒 Midnight cut-off logic (orders open 8 PM–11:59 PM SGT; greyed out otherwise).
- 📲 Telegram notifications to the owner (and the customer if they give a `@handle`).

## Files

| File                  | Purpose                                              |
| --------------------- | ---------------------------------------------------- |
| `app.py`              | The complete Streamlit application.                  |
| `requirements.txt`    | Python dependencies (`streamlit`, `requests`, `pytz`).|
| `secrets.toml.example`| Template for the Telegram secrets.                   |
| `kopi_toast.png`      | Hero / menu image (place in this folder).            |
| `paynow_qr.png`       | PayNow/PayLah! QR code shown on confirmation.        |

> Before going live, open `app.py` and set `PAYNOW_NUMBER` to the operator's actual
> PayNow-registered mobile number (it appears in the payment instructions).

## Run locally

```bash
pip install -r requirements.txt
# Create .streamlit/secrets.toml from the example below, then:
streamlit run app.py
```

Create `.streamlit/secrets.toml` (do **not** commit it):

```toml
BOT_TOKEN = "your-telegram-bot-token"
OWNER_CHAT_ID = "your-chat-id"
```

- **BOT_TOKEN** — from [@BotFather](https://t.me/BotFather) (`/newbot`).
- **OWNER_CHAT_ID** — your numeric chat ID. Message your bot once, then visit
  `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates` and copy the `chat.id`.

## Deploy on Streamlit Community Cloud

1. **Create a GitHub repo** and push all files, including `kopi_toast.png` and
   `paynow_qr.png`.
2. Go to [share.streamlit.io](https://share.streamlit.io) and **sign in with GitHub**.
3. **Select your repo** and set the main file to **`app.py`**.
4. Click **Deploy**.
5. Open **App settings → Secrets** and paste your `BOT_TOKEN` and `OWNER_CHAT_ID`
   (same format as `secrets.toml.example`).
6. **Replace `paynow_qr.png`** with your actual PayNow/PayLah! QR code (and update
   `PAYNOW_NUMBER` in `app.py`), then push the change.

Made with ❤️ in Hall 16, NTU
