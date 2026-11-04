import os, sqlite3, secrets, json
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template, g, abort, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-production")
DB_PATH = os.environ.get("DATABASE_PATH", "talanta_tickets.db")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    conn=g.pop("db",None)
    if conn: conn.close()

def init_db():
    conn=sqlite3.connect(DB_PATH)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS orders(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      reference TEXT UNIQUE NOT NULL,
      customer_name TEXT NOT NULL,
      email TEXT NOT NULL,
      phone TEXT NOT NULL,
      category TEXT NOT NULL,
      quantity INTEGER NOT NULL,
      currency TEXT NOT NULL,
      unit_price REAL NOT NULL,
      total REAL NOT NULL,
      payment_method TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'PENDING',
      created_at TEXT NOT NULL
    );
    """)
    conn.commit(); conn.close()

TICKETS = {
 "west": {"name":"Category 1 Lower Grandstand","area":"WEST STAND TIER 1","price":103,"desc":"Prime mid-pitch grandstand view with covered canopy, adjacent to players tunnel","accent":"gold"},
 "vip": {"name":"Presidential VIP Hospitality & Skybox","area":"PRESIDENTIAL PAVILION","price":249,"desc":"Executive lounge access, fine refreshments, private bar & VIP parking pass","accent":"vip"},
 "east": {"name":"Category 2 Upper Grandstand","area":"EAST GRANDSTAND TIER 2","price":75,"desc":"Panoramic match observation with full pitch visibility and covered roof acoustics","accent":"gold"},
 "ajax": {"name":"North Stand — Ajax Supporters End","area":"NORTH GOAL STAND (AJAX END)","price":55,"desc":"Dedicated supporter zone behind north goal for Ajax fans in red & white","accent":"red"},
 "bayern": {"name":"South Stand — Bayern München Supporters End","area":"SOUTH GOAL STAND (BAYERN END)","price":55,"desc":"Dedicated supporter zone behind south goal for Bayern fans in red & navy","accent":"red"}
}
def price_for(code,currency):
    # Illustrative display conversion only; actual checkout must use provider-supported currency.
    rates={"EUR":1,"KES":145,"USD":1.08}
    return round(TICKETS[code]["price"]*rates.get(currency,1),2)

@app.route("/")
def home():
    return render_template("index.html", tickets=TICKETS)

@app.route("/reserve/<code>", methods=["GET","POST"])
def reserve(code):
    if code not in TICKETS: abort(404)
    currency=request.values.get("currency","EUR")
    if currency not in ("EUR","KES","USD"): currency="EUR"
    if request.method=="GET":
        return render_template("checkout.html", ticket=TICKETS[code], code=code, currency=currency, unit=price_for(code,currency))
    f=request.form
    name=f.get("name","").strip(); email=f.get("email","").strip(); phone=f.get("phone","").strip()
    try: qty=int(f.get("quantity","1"))
    except ValueError: abort(400)
    method=f.get("payment_method","")
    if not name or not email or not phone or not 1<=qty<=10 or method not in ("MPESA","PAYPAL"):
        return "Please check your details and quantity (1–10).",400
    unit=price_for(code,currency); total=round(unit*qty,2)
    ref="TAL-"+secrets.token_hex(5).upper()
    conn=db()
    conn.execute("""INSERT INTO orders(reference,customer_name,email,phone,category,quantity,currency,unit_price,total,payment_method,status,created_at)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,'PENDING',?)""",
      (ref,name,email,phone,code,qty,currency,unit,total,method,datetime.utcnow().isoformat()))
    conn.commit()
    return render_template("success.html",ref=ref,name=name,ticket=TICKETS[code],qty=qty,currency=currency,total=total)

@app.route("/order/<reference>")
def order_status(reference):
    row=db().execute("SELECT reference,category,quantity,currency,total,payment_method,status,created_at FROM orders WHERE reference=?",(reference,)).fetchone()
    if not row: abort(404)
    return jsonify(dict(row))

@app.route("/health")
def health(): return {"status":"ok","app":"Talanta Stadium Ticket Demo"}

@app.route("/admin/orders")
def admin_orders():
    # Demo-only endpoint; add proper authentication before production.
    key=os.environ.get("ADMIN_KEY")
    if not key or request.args.get("key") != key: abort(403)
    rows=db().execute("SELECT * FROM orders ORDER BY id DESC LIMIT 200").fetchall()
    return jsonify([dict(r) for r in rows])

with app.app_context(): init_db()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
