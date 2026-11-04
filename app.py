import os
import sqlite3
from datetime import date
from flask import Flask, request, redirect, url_for, render_template_string, g, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deployment")
DATABASE = os.environ.get("DATABASE_PATH", "housebook.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS properties (
      id INTEGER PRIMARY KEY AUTOINCREMENT, owner_name TEXT NOT NULL,
      title TEXT NOT NULL, country TEXT NOT NULL, city TEXT NOT NULL,
      address TEXT, property_type TEXT NOT NULL, price_per_night REAL NOT NULL,
      description TEXT, photo_url TEXT, active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS bookings (
      id INTEGER PRIMARY KEY AUTOINCREMENT, property_id INTEGER NOT NULL,
      guest_name TEXT NOT NULL, guest_email TEXT NOT NULL, check_in TEXT NOT NULL,
      check_out TEXT NOT NULL, guests INTEGER NOT NULL, total_price REAL NOT NULL,
      payment_method TEXT NOT NULL, payment_status TEXT NOT NULL DEFAULT 'PENDING',
      booking_status TEXT NOT NULL DEFAULT 'PENDING',
      FOREIGN KEY(property_id) REFERENCES properties(id)
    );
    """)
    db.commit()
    db.close()

STYLE = """
:root{--navy:#07172f;--navy2:#0b1d39;--card:#101e36;--line:#20314d;--gold:#ffbd08;--white:#f7f9ff;--muted:#a9b7cc;--green:#22b68a}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--navy);color:var(--white);font-family:Inter,Arial,sans-serif;line-height:1.6}
a{color:inherit;text-decoration:none}.wrap{width:min(1120px,92%);margin:auto}
header{position:sticky;top:0;z-index:20;background:rgba(7,23,47,.96);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.nav{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:15px 0}.brand{display:flex;align-items:center;gap:11px;font-weight:900;font-size:21px;letter-spacing:-.5px}.logo{display:grid;place-items:center;background:linear-gradient(135deg,#ff8b00,var(--gold));color:#07172f;border-radius:12px;width:42px;height:42px;font-size:21px}
.navlinks{display:flex;gap:24px;align-items:center;color:#c3cee0;font-weight:600}.navlinks a:hover{color:var(--gold)}
.btn{display:inline-flex;justify-content:center;align-items:center;gap:9px;background:var(--gold);color:#07172f;border:0;border-radius:12px;padding:13px 20px;font-weight:800;cursor:pointer;box-shadow:0 8px 24px #ffbd0818}.btn:hover{filter:brightness(1.06);transform:translateY(-1px)}.btn.secondary{background:#1b2b45;color:#eaf0fa;box-shadow:none;border:1px solid #2b3d59}
.hero{padding:68px 0 46px;background:radial-gradient(ellipse at 85% 15%,#192d4d 0,transparent 42%),linear-gradient(180deg,#08172e,#07172f)}
.hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:42px;align-items:center}.eyebrow{color:var(--gold);font-weight:800;letter-spacing:2px;text-transform:uppercase;font-size:13px}.hero h1{font-size:clamp(38px,6vw,68px);line-height:1.06;letter-spacing:-2.5px;margin:15px 0 20px;font-weight:900}.hero h1 span{color:var(--gold)}.lead{color:#bdc9db;font-size:19px;max-width:580px}.hero-photo{min-height:370px;border-radius:24px;border:1px solid #2b3c59;background:#142742 center/cover;box-shadow:0 25px 60px #0004;position:relative;overflow:hidden}.photo-label{position:absolute;bottom:18px;left:18px;background:#07172fdd;border:1px solid #ffffff20;border-radius:12px;padding:12px 16px}
.searchbox{margin-top:28px;background:#101e36;border:1px solid #243650;border-radius:18px;padding:16px;display:grid;grid-template-columns:1.2fr 1fr 1fr auto;gap:10px}.searchbox input,.searchbox select,.field{width:100%;background:#08172e;color:white;border:1px solid #293b58;border-radius:10px;padding:13px;font:inherit;outline:none}.searchbox input::placeholder{color:#8191a9}
.section{padding:62px 0}.section-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:25px}.section h2{font-size:clamp(27px,4vw,40px);line-height:1.15;margin:8px 0;font-weight:900;letter-spacing:-1px}.sub{color:var(--muted);margin:0}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.property{background:var(--card);border:1px solid var(--line);border-radius:18px;overflow:hidden;transition:.2s}.property:hover{transform:translateY(-4px);border-color:#53647d}.property img{width:100%;height:220px;object-fit:cover;display:block;background:#172943}.property-body{padding:18px}.tag{display:inline-block;color:var(--gold);background:#ffbd0815;border:1px solid #ffbd0830;border-radius:7px;padding:4px 9px;font-size:12px;font-weight:800}.property h3{font-size:21px;margin:10px 0 4px}.location{color:var(--muted);font-size:14px}.price{font-size:22px;font-weight:900;color:var(--gold)}.price small{font-size:13px;color:var(--muted);font-weight:500}.property-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)}
.feature{background:linear-gradient(120deg,#10213c,#0b1a33);border:1px solid #253650;border-radius:22px;padding:28px;display:grid;grid-template-columns:1fr 1fr;gap:28px;align-items:center}.feature h2{margin-top:10px}.feature ul{padding-left:20px;color:#c2cede}.feature-art{min-height:260px;border-radius:16px;background:linear-gradient(135deg,#1b3555,#0b1b32);display:grid;place-items:center;font-size:75px}
footer{border-top:1px solid var(--line);padding:35px 0;color:var(--muted)}.footer-row{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}
.form-card{max-width:720px;margin:35px auto;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:25px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.form-card label{display:block;color:#bdc9db;font-size:14px;margin:8px 0}.form-card input,.form-card select,.form-card textarea{width:100%;background:#08172e;border:1px solid #293b58;color:#fff;padding:13px;border-radius:10px;font:inherit}.form-card textarea{min-height:110px}.full{grid-column:1/-1}.notice{background:#101e36;border:1px solid var(--line);padding:14px;border-radius:12px;color:#bac8dc;margin:15px 0}
@media(max-width:800px){.hero-grid,.feature{grid-template-columns:1fr}.hero{padding-top:42px}.hero-photo{min-height:270px}.searchbox{grid-template-columns:1fr 1fr}.searchbox .btn{grid-column:1/-1}.grid{grid-template-columns:1fr 1fr}.navlinks{gap:12px}.navlinks .hide-mobile{display:none}}
@media(max-width:520px){.grid{grid-template-columns:1fr}.nav{padding:11px 0}.brand{font-size:17px}.navlinks{font-size:13px}.navlinks .btn{padding:10px 12px}.hero h1{letter-spacing:-1.5px}.section{padding:45px 0}.searchbox{grid-template-columns:1fr}.form-grid{grid-template-columns:1fr}.full{grid-column:auto}}
"""

HOME = """
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HouseBook Kenya | Find Your Stay</title><style>{{ style|safe }}</style></head><body>
<header><div class="wrap nav"><a class="brand" href="/"><span class="logo">⌂</span> HOUSEBOOK <span style="color:var(--gold)">KENYA</span></a><nav class="navlinks"><a class="hide-mobile" href="#stays">Explore stays</a><a class="hide-mobile" href="#why">Why HouseBook</a><a href="/list-property" class="btn">＋ List Property</a></nav></div></header>
<section class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">YOUR NEXT STAY STARTS HERE</div><h1>Find your perfect<br><span>stay in Kenya.</span></h1><p class="lead">Discover comfortable homes, apartments and holiday escapes. Book a place that feels like home.</p><a href="#stays" class="btn">Explore properties →</a> <a href="/list-property" class="btn secondary">Become a host</a></div>
<div class="hero-photo" style="background-image:linear-gradient(0deg,#07172f99,transparent 60%),url('https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1100&q=85')"><div class="photo-label"><strong>Beautiful stays, memorable moments</strong><br><span style="color:var(--muted)">Explore Kenya one stay at a time</span></div></div></div>
<form class="searchbox" method="get" action="/"><input name="city" placeholder="Where are you going?" value="{{ city }}"><select name="type"><option value="">All property types</option>{% for t in types %}<option value="{{t}}" {% if prop_type==t %}selected{% endif %}>{{t}}</option>{% endfor %}<option value="Holiday rental">Holiday rental</option></select><input name="max_price" type="number" min="0" placeholder="Max price / night (KES)" value="{{max_price}}"><button class="btn">Search stays</button></form></div></section>
<section class="section wrap" id="stays"><div class="section-head"><div><div class="eyebrow">HANDPICKED FOR YOU</div><h2>Places worth staying</h2><p class="sub">Find your next favourite place, from city apartments to peaceful escapes.</p></div><a href="/list-property" class="btn secondary">List your property →</a></div>
<div class="grid">{% for p in properties %}<article class="property"><img src="{{p.photo_url or fallback}}" alt="{{p.title}}" loading="lazy"><div class="property-body"><span class="tag">{{p.property_type}}</span><h3>{{p.title}}</h3><div class="location">⌖ {{p.city}}, {{p.country}}</div><p style="color:#bac8dc">{{(p.description or '')[:105]}}</p><div class="property-foot"><div class="price">KES {{ "%.0f"|format(p.price_per_night) }} <small>/ night</small></div><a class="btn" href="/book/{{p.id}}">Book →</a></div></div></article>{% else %}<div class="notice">No properties match your search yet. Be the first host to list a property.</div>{% endfor %}</div></section>
<section class="section wrap" id="why"><div class="feature"><div><div class="eyebrow">TRAVEL WITH CONFIDENCE</div><h2>Stay somewhere<br><span style="color:var(--gold)">that feels right.</span></h2><p class="lead">A simpler way to discover and request your next accommodation in Kenya.</p><ul><li>Explore a range of property types</li><li>See nightly prices upfront</li><li>Request bookings in a few steps</li></ul><a class="btn" href="#stays">Find your stay →</a></div><div class="feature-art">⌂</div></div></section>
<footer><div class="wrap footer-row"><a class="brand" href="/"><span class="logo">⌂</span> HOUSEBOOK <span style="color:var(--gold)">KENYA</span></a><span>Find a stay. Feel at home.</span><span>© HouseBook Kenya</span></div></footer></body></html>
"""

LISTING = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>List your property | HouseBook Kenya</title><style>{{style|safe}}</style></head><body><header><div class="wrap nav"><a class="brand" href="/"><span class="logo">⌂</span> HOUSEBOOK <span style="color:var(--gold)">KENYA</span></a><a class="btn secondary" href="/">← Back home</a></div></header><main class="wrap"><form class="form-card" method="post"><div class="eyebrow">WELCOME, HOST</div><h2>List your property</h2><p class="sub">Share your space with guests looking for their next stay.</p><div class="form-grid">
<div><label>Owner name *</label><input name="owner_name" required></div><div><label>Property title *</label><input name="title" required></div><div><label>Country *</label><input name="country" value="Kenya" required></div><div><label>City *</label><input name="city" required></div><div><label>Area / address</label><input name="address"></div><div><label>Property type *</label><select name="property_type"><option>Apartment</option><option>Bedsitter</option><option>Studio</option><option>House</option><option>Holiday rental</option><option>Villa</option></select></div><div><label>Price per night (KES) *</label><input name="price" type="number" min="1" step=".01" required></div><div><label>Photo URL</label><input name="photo_url" type="url" placeholder="https://..."></div><div class="full"><label>Description</label><textarea name="description" placeholder="Describe your property, amenities and nearby attractions"></textarea></div></div><div class="notice">Listings are submitted as provided and are not independently verified by this demo.</div><button class="btn" style="width:100%">Submit property →</button></form></main><footer><div class="wrap footer-row"><span>HouseBook Kenya</span><a href="/">Home</a></div></footer></body></html>
"""

BOOKING = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Book {{p.title}} | HouseBook Kenya</title><style>{{style|safe}}</style></head><body><header><div class="wrap nav"><a class="brand" href="/"><span class="logo">⌂</span> HOUSEBOOK <span style="color:var(--gold)">KENYA</span></a><a class="btn secondary" href="/">← Explore stays</a></div></header><main class="wrap"><form class="form-card" method="post"><div class="eyebrow">YOUR NEXT STAY</div><h2>Request your booking</h2><div class="notice"><strong>{{p.title}}</strong><br>{{p.city}}, {{p.country}} · <span style="color:var(--gold)">KES {{ "%.0f"|format(p.price_per_night) }} / night</span></div><div class="form-grid"><div class="full"><label>Full name *</label><input name="guest_name" required></div><div class="full"><label>Email address *</label><input name="guest_email" type="email" required></div><div><label>Check-in *</label><input name="check_in" type="date" min="{{today}}" required></div><div><label>Check-out *</label><input name="check_out" type="date" min="{{today}}" required></div><div><label>Guests *</label><input name="guests" type="number" min="1" max="30" value="1" required></div><div><label>Payment method</label><select name="payment_method"><option value="MPESA">M-Pesa</option><option value="PAYPAL">PayPal</option></select></div></div><div class="notice">This creates a booking request only. Payment is not collected here and booking is not confirmed until availability and payment are verified.</div><button class="btn" style="width:100%">Request booking →</button></form></main></body></html>
"""

@app.route("/")
def home():
    db = get_db()
    city = request.args.get("city", "").strip()
    prop_type = request.args.get("type", "").strip()
    max_price = request.args.get("max_price", "").strip()
    sql = "SELECT * FROM properties WHERE active=1"
    params = []
    if city:
        sql += " AND city LIKE ?"; params.append("%"+city+"%")
    if prop_type:
        sql += " AND property_type=?"; params.append(prop_type)
    if max_price:
        try:
            amount=float(max_price)
            if amount<0: abort(400)
            sql += " AND price_per_night<=?"; params.append(amount)
        except ValueError: abort(400)
    properties=db.execute(sql+" ORDER BY id DESC",params).fetchall()
    return render_template_string(HOME, style=STYLE, properties=properties, city=city,
        prop_type=prop_type, max_price=max_price,
        types=["Studio","Bedsitter","Apartment","House","Villa"],
        fallback="https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=900&q=80")

@app.route("/list-property", methods=["GET","POST"])
def list_property():
    if request.method=="GET": return render_template_string(LISTING,style=STYLE)
    f=request.form
    try:
        price=float(f.get("price",""))
        if price<=0: abort(400)
    except ValueError: abort(400)
    db=get_db()
    db.execute("""INSERT INTO properties(owner_name,title,country,city,address,property_type,price_per_night,description,photo_url)
    VALUES(?,?,?,?,?,?,?,?,?)""",(f["owner_name"].strip(),f["title"].strip(),f["country"].strip(),f["city"].strip(),f.get("address","").strip(),f["property_type"],price,f.get("description","").strip(),f.get("photo_url","").strip()))
    db.commit()
    return redirect(url_for("home"))

@app.route("/book/<int:property_id>",methods=["GET","POST"])
def book(property_id):
    db=get_db(); p=db.execute("SELECT * FROM properties WHERE id=? AND active=1",(property_id,)).fetchone()
    if not p: abort(404)
    if request.method=="GET": return render_template_string(BOOKING,style=STYLE,p=p,today=date.today().isoformat())
    f=request.form
    try: check_in=date.fromisoformat(f["check_in"]); check_out=date.fromisoformat(f["check_out"]); guests=int(f["guests"])
    except (ValueError,KeyError): abort(400)
    if check_in<date.today() or check_out<=check_in: return "Invalid check-in or check-out dates.",400
    if not 1<=guests<=30: abort(400)
    name=f.get("guest_name","").strip(); email=f.get("guest_email","").strip(); method=f.get("payment_method","")
    if not name or not email or method not in ("MPESA","PAYPAL"): abort(400)
    conflict=db.execute("""SELECT id FROM bookings WHERE property_id=? AND booking_status IN ('PENDING','CONFIRMED') AND check_in<? AND check_out>?""",(property_id,check_out.isoformat(),check_in.isoformat())).fetchone()
    if conflict: return "Dates are not currently available. Choose other dates.",409
    total=(check_out-check_in).days*p["price_per_night"]
    cur=db.execute("""INSERT INTO bookings(property_id,guest_name,guest_email,check_in,check_out,guests,total_price,payment_method,payment_status,booking_status) VALUES(?,?,?,?,?,?,?,?, 'PENDING','PENDING')""",(property_id,name,email,check_in.isoformat(),check_out.isoformat(),guests,total,method))
    db.commit()
    return f"Booking request #{cur.lastrowid} created. Total: KES {total:.2f}. Payment has NOT been received and booking is NOT confirmed.",201

@app.route("/health")
def health(): return {"status":"ok","app":"HouseBook Kenya"}

with app.app_context(): init_db()

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
