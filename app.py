import os, sqlite3, secrets, requests
from math import ceil
from datetime import date
from flask import Flask, request, redirect, url_for, render_template_string, g, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-only-change-me")
DATABASE = os.environ.get("DATABASE_PATH", "housebook.db")

def get_db():
    if "db" not in g:
        g.db=sqlite3.connect(DATABASE, timeout=20)
        g.db.row_factory=sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db=g.pop("db",None)
    if db: db.close()

def init_db():
    db=sqlite3.connect(DATABASE)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS properties(
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_name TEXT NOT NULL, title TEXT NOT NULL,
      country TEXT NOT NULL, city TEXT NOT NULL, address TEXT, property_type TEXT NOT NULL,
      price_per_night REAL NOT NULL, description TEXT, photo_url TEXT, active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS bookings(
      id INTEGER PRIMARY KEY AUTOINCREMENT, property_id INTEGER NOT NULL, guest_name TEXT NOT NULL,
      guest_email TEXT NOT NULL, check_in TEXT NOT NULL, check_out TEXT NOT NULL, guests INTEGER NOT NULL,
      total_price REAL NOT NULL, payment_method TEXT NOT NULL, payment_status TEXT NOT NULL DEFAULT 'PENDING',
      booking_status TEXT NOT NULL DEFAULT 'PENDING', payhero_reference TEXT, payhero_checkout_id TEXT,
      mpesa_receipt TEXT, FOREIGN KEY(property_id) REFERENCES properties(id));
    """)
    cols={r[1] for r in db.execute("PRAGMA table_info(bookings)")}
    for col in ("payhero_reference","payhero_checkout_id","mpesa_receipt"):
        if col not in cols: db.execute(f"ALTER TABLE bookings ADD COLUMN {col} TEXT")
    db.commit(); db.close()

TYPES=["Studio","Bedsitter","Apartment","House","Holiday rental"]
PAGE="""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HouseBook Kenya</title><style>
body{font-family:Arial;background:#f4f6f8;margin:0;color:#17202a}header{background:#124e3b;color:white;padding:22px}main{max-width:900px;margin:auto;padding:18px}.card{background:white;padding:18px;margin:14px 0;border-radius:12px}
input,select,textarea,button{box-sizing:border-box;width:100%;padding:12px;margin:7px 0;border:1px solid #ddd;border-radius:7px}button{background:#146c43;color:white;border:0}img{max-width:100%;border-radius:8px}a{color:#146c43}</style></head><body><header><h1>HouseBook Kenya</h1><p>Find a place to stay or list your property.</p></header><main>
<div class="card"><h2>Search houses</h2><form><input name="city" placeholder="City" value="{{city}}"><select name="type"><option value="">All types</option>{% for t in types %}<option {% if selected_type==t %}selected{% endif %}>{{t}}</option>{% endfor %}</select><input name="max_price" type="number" min="0" placeholder="Maximum nightly price (KES)" value="{{max_price}}"><button>Search</button></form></div>
<div class="card"><h2>List your property</h2><form action="/properties" method="post"><input name="owner_name" placeholder="Owner name" required><input name="title" placeholder="Property title" required><input name="country" value="Kenya" required><input name="city" placeholder="City" required><input name="address" placeholder="Area/address"><select name="property_type">{% for t in types %}<option>{{t}}</option>{% endfor %}</select><input name="price" type="number" min="1" step=".01" placeholder="Price per night KES" required><input name="photo_url" type="url" placeholder="Photo URL"><textarea name="description" placeholder="Describe property"></textarea><button>Submit property</button></form><small>Listings are not automatically verified.</small></div>
<h2>Available properties</h2>{% for p in properties %}<div class="card">{% if p.photo_url %}<img src="{{p.photo_url}}" alt="Property photo">{% endif %}<h3>{{p.title}}</h3><p>{{p.property_type}} · {{p.city}}, {{p.country}}</p><p>{{p.description or ""}}</p><b>KES {{ "%.2f"|format(p.price_per_night) }} per night</b><p><small>Listed by {{p.owner_name}} · Not verified</small></p><a href="/book/{{p.id}}">Book this property</a></div>{% else %}<p>No matching properties.</p>{% endfor %}</main></body></html>"""
BOOK="""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Book property</title><style>body{font-family:Arial;max-width:650px;margin:auto;padding:20px}input,select,button{box-sizing:border-box;width:100%;padding:12px;margin:8px 0}button{background:#146c43;color:white;border:0}</style></head><body><h1>Book {{p.title}}</h1><p>{{p.city}} · KES {{ "%.2f"|format(p.price_per_night) }}/night</p><form method="post"><input name="guest_name" placeholder="Full name" required><input name="guest_email" type="email" placeholder="Email" required><label>Check-in</label><input name="check_in" type="date" min="{{today}}" required><label>Check-out</label><input name="check_out" type="date" min="{{today}}" required><label>Guests</label><input name="guests" type="number" min="1" max="30" value="1" required><label>M-Pesa phone number</label><input name="phone_number" placeholder="07XXXXXXXX" required><input type="hidden" name="payment_method" value="MPESA"><button>Request booking & pay by M-Pesa</button></form><p>Booking is pending until PayHero confirms payment.</p></body></html>"""

@app.route("/")
def home():
    city=request.args.get("city","").strip()[:100]; typ=request.args.get("type",""); maxp=request.args.get("max_price","")
    sql="SELECT * FROM properties WHERE active=1"; args=[]
    if city: sql+=" AND city LIKE ?"; args.append("%"+city+"%")
    if typ in TYPES: sql+=" AND property_type=?"; args.append(typ)
    if maxp:
        try:
            v=float(maxp)
            if v<0: abort(400)
            sql+=" AND price_per_night<=?"; args.append(v)
        except ValueError: abort(400)
    props=get_db().execute(sql+" ORDER BY id DESC",args).fetchall()
    return render_template_string(PAGE,properties=props,city=city,selected_type=typ,max_price=maxp,types=TYPES)

@app.route("/properties",methods=["POST"])
def add_property():
    f=request.form
    try: price=float(f.get("price",""))
    except ValueError: abort(400)
    if price<=0: abort(400)
    vals=[f.get(k,"").strip() for k in ("owner_name","title","country","city")]
    if any(not x for x in vals): abort(400)
    photo=f.get("photo_url","").strip()
    if photo and not photo.startswith(("https://","http://")): abort(400)
    get_db().execute("""INSERT INTO properties(owner_name,title,country,city,address,property_type,price_per_night,description,photo_url) VALUES(?,?,?,?,?,?,?,?,?)""",
      (*vals,f.get("address","").strip(),f.get("property_type","House"),price,f.get("description","").strip(),photo))
    get_db().commit(); return redirect(url_for("home"))

@app.route("/book/<int:pid>",methods=["GET","POST"])
def book(pid):
    db=get_db(); p=db.execute("SELECT * FROM properties WHERE id=? AND active=1",(pid,)).fetchone()
    if not p: abort(404)
    if request.method=="GET": return render_template_string(BOOK,p=p,today=date.today().isoformat())
    f=request.form
    try: ci=date.fromisoformat(f["check_in"]); co=date.fromisoformat(f["check_out"]); guests=int(f["guests"])
    except (ValueError,KeyError): abort(400)
    if ci<date.today() or co<=ci or not 1<=guests<=30: return "Invalid dates or guest count",400
    name=f.get("guest_name","").strip(); email=f.get("guest_email","").strip(); phone=f.get("phone_number","").strip()
    if not name or not email or not phone: abort(400)
    conflict=db.execute("""SELECT id FROM bookings WHERE property_id=? AND booking_status IN ('PENDING','CONFIRMED') AND check_in<? AND check_out>?""",(pid,co.isoformat(),ci.isoformat())).fetchone()
    if conflict: return "Dates unavailable; select other dates.",409
    total=(co-ci).days*p["price_per_night"]
    cur=db.execute("""INSERT INTO bookings(property_id,guest_name,guest_email,check_in,check_out,guests,total_price,payment_method) VALUES(?,?,?,?,?,?,?,'MPESA')""",(pid,name,email,ci.isoformat(),co.isoformat(),guests,total))
    booking_id=cur.lastrowid
    username=os.environ.get("PAYHERO_API_USERNAME","").strip(); password=os.environ.get("PAYHERO_API_PASSWORD","").strip()
    channel=os.environ.get("PAYHERO_CHANNEL_ID","").strip(); site=os.environ.get("PUBLIC_BASE_URL","").rstrip("/")
    if not username or not password or not channel or not site:
        db.commit(); return "Booking saved, but PayHero is not configured. Ask admin to finish setup.",503
    amount=int(ceil(total)); ref=f"HBK-{booking_id}-{secrets.token_hex(4).upper()}"
    payload={"amount":amount,"phone_number":phone,"channel_id":int(channel),"provider":"m-pesa","external_reference":ref,"customer_name":name,"callback_url":site+"/payhero/callback"}
    try:
        r=requests.post("https://backend.payhero.co.ke/api/v2/payments",auth=(username,password),json=payload,headers={"Content-Type":"application/json"},timeout=25); data=r.json()
    except (requests.RequestException,ValueError):
        db.commit(); return "Booking saved but PayHero could not be reached. Contact support.",502
    if r.status_code in (200,201) and data.get("success"):
        db.execute("UPDATE bookings SET payhero_reference=?,payhero_checkout_id=? WHERE id=?",(ref,str(data.get("CheckoutRequestID","")),booking_id)); db.commit()
        return f"Booking #{booking_id} created. STK Push requested for {phone}, KES {amount}. Enter your M-Pesa PIN. Booking stays pending until payment confirmation.",201
    app.logger.error("PayHero initiation error: %s",data); db.commit(); return "Booking saved but PayHero STK initiation failed. Contact support.",502

@app.route("/payhero/callback",methods=["POST"])
def payhero_callback():
    payload=request.get_json(silent=True) or {}; data=payload.get("response") or {}; ref=str(data.get("ExternalReference","")).strip()
    if not ref: return {"received":False},400
    db=get_db(); b=db.execute("SELECT * FROM bookings WHERE payhero_reference=?",(ref,)).fetchone()
    if not b: app.logger.warning("Unknown PayHero reference %s",ref); return {"received":True},200
    status=str(data.get("Status","")).lower(); code=data.get("ResultCode"); amount=data.get("Amount")
    success=payload.get("status") is True and status=="success" and str(code)=="0"
    matches=amount is not None and int(float(amount))==int(ceil(b["total_price"]))
    if b["payment_status"]!="PAID":
        if success and matches:
            db.execute("UPDATE bookings SET payment_status='PAID',booking_status='CONFIRMED',mpesa_receipt=? WHERE id=? AND payment_status!='PAID'",(str(data.get("MpesaReceiptNumber","")),b["id"]))
        elif status in ("failed","cancelled") or (code is not None and str(code)!="0"):
            db.execute("UPDATE bookings SET payment_status='FAILED' WHERE id=? AND payment_status!='PAID'",(b["id"],))
        elif success and not matches: app.logger.error("PayHero amount mismatch booking=%s",b["id"])
        db.commit()
    return {"received":True},200

@app.route("/health")
def health(): return {"status":"ok","app":"HouseBook Kenya"}

with app.app_context(): init_db()
if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=False)
