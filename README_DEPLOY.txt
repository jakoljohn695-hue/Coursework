TALANTA STADIUM TICKET WEBSITE — DEMO RECREATION

This is an original, unofficial recreation inspired by the supplied reference's navy/gold styling and layout. It is not the original website, does not establish event legitimacy, and does not provide official tickets.

LOCAL TEST:
  pip install -r requirements.txt
  python app.py
  open http://127.0.0.1:5000

RENDER:
1. Upload all ZIP contents to a GitHub repository (keep app.py, Procfile, requirements.txt and render.yaml at repository root).
2. Render Dashboard > New > Blueprint > connect repository > apply.
3. Persistent disk is specified in render.yaml. If your Render plan does not support disks, use PostgreSQL or another persistent database; SQLite on ephemeral storage can lose orders.
4. Set ADMIN_KEY to a long secret in Render environment variables.
5. Deploy and open the Render URL. /health checks the app.

RAILWAY DATABASE:
This app currently uses SQLite. DATABASE_PUBLIC_URL from Railway is a PostgreSQL URL and cannot be used as DATABASE_PATH. To use Railway PostgreSQL, code must be migrated to PostgreSQL (psycopg) and DATABASE_URL, then connect Railway service's private connection URL when app and DB are on Railway, or public URL only if connecting externally and Railway allows it.

PAYMENTS:
M-Pesa and PayPal are NOT integrated. Orders are saved as PENDING only. Do not take customer money or advertise orders as valid tickets. Connect a licensed payment provider and verify callbacks/server-side transaction status before changing an order to PAID.

SECURITY / PRODUCTION:
- Admin JSON endpoint /admin/orders?key=... is a demo key gate, not production admin auth.
- Add proper authentication, CSRF protection, rate limits, privacy/terms/refund policies, secure payment integration, QR issuance and email delivery before production.
- Ticket price conversion rates are illustrative fixed values. Replace with live/approved pricing and define payment settlement currency.
- Event date, venue, clubs, capacity, seat counts, ticket availability and "official" claims must be independently verified with organizer. This project deliberately labels itself unofficial/demo.
