"""16 Kopi & Toast — breakfast pre-order web app.

A single-file Streamlit application for a Hall 16 (NTU) breakfast pre-order
business. Orders are placed the night before, with a midnight cut-off.

Telegram notifications use the Bot HTTP API via the ``requests`` library only.
Secrets (BOT_TOKEN, OWNER_CHAT_ID) are read from ``st.secrets`` — never hardcode.
"""

import base64
from datetime import datetime, timedelta

import pytz
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SHOP_NAME = "16 Kopi & Toast"

# PayNow / PayLah! mobile number shown on the confirmation page.
# >>> Replace this with the operator's actual PayNow-registered number. <<<
PAYNOW_NUMBER = "8822 6946"

# Pricing — Opening Promo
SOLO_BASE = 4.00
SOLO_ORIGINAL = 4.50
ROOMIE_BASE = 7.50
ROOMIE_ORIGINAL = 8.00

# Drink options and their add-on charges (coffee / tea are included).
DRINKS = {
    "Coffee": 0.00,
    "Tea": 0.00,
    "Milo": 0.50,
    "Americano": 1.00,
    "Latte": 1.00,
    "Cappuccino": 1.00,
}

EGG_TYPES = ["Soft-boiled", "Hard-boiled"]
BLOCKS = ["A", "B", "C", "D", "E"]

SGT = pytz.timezone("Asia/Singapore")

HERO_IMAGE = "kopi_toast.png"
QR_IMAGE = "paynow_qr.png"

st.set_page_config(page_title=SHOP_NAME, page_icon="☕", layout="centered")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_secret(key):
    """Return a secret value, or None if secrets are not configured."""
    try:
        return st.secrets[key]
    except Exception:
        return None


def img_to_base64(path):
    """Read an image file and return base64 text, or None if it fails to load."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def drink_label(name):
    """Selectbox label for a drink, showing its add-on charge."""
    add = DRINKS[name]
    return f"{name} (+${add:.2f})" if add > 0 else f"{name} (included)"


def drink_inline(name):
    """Compact drink label used inside Telegram messages."""
    add = DRINKS[name]
    return f"{name} (+${add:.2f})" if add > 0 else name


def now_sgt():
    return datetime.now(SGT)


def orders_are_open():
    """Open for pre-orders 8:00 PM–11:59 PM SGT; closed 12:00 AM–7:59 PM."""
    return now_sgt().hour >= 20


def pickup_time_options():
    """5-minute increments from 6:30 AM to 9:00 AM (inclusive)."""
    opts = []
    t = datetime(2000, 1, 1, 6, 30)
    end = datetime(2000, 1, 1, 9, 0)
    while t <= end:
        opts.append(t.strftime("%I:%M %p").lstrip("0"))
        t += timedelta(minutes=5)
    return opts


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&display=swap');

        .stApp { background-color: #FDF6EC; }

        .block-container {
            max-width: 480px;
            padding-top: 1.2rem;
            padding-bottom: 2.5rem;
        }

        [data-testid="stHeader"] { background: transparent; }
        #MainMenu, footer { visibility: hidden; }

        /* Section cards (st.container(border=True)) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFF8F0;
            border: 1px solid #ECD9C0;
            border-radius: 16px;
            box-shadow: 0 1px 4px rgba(139, 69, 19, 0.06);
            margin-bottom: 6px;
        }

        /* Header */
        .kt-title {
            text-align: center;
            font-family: 'Playfair Display', Georgia, 'Times New Roman', serif;
            color: #8B4513;
            font-size: 2.3rem;
            font-weight: 900;
            margin: 0.2rem 0 0;
            line-height: 1.15;
        }
        .kt-tagline {
            text-align: center;
            font-style: italic;
            color: #8B4513;
            opacity: 0.85;
            font-size: 1rem;
            margin: 0.1rem 0 0.7rem;
        }

        /* Promo banner */
        .kt-promo {
            position: relative;
            background: linear-gradient(135deg, #F5A623, #E8890B);
            border: 2px solid #C9760A;
            border-radius: 16px;
            padding: 18px 18px 16px;
            text-align: center;
            color: #3B2407;
            box-shadow: 0 3px 10px rgba(139, 69, 19, 0.18);
            margin-bottom: 6px;
            overflow: hidden;
        }
        .kt-ribbon {
            position: absolute;
            top: 12px;
            right: -34px;
            transform: rotate(40deg);
            background: #B91C1C;
            color: #fff;
            padding: 3px 40px;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 1.5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.25);
        }
        .kt-promo-title { font-size: 1.18rem; font-weight: 800; margin-bottom: 6px; }
        .kt-promo-prices { margin: 6px 0; }
        .kt-old {
            text-decoration: line-through;
            color: #7a4a12;
            font-size: 1.1rem;
            margin-right: 10px;
            opacity: 0.85;
        }
        .kt-new { color: #B91C1C; font-size: 2rem; font-weight: 900; }
        .kt-promo-sub { font-size: 0.85rem; margin-top: 6px; color: #4a2f0c; }

        /* Hero image */
        .kt-hero {
            width: 100%;
            border-radius: 16px;
            filter: brightness(0.9);
            display: block;
            margin-bottom: 6px;
            max-height: 240px;
            object-fit: cover;
        }
        .kt-hero-placeholder {
            width: 100%;
            min-height: 170px;
            border-radius: 16px;
            background: #6F4E37;
            color: #FFF3CD;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.6rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 6px;
            padding: 20px;
        }

        /* Roomie set image with x2 badge */
        .kt-roomie-wrap { position: relative; width: 100%; margin-bottom: 8px; }
        .kt-roomie-img {
            width: 100%;
            border-radius: 14px;
            filter: brightness(0.9);
            display: block;
            max-height: 200px;
            object-fit: cover;
        }
        .kt-x2 {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: rgba(40, 25, 15, 0.88);
            color: #fff;
            font-size: 1.55rem;
            font-weight: 900;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.35);
        }

        /* Cut-off banners */
        .kt-banner-closed {
            background: #FDECEA;
            border: 1px solid #E0B4B4;
            color: #B91C1C;
            border-radius: 14px;
            padding: 14px 16px;
            text-align: center;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .kt-banner-open {
            background: #E7F6EC;
            border: 1px solid #A7D7B7;
            color: #1B7A3D;
            border-radius: 14px;
            padding: 14px 16px;
            text-align: center;
            font-weight: 700;
            margin-bottom: 8px;
        }

        /* Section labels */
        .kt-section-label {
            font-weight: 800;
            color: #8B4513;
            font-size: 1.05rem;
            margin: 2px 0 2px;
        }
        .kt-section-note { color: #8a6d4b; font-size: 0.85rem; margin-bottom: 4px; }
        .kt-roomie-head {
            font-weight: 800;
            color: #8B4513;
            font-size: 1.05rem;
        }
        .kt-strike { text-decoration: line-through; color: #b08a5a; margin-right: 6px; }

        /* Live total box */
        .kt-total {
            background: #FFF3CD;
            border: 1px solid #F5A623;
            border-radius: 14px;
            padding: 16px 18px;
            margin: 10px 0 6px;
            color: #3B2407;
        }
        .kt-total-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            font-size: 0.95rem;
            margin: 4px 0;
        }
        .kt-total-final {
            display: flex;
            justify-content: space-between;
            font-size: 1.55rem;
            font-weight: 900;
            margin-top: 10px;
            color: #8B4513;
        }

        /* Confirmation summary */
        .kt-summary {
            background: #FFF8F0;
            border: 1px solid #ECD9C0;
            border-radius: 16px;
            padding: 16px 18px;
            margin: 8px 0;
        }
        .kt-summary-title {
            font-weight: 800;
            color: #8B4513;
            font-size: 1.15rem;
            margin-bottom: 10px;
        }

        /* PayNow / payment */
        .kt-qr {
            display: block;
            margin: 12px auto;
            width: 240px;
            max-width: 80%;
            border-radius: 14px;
        }
        .kt-qr-placeholder {
            width: 240px;
            height: 240px;
            margin: 12px auto;
            border-radius: 14px;
            background: #6F4E37;
            color: #FFF3CD;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            font-family: Georgia, serif;
            padding: 16px;
        }
        .kt-pay { text-align: center; font-size: 1rem; color: #3B2407; margin: 10px 4px; }
        .kt-footnote {
            text-align: center;
            font-style: italic;
            font-size: 0.8rem;
            color: #8a6d4b;
            margin: 12px 4px;
        }

        /* Buttons */
        .stButton > button {
            background-color: #8B4513;
            color: #FFF8F0;
            border: none;
            border-radius: 12px;
            font-weight: 700;
            padding: 0.5rem 1rem;
        }
        .stButton > button:hover { background-color: #6F360F; color: #fff; }
        .stButton > button:disabled { background-color: #c9b39c; color: #f3ece2; }

        /* Footer */
        .kt-footer {
            text-align: center;
            font-size: 0.8rem;
            color: #8B4513;
            opacity: 0.85;
            margin-top: 22px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------------
def render_header():
    st.markdown(f'<div class="kt-title">☕🍳 {SHOP_NAME}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="kt-tagline">Real SCS Butter. Not Margarine. 🧈</div>',
        unsafe_allow_html=True,
    )


def render_promo():
    st.markdown(
        f"""
        <div class="kt-promo">
            <div class="kt-ribbon">PROMO</div>
            <div class="kt-promo-title">🎉 Opening Promo — Limited Time!</div>
            <div class="kt-promo-prices">
                <span class="kt-old">${SOLO_ORIGINAL:.2f}</span>
                <span class="kt-new">${SOLO_BASE:.2f}</span>
            </div>
            <div class="kt-promo-sub">
                Enjoy our opening special — same great SCS butter kaya toast,
                just cheaper. Grab it while it lasts! 🍞☕
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    b64 = img_to_base64(HERO_IMAGE)
    if b64:
        st.markdown(
            f'<img class="kt-hero" src="data:image/png;base64,{b64}" alt="{SHOP_NAME}">',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="kt-hero-placeholder">{SHOP_NAME}</div>',
            unsafe_allow_html=True,
        )


def render_roomie_image():
    b64 = img_to_base64(HERO_IMAGE)
    if b64:
        st.markdown(
            f'<div class="kt-roomie-wrap">'
            f'<img class="kt-roomie-img" src="data:image/png;base64,{b64}" alt="Roomie Set">'
            f'<div class="kt-x2">x2</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="kt-hero-placeholder">{SHOP_NAME} · x2</div>',
            unsafe_allow_html=True,
        )


def render_cutoff_banner(is_open):
    if is_open:
        st.markdown(
            '<div class="kt-banner-open">✅ Now taking pre-orders for tomorrow '
            "morning! Cut-off at midnight.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class=\"kt-banner-closed\">🔒 Orders for today are closed. "
            "Come back tonight after 8 PM to pre-order for tomorrow's breakfast!</div>",
            unsafe_allow_html=True,
        )


def render_footer():
    st.markdown(
        '<div class="kt-footer">Made with ❤️ in Hall 16, NTU</div>',
        unsafe_allow_html=True,
    )


def person_inputs(label, key_prefix, disabled):
    st.markdown(f'<div class="kt-section-label">{label}</div>', unsafe_allow_html=True)
    egg = st.radio(
        "Egg type",
        EGG_TYPES,
        key=f"{key_prefix}_egg",
        horizontal=True,
        disabled=disabled,
    )
    drink = st.selectbox(
        "Drink",
        list(DRINKS.keys()),
        key=f"{key_prefix}_drink",
        format_func=drink_label,
        disabled=disabled,
    )
    return egg, drink


def room_inputs(disabled):
    c1, c2, c3 = st.columns(3)
    with c1:
        block = st.selectbox("Block", BLOCKS, key="blk", disabled=disabled)
    with c2:
        level = st.number_input("Level", min_value=1, max_value=10, value=1, step=1,
                                key="lvl", disabled=disabled)
    with c3:
        room = st.number_input("Room", min_value=1, max_value=20, value=1, step=1,
                               key="rm", disabled=disabled)
    return f"{block}-{int(level)}-{int(room):02d}"


# ---------------------------------------------------------------------------
# Telegram notifications
# ---------------------------------------------------------------------------
def send_telegram(chat_id, text):
    """Send a message via the Telegram Bot HTTP API (requests only)."""
    token = get_secret("BOT_TOKEN")
    if not token:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    return resp.ok


def build_owner_message(o):
    lines = [
        f"🆕 NEW ORDER — {SHOP_NAME}",
        f"📦 Set: {o['set_name']} (${o['base']:.2f})",
        f"🥚 P1 Egg: {o['p1_egg']} | ☕ P1 Drink: {drink_inline(o['p1_drink'])}",
    ]
    if o["set_choice"] == "roomie":
        lines.append(
            f"🥚 P2 Egg: {o['p2_egg']} | ☕ P2 Drink: {drink_inline(o['p2_drink'])}"
        )
    if o["collection_method"] == "delivery":
        collection = f"Delivery to Room {o['room_str']}"
    else:
        collection = "Prime Self-Collection"
    lines += [
        f"👤 Name: {o['name']}",
        f"📱 Contact: {o['contact']}",
        f"📍 Collection: {collection}",
        f"⏰ Pickup Time: {o['pickup']}",
        f"📝 Special Requests: {o['special'] or 'None'}",
        f"💰 TOTAL: ${o['total']:.2f}",
    ]
    return "\n".join(lines)


def build_customer_message(o):
    lines = [
        f"☕🍳 {SHOP_NAME} — Order Confirmation",
        "",
        f"Hi {o['name']}! Thanks for your pre-order 🙏",
        "",
        f"📦 {o['set_name']}",
        f"🥚 P1: {o['p1_egg']} egg · ☕ {o['p1_drink']}",
    ]
    if o["set_choice"] == "roomie":
        lines.append(f"🥚 P2: {o['p2_egg']} egg · ☕ {o['p2_drink']}")
    if o["collection_method"] == "delivery":
        lines.append(f"📍 Delivery to Room {o['room_str']} (Hall 16)")
    else:
        lines.append("📍 Self-collection at Prime Supermarket entrance")
    lines.append(f"⏰ Pickup: {o['pickup']}")
    if o["special"]:
        lines.append(f"📝 Notes: {o['special']}")
    lines += [
        "",
        f"💰 Total: ${o['total']:.2f}",
        "",
        f"Please PayNow/PayLah! ${o['total']:.2f} to {PAYNOW_NUMBER} and screenshot "
        "your receipt. Your order is confirmed once payment is received. "
        "See you in the morning! 🌅",
    ]
    return "\n".join(lines)


def notify(o):
    """Send the owner notification, and the customer one if a @handle was given."""
    owner_id = get_secret("OWNER_CHAT_ID")
    try:
        if owner_id:
            send_telegram(owner_id, build_owner_message(o))
    except Exception:
        pass

    handle = o["contact"].strip()
    if handle.startswith("@"):
        try:
            send_telegram(handle, build_customer_message(o))
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Order form
# ---------------------------------------------------------------------------
def compute_order(set_choice, p1_drink, p2_drink):
    """Return (base, items, total). items is a list of breakdown dicts."""
    if set_choice == "roomie":
        base, set_name = ROOMIE_BASE, "Roomie Set"
    else:
        base, set_name = SOLO_BASE, "Solo Set"

    items = [{"label": f"{set_name} base", "amount": base, "kind": "base"}]
    total = base

    p1_addon = DRINKS[p1_drink]
    items.append({"label": f"P1 {p1_drink}", "amount": p1_addon, "kind": "addon"})
    total += p1_addon

    if set_choice == "roomie":
        p2_addon = DRINKS[p2_drink]
        items.append({"label": f"P2 {p2_drink}", "amount": p2_addon, "kind": "addon"})
        total += p2_addon

    return base, set_name, items, total


def render_total_box(items, total):
    rows = ""
    for item in items:
        if item["kind"] == "base":
            amt = f"${item['amount']:.2f}"
        else:
            amt = f"+${item['amount']:.2f}" if item["amount"] > 0 else "Included"
        rows += (
            f'<div class="kt-total-row"><span>{item["label"]}</span>'
            f"<span>{amt}</span></div>"
        )
    st.markdown(
        f'<div class="kt-total">{rows}'
        f'<div class="kt-total-final"><span>Total</span>'
        f'<span>${total:.2f}</span></div></div>',
        unsafe_allow_html=True,
    )


def render_order_page(is_open):
    disabled = not is_open

    # Promo banner (dismissible, visible by default)
    if not st.session_state.get("promo_dismissed", False):
        render_promo()
        _, x_col = st.columns([5, 1])
        with x_col:
            if st.button("✕", key="dismiss_promo", help="Dismiss promo"):
                st.session_state.promo_dismissed = True
                st.rerun()

    # Hero image
    render_hero()

    # Cut-off banner
    render_cutoff_banner(is_open)

    if disabled:
        # Visually grey out the cards while orders are closed.
        st.markdown(
            "<style>div[data-testid='stVerticalBlockBorderWrapper']{opacity:0.55;}</style>",
            unsafe_allow_html=True,
        )

    # Step 1 — set selection
    with st.container(border=True):
        st.markdown('<div class="kt-section-label">Step 1 · Choose your set</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="kt-section-note">2 eggs + kaya butter toast (SCS butter), '
            "includes one standard drink (coffee or tea).</div>",
            unsafe_allow_html=True,
        )
        set_choice = st.radio(
            "Set",
            options=["solo", "roomie"],
            format_func=lambda x: (
                "🧍 Solo Set — $4.00  (Opening Promo, was $4.50)"
                if x == "solo"
                else "🛏️ Roomie Set — $7.00  (Opening Promo, was $8.00 · $3.50/pax)"
            ),
            key="set_choice",
            label_visibility="collapsed",
            disabled=disabled,
        )

    p1_egg = p1_drink = None
    p2_egg = p2_drink = None

    # Step 2 — breakfast choices
    if set_choice == "roomie":
        st.markdown(
            '<div class="kt-roomie-head">🛏️ Roomie Set — You + Your Roomie, '
            '<span class="kt-strike">$8.00</span> $7.00 '
            "(Only $3.50 per person — Opening Promo!)</div>",
            unsafe_allow_html=True,
        )
        render_roomie_image()
        with st.container(border=True):
            p1_egg, p1_drink = person_inputs("👤 Person 1", "p1", disabled)
        with st.container(border=True):
            p2_egg, p2_drink = person_inputs("👤 Person 2", "p2", disabled)
    else:
        with st.container(border=True):
            p1_egg, p1_drink = person_inputs("👤 Your breakfast", "p1", disabled)

    # Customer details
    with st.container(border=True):
        st.markdown('<div class="kt-section-label">Your details</div>',
                    unsafe_allow_html=True)
        name = st.text_input("Customer name", key="cust_name", disabled=disabled)
        contact = st.text_input(
            "Telegram handle or phone number",
            key="cust_contact",
            placeholder="@yourhandle or 9123 4567",
            help="Used to send your order confirmation.",
            disabled=disabled,
        )

    # Collection / delivery
    with st.container(border=True):
        st.markdown('<div class="kt-section-label">Collection & delivery</div>',
                    unsafe_allow_html=True)
        if set_choice == "roomie":
            collection_method = "delivery"
            st.markdown(
                '<div class="kt-section-note">🏠 Roomie Set is delivered to your '
                "Hall 16 room.</div>",
                unsafe_allow_html=True,
            )
            room_str = room_inputs(disabled)
        else:
            collection_method = st.radio(
                "Collection option",
                options=["delivery", "self"],
                format_func=lambda x: (
                    "🏠 Delivery to room — Hall 16 only"
                    if x == "delivery"
                    else "🛒 Self-collection at Prime Supermarket entrance"
                ),
                key="collection",
                disabled=disabled,
            )
            if collection_method == "delivery":
                room_str = room_inputs(disabled)
            else:
                room_str = None

    # Pickup time
    with st.container(border=True):
        st.markdown('<div class="kt-section-label">Pickup time</div>',
                    unsafe_allow_html=True)
        pickup = st.selectbox(
            "Pickup time (SGT)",
            pickup_time_options(),
            key="pickup",
            disabled=disabled,
        )

    # Special requests
    with st.container(border=True):
        st.markdown('<div class="kt-section-label">Special requests (optional)</div>',
                    unsafe_allow_html=True)
        special = st.text_area(
            "Special requests",
            key="special",
            placeholder="e.g. less sugar in the kopi, extra kaya...",
            label_visibility="collapsed",
            disabled=disabled,
        )

    # Live total
    base, set_name, items, total = compute_order(set_choice, p1_drink, p2_drink)
    render_total_box(items, total)

    # Submit
    if st.button("✅ Place My Order", type="primary",
                 use_container_width=True, disabled=disabled):
        if not name.strip() or not contact.strip():
            st.error("Please enter your name and a Telegram handle or phone number.")
        else:
            order = {
                "set_choice": set_choice,
                "set_name": set_name,
                "base": base,
                "p1_egg": p1_egg,
                "p1_drink": p1_drink,
                "p2_egg": p2_egg,
                "p2_drink": p2_drink,
                "name": name.strip(),
                "contact": contact.strip(),
                "collection_method": collection_method,
                "room_str": room_str,
                "pickup": pickup,
                "special": special.strip() if special else "",
                "items": items,
                "total": total,
            }
            notify(order)
            st.session_state.order = order
            st.session_state.submitted = True
            st.rerun()


# ---------------------------------------------------------------------------
# Confirmation page
# ---------------------------------------------------------------------------
def reset_form():
    for k in [
        "set_choice", "p1_egg", "p1_drink", "p2_egg", "p2_drink",
        "cust_name", "cust_contact", "collection", "blk", "lvl", "rm",
        "pickup", "special", "order",
    ]:
        st.session_state.pop(k, None)
    st.session_state.submitted = False


def render_confirmation():
    o = st.session_state.order

    st.markdown(
        '<div class="kt-banner-open">✅ Order received — thank you!</div>',
        unsafe_allow_html=True,
    )

    rows = [("Set", o["set_name"])]
    rows.append(("Person 1", f"{o['p1_egg']} egg · {o['p1_drink']}"))
    if o["set_choice"] == "roomie":
        rows.append(("Person 2", f"{o['p2_egg']} egg · {o['p2_drink']}"))
    rows.append(("Name", o["name"]))
    rows.append(("Contact", o["contact"]))
    if o["collection_method"] == "delivery":
        rows.append(("Collection", f"Delivery to Room {o['room_str']} (Hall 16)"))
    else:
        rows.append(("Collection", "Self-collection at Prime Supermarket"))
    rows.append(("Pickup time", o["pickup"]))
    rows.append(("Special requests", o["special"] or "None"))

    rows_html = "".join(
        f'<div class="kt-total-row">'
        f'<span style="color:#8a6d4b">{k}</span>'
        f'<span style="font-weight:600;text-align:right">{v}</span></div>'
        for k, v in rows
    )
    st.markdown(
        f'<div class="kt-summary"><div class="kt-summary-title">📋 Order Summary</div>'
        f"{rows_html}</div>",
        unsafe_allow_html=True,
    )

    # Total
    st.markdown(
        f'<div class="kt-total"><div class="kt-total-final">'
        f'<span>Total</span><span>${o["total"]:.2f}</span></div></div>',
        unsafe_allow_html=True,
    )

    # PayNow QR
    b64 = img_to_base64(QR_IMAGE)
    if b64:
        st.markdown(
            f'<img class="kt-qr" src="data:image/png;base64,{b64}" alt="PayNow QR">',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="kt-qr-placeholder">PayNow / PayLah!<br>QR code</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="kt-pay">Please PayNow/PayLah! the exact amount of '
        f'<b>${o["total"]:.2f}</b> to <b>{PAYNOW_NUMBER}</b>. '
        "Screenshot your payment receipt — your order is confirmed once "
        "payment is received.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="kt-footnote">⏱️ If your food is not collected within 15 minutes '
        "of your selected pickup time at Prime Supermarket, it will be left at the "
        "collection point.</div>",
        unsafe_allow_html=True,
    )

    if st.button("🔄 Place Another Order", use_container_width=True):
        reset_form()
        st.rerun()


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------
def main():
    inject_css()
    render_header()

    if st.session_state.get("submitted", False):
        render_confirmation()
    else:
        render_order_page(orders_are_open())

    render_footer()


main()
