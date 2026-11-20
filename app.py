import os, random, time, secrets
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY') or secrets.token_hex(32)
url=os.environ.get('DATABASE_URL','sqlite:///eggblitz.db')
if url.startswith('postgres://'): url='postgresql://'+url[len('postgres://'):]
app.config.update(SQLALCHEMY_DATABASE_URI=url,SQLALCHEMY_TRACK_MODIFICATIONS=False,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',SESSION_COOKIE_SECURE=os.environ.get('RENDER')=='true')
db=SQLAlchemy(app)
class User(db.Model):
 id=db.Column(db.Integer,primary_key=True)
 username=db.Column(db.String(24),unique=True,nullable=False)
 password=db.Column(db.String(255),nullable=False)
 coins=db.Column(db.Integer,default=250,nullable=False)
 last_daily=db.Column(db.Float,default=0)
 last_click=db.Column(db.Float,default=0)
 last_challenge=db.Column(db.Float,default=0)
 streak=db.Column(db.Integer,default=0)
 tag=db.Column(db.String(20),default='')
 creatures=db.relationship('Owned',backref='owner',cascade='all, delete-orphan')
class Owned(db.Model):
 id=db.Column(db.Integer,primary_key=True)
 user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True)
 species=db.Column(db.String(32),nullable=False)
class Redemption(db.Model):
 id=db.Column(db.Integer,primary_key=True)
 user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
 code=db.Column(db.String(32),nullable=False)
 __table_args__=(db.UniqueConstraint('user_id','code'),)
class Code(db.Model):
 code=db.Column(db.String(32),primary_key=True)
 reward=db.Column(db.String(32),nullable=False)
 value=db.Column(db.String(64),nullable=False)
 max_uses=db.Column(db.Integer,default=0)
 uses=db.Column(db.Integer,default=0)

SPECIES=[
 ('Pebblit','Common',8,'🪨'),('Sproutle','Common',12,'🌱'),('Bloop','Common',16,'🫧'),('Chickzap','Common',20,'🐣'),
 ('Frostbyte','Rare',45,'❄️'),('Flameling','Rare',58,'🔥'),('Voltfox','Rare',72,'🦊'),('Aqualotl','Rare',88,'🦎'),
 ('Glitchcat','Epic',180,'🐈'),('Prismoth','Epic',240,'🦋'),('Neon Hydra','Epic',310,'🐉'),
 ('Solar Rex','Legendary',800,'🦖'),('Thunder Seraph','Legendary',1050,'⚡'),('Void Phoenix','Legendary',1400,'🪽'),
 ('Astral Sovereign','Mythic',4500,'👑'),('Eclipse Leviathan','Mythic',6500,'🐲'),
 ('Blitz Zero','Secret',12000,'💠')]

# 300 additional hand-structured pixel species: 20 body families × 15 distinct themes.
SPECIES += [('Comet Mole', 'Common', 10, '✨'), ('Bramble Mole', 'Common', 17, '✨'), ('Clockwork Mole', 'Common', 24, '✨'), ('Coral Mole', 'Rare', 86, '✨'), ('Lantern Mole', 'Rare', 93, '✨'), ('Tundra Mole', 'Rare', 100, '✨'), ('Meteor Mole', 'Epic', 302, '✨'), ('Circuit Mole', 'Epic', 309, '✨'), ('Marsh Mole', 'Epic', 316, '✨'), ('Crown Mole', 'Legendary', 1163, '✨'), ('Fossil Mole', 'Legendary', 1170, '✨'), ('Kite Mole', 'Legendary', 1177, '✨'), ('Crystal Mole', 'Mythic', 5084, '✨'), ('Ink Mole', 'Mythic', 5091, '✨'), ('Bubble Mole', 'Mythic', 5098, '✨'), ('Comet Crab', 'Common', 13, '✨'), ('Bramble Crab', 'Common', 20, '✨'), ('Clockwork Crab', 'Common', 27, '✨'), ('Coral Crab', 'Rare', 89, '✨'), ('Lantern Crab', 'Rare', 96, '✨'), ('Tundra Crab', 'Rare', 103, '✨'), ('Meteor Crab', 'Epic', 305, '✨'), ('Circuit Crab', 'Epic', 312, '✨'), ('Marsh Crab', 'Epic', 319, '✨'), ('Crown Crab', 'Legendary', 1166, '✨'), ('Fossil Crab', 'Legendary', 1173, '✨'), ('Kite Crab', 'Legendary', 1180, '✨'), ('Crystal Crab', 'Mythic', 5087, '✨'), ('Ink Crab', 'Mythic', 5094, '✨'), ('Bubble Crab', 'Mythic', 5101, '✨'), ('Comet Owl', 'Common', 16, '✨'), ('Bramble Owl', 'Common', 23, '✨'), ('Clockwork Owl', 'Common', 30, '✨'), ('Coral Owl', 'Rare', 92, '✨'), ('Lantern Owl', 'Rare', 99, '✨'), ('Tundra Owl', 'Rare', 106, '✨'), ('Meteor Owl', 'Epic', 308, '✨'), ('Circuit Owl', 'Epic', 315, '✨'), ('Marsh Owl', 'Epic', 322, '✨'), ('Crown Owl', 'Legendary', 1169, '✨'), ('Fossil Owl', 'Legendary', 1176, '✨'), ('Kite Owl', 'Legendary', 1183, '✨'), ('Crystal Owl', 'Mythic', 5090, '✨'), ('Ink Owl', 'Mythic', 5097, '✨'), ('Bubble Owl', 'Mythic', 5104, '✨'), ('Comet Mantis', 'Common', 19, '✨'), ('Bramble Mantis', 'Common', 26, '✨'), ('Clockwork Mantis', 'Common', 33, '✨'), ('Coral Mantis', 'Rare', 95, '✨'), ('Lantern Mantis', 'Rare', 102, '✨'), ('Tundra Mantis', 'Rare', 109, '✨'), ('Meteor Mantis', 'Epic', 311, '✨'), ('Circuit Mantis', 'Epic', 318, '✨'), ('Marsh Mantis', 'Epic', 325, '✨'), ('Crown Mantis', 'Legendary', 1172, '✨'), ('Fossil Mantis', 'Legendary', 1179, '✨'), ('Kite Mantis', 'Legendary', 1186, '✨'), ('Crystal Mantis', 'Mythic', 5093, '✨'), ('Ink Mantis', 'Mythic', 5100, '✨'), ('Bubble Mantis', 'Mythic', 5107, '✨'), ('Comet Turtle', 'Common', 22, '✨'), ('Bramble Turtle', 'Common', 29, '✨'), ('Clockwork Turtle', 'Common', 36, '✨'), ('Coral Turtle', 'Rare', 98, '✨'), ('Lantern Turtle', 'Rare', 105, '✨'), ('Tundra Turtle', 'Rare', 112, '✨'), ('Meteor Turtle', 'Epic', 314, '✨'), ('Circuit Turtle', 'Epic', 321, '✨'), ('Marsh Turtle', 'Epic', 328, '✨'), ('Crown Turtle', 'Legendary', 1175, '✨'), ('Fossil Turtle', 'Legendary', 1182, '✨'), ('Kite Turtle', 'Legendary', 1189, '✨'), ('Crystal Turtle', 'Mythic', 5096, '✨'), ('Ink Turtle', 'Mythic', 5103, '✨'), ('Bubble Turtle', 'Mythic', 5110, '✨'), ('Comet Jelly', 'Common', 25, '✨'), ('Bramble Jelly', 'Common', 32, '✨'), ('Clockwork Jelly', 'Common', 39, '✨'), ('Coral Jelly', 'Rare', 101, '✨'), ('Lantern Jelly', 'Rare', 108, '✨'), ('Tundra Jelly', 'Rare', 115, '✨'), ('Meteor Jelly', 'Epic', 317, '✨'), ('Circuit Jelly', 'Epic', 324, '✨'), ('Marsh Jelly', 'Epic', 331, '✨'), ('Crown Jelly', 'Legendary', 1178, '✨'), ('Fossil Jelly', 'Legendary', 1185, '✨'), ('Kite Jelly', 'Legendary', 1192, '✨'), ('Crystal Jelly', 'Mythic', 5099, '✨'), ('Ink Jelly', 'Mythic', 5106, '✨'), ('Bubble Jelly', 'Mythic', 5113, '✨'), ('Comet Bat', 'Common', 28, '✨'), ('Bramble Bat', 'Common', 35, '✨'), ('Clockwork Bat', 'Common', 42, '✨'), ('Coral Bat', 'Rare', 104, '✨'), ('Lantern Bat', 'Rare', 111, '✨'), ('Tundra Bat', 'Rare', 118, '✨'), ('Meteor Bat', 'Epic', 320, '✨'), ('Circuit Bat', 'Epic', 327, '✨'), ('Marsh Bat', 'Epic', 334, '✨'), ('Crown Bat', 'Legendary', 1181, '✨'), ('Fossil Bat', 'Legendary', 1188, '✨'), ('Kite Bat', 'Legendary', 1195, '✨'), ('Crystal Bat', 'Mythic', 5102, '✨'), ('Ink Bat', 'Mythic', 5109, '✨'), ('Bubble Bat', 'Mythic', 5116, '✨'), ('Comet Beetle', 'Common', 31, '✨'), ('Bramble Beetle', 'Common', 38, '✨'), ('Clockwork Beetle', 'Common', 45, '✨'), ('Coral Beetle', 'Rare', 107, '✨'), ('Lantern Beetle', 'Rare', 114, '✨'), ('Tundra Beetle', 'Rare', 121, '✨'), ('Meteor Beetle', 'Epic', 323, '✨'), ('Circuit Beetle', 'Epic', 330, '✨'), ('Marsh Beetle', 'Epic', 337, '✨'), ('Crown Beetle', 'Legendary', 1184, '✨'), ('Fossil Beetle', 'Legendary', 1191, '✨'), ('Kite Beetle', 'Legendary', 1198, '✨'), ('Crystal Beetle', 'Mythic', 5105, '✨'), ('Ink Beetle', 'Mythic', 5112, '✨'), ('Bubble Beetle', 'Mythic', 5119, '✨'), ('Comet Wisp', 'Common', 34, '✨'), ('Bramble Wisp', 'Common', 41, '✨'), ('Clockwork Wisp', 'Common', 48, '✨'), ('Coral Wisp', 'Rare', 110, '✨'), ('Lantern Wisp', 'Rare', 117, '✨'), ('Tundra Wisp', 'Rare', 124, '✨'), ('Meteor Wisp', 'Epic', 326, '✨'), ('Circuit Wisp', 'Epic', 333, '✨'), ('Marsh Wisp', 'Epic', 340, '✨'), ('Crown Wisp', 'Legendary', 1187, '✨'), ('Fossil Wisp', 'Legendary', 1194, '✨'), ('Kite Wisp', 'Legendary', 1201, '✨'), ('Crystal Wisp', 'Mythic', 5108, '✨'), ('Ink Wisp', 'Mythic', 5115, '✨'), ('Bubble Wisp', 'Mythic', 5122, '✨'), ('Comet Snail', 'Common', 37, '✨'), ('Bramble Snail', 'Common', 44, '✨'), ('Clockwork Snail', 'Common', 51, '✨'), ('Coral Snail', 'Rare', 113, '✨'), ('Lantern Snail', 'Rare', 120, '✨'), ('Tundra Snail', 'Rare', 127, '✨'), ('Meteor Snail', 'Epic', 329, '✨'), ('Circuit Snail', 'Epic', 336, '✨'), ('Marsh Snail', 'Epic', 343, '✨'), ('Crown Snail', 'Legendary', 1190, '✨'), ('Fossil Snail', 'Legendary', 1197, '✨'), ('Kite Snail', 'Legendary', 1204, '✨'), ('Crystal Snail', 'Mythic', 5111, '✨'), ('Ink Snail', 'Mythic', 5118, '✨'), ('Bubble Snail', 'Mythic', 5125, '✨'), ('Comet Shark', 'Common', 40, '✨'), ('Bramble Shark', 'Common', 47, '✨'), ('Clockwork Shark', 'Common', 54, '✨'), ('Coral Shark', 'Rare', 116, '✨'), ('Lantern Shark', 'Rare', 123, '✨'), ('Tundra Shark', 'Rare', 130, '✨'), ('Meteor Shark', 'Epic', 332, '✨'), ('Circuit Shark', 'Epic', 339, '✨'), ('Marsh Shark', 'Epic', 346, '✨'), ('Crown Shark', 'Legendary', 1193, '✨'), ('Fossil Shark', 'Legendary', 1200, '✨'), ('Kite Shark', 'Legendary', 1207, '✨'), ('Crystal Shark', 'Mythic', 5114, '✨'), ('Ink Shark', 'Mythic', 5121, '✨'), ('Bubble Shark', 'Mythic', 5128, '✨'), ('Comet Golem', 'Common', 43, '✨'), ('Bramble Golem', 'Common', 50, '✨'), ('Clockwork Golem', 'Common', 57, '✨'), ('Coral Golem', 'Rare', 119, '✨'), ('Lantern Golem', 'Rare', 126, '✨'), ('Tundra Golem', 'Rare', 133, '✨'), ('Meteor Golem', 'Epic', 335, '✨'), ('Circuit Golem', 'Epic', 342, '✨'), ('Marsh Golem', 'Epic', 349, '✨'), ('Crown Golem', 'Legendary', 1196, '✨'), ('Fossil Golem', 'Legendary', 1203, '✨'), ('Kite Golem', 'Legendary', 1210, '✨'), ('Crystal Golem', 'Mythic', 5117, '✨'), ('Ink Golem', 'Mythic', 5124, '✨'), ('Bubble Golem', 'Mythic', 5131, '✨'), ('Comet Dragon', 'Common', 46, '✨'), ('Bramble Dragon', 'Common', 53, '✨'), ('Clockwork Dragon', 'Common', 60, '✨'), ('Coral Dragon', 'Rare', 122, '✨'), ('Lantern Dragon', 'Rare', 129, '✨'), ('Tundra Dragon', 'Rare', 136, '✨'), ('Meteor Dragon', 'Epic', 338, '✨'), ('Circuit Dragon', 'Epic', 345, '✨'), ('Marsh Dragon', 'Epic', 352, '✨'), ('Crown Dragon', 'Legendary', 1199, '✨'), ('Fossil Dragon', 'Legendary', 1206, '✨'), ('Kite Dragon', 'Legendary', 1213, '✨'), ('Crystal Dragon', 'Mythic', 5120, '✨'), ('Ink Dragon', 'Mythic', 5127, '✨'), ('Bubble Dragon', 'Mythic', 5134, '✨'), ('Comet Mushroom', 'Common', 49, '✨'), ('Bramble Mushroom', 'Common', 56, '✨'), ('Clockwork Mushroom', 'Common', 63, '✨'), ('Coral Mushroom', 'Rare', 125, '✨'), ('Lantern Mushroom', 'Rare', 132, '✨'), ('Tundra Mushroom', 'Rare', 139, '✨'), ('Meteor Mushroom', 'Epic', 341, '✨'), ('Circuit Mushroom', 'Epic', 348, '✨'), ('Marsh Mushroom', 'Epic', 355, '✨'), ('Crown Mushroom', 'Legendary', 1202, '✨'), ('Fossil Mushroom', 'Legendary', 1209, '✨'), ('Kite Mushroom', 'Legendary', 1216, '✨'), ('Crystal Mushroom', 'Mythic', 5123, '✨'), ('Ink Mushroom', 'Mythic', 5130, '✨'), ('Bubble Mushroom', 'Mythic', 5137, '✨'), ('Comet Spider', 'Common', 52, '✨'), ('Bramble Spider', 'Common', 59, '✨'), ('Clockwork Spider', 'Common', 66, '✨'), ('Coral Spider', 'Rare', 128, '✨'), ('Lantern Spider', 'Rare', 135, '✨'), ('Tundra Spider', 'Rare', 142, '✨'), ('Meteor Spider', 'Epic', 344, '✨'), ('Circuit Spider', 'Epic', 351, '✨'), ('Marsh Spider', 'Epic', 358, '✨'), ('Crown Spider', 'Legendary', 1205, '✨'), ('Fossil Spider', 'Legendary', 1212, '✨'), ('Kite Spider', 'Legendary', 1219, '✨'), ('Crystal Spider', 'Mythic', 5126, '✨'), ('Ink Spider', 'Mythic', 5133, '✨'), ('Bubble Spider', 'Mythic', 5140, '✨'), ('Comet Rabbit', 'Common', 55, '✨'), ('Bramble Rabbit', 'Common', 62, '✨'), ('Clockwork Rabbit', 'Common', 69, '✨'), ('Coral Rabbit', 'Rare', 131, '✨'), ('Lantern Rabbit', 'Rare', 138, '✨'), ('Tundra Rabbit', 'Rare', 145, '✨'), ('Meteor Rabbit', 'Epic', 347, '✨'), ('Circuit Rabbit', 'Epic', 354, '✨'), ('Marsh Rabbit', 'Epic', 361, '✨'), ('Crown Rabbit', 'Legendary', 1208, '✨'), ('Fossil Rabbit', 'Legendary', 1215, '✨'), ('Kite Rabbit', 'Legendary', 1222, '✨'), ('Crystal Rabbit', 'Mythic', 5129, '✨'), ('Ink Rabbit', 'Mythic', 5136, '✨'), ('Bubble Rabbit', 'Mythic', 5143, '✨'), ('Comet Cactus', 'Common', 58, '✨'), ('Bramble Cactus', 'Common', 65, '✨'), ('Clockwork Cactus', 'Common', 72, '✨'), ('Coral Cactus', 'Rare', 134, '✨'), ('Lantern Cactus', 'Rare', 141, '✨'), ('Tundra Cactus', 'Rare', 148, '✨'), ('Meteor Cactus', 'Epic', 350, '✨'), ('Circuit Cactus', 'Epic', 357, '✨'), ('Marsh Cactus', 'Epic', 364, '✨'), ('Crown Cactus', 'Legendary', 1211, '✨'), ('Fossil Cactus', 'Legendary', 1218, '✨'), ('Kite Cactus', 'Legendary', 1225, '✨'), ('Crystal Cactus', 'Mythic', 5132, '✨'), ('Ink Cactus', 'Mythic', 5139, '✨'), ('Bubble Cactus', 'Mythic', 5146, '✨'), ('Comet Robot', 'Common', 61, '✨'), ('Bramble Robot', 'Common', 68, '✨'), ('Clockwork Robot', 'Common', 75, '✨'), ('Coral Robot', 'Rare', 137, '✨'), ('Lantern Robot', 'Rare', 144, '✨'), ('Tundra Robot', 'Rare', 151, '✨'), ('Meteor Robot', 'Epic', 353, '✨'), ('Circuit Robot', 'Epic', 360, '✨'), ('Marsh Robot', 'Epic', 367, '✨'), ('Crown Robot', 'Legendary', 1214, '✨'), ('Fossil Robot', 'Legendary', 1221, '✨'), ('Kite Robot', 'Legendary', 1228, '✨'), ('Crystal Robot', 'Mythic', 5135, '✨'), ('Ink Robot', 'Mythic', 5142, '✨'), ('Bubble Robot', 'Mythic', 5149, '✨'), ('Comet Squid', 'Common', 64, '✨'), ('Bramble Squid', 'Common', 71, '✨'), ('Clockwork Squid', 'Common', 78, '✨'), ('Coral Squid', 'Rare', 140, '✨'), ('Lantern Squid', 'Rare', 147, '✨'), ('Tundra Squid', 'Rare', 154, '✨'), ('Meteor Squid', 'Epic', 356, '✨'), ('Circuit Squid', 'Epic', 363, '✨'), ('Marsh Squid', 'Epic', 370, '✨'), ('Crown Squid', 'Legendary', 1217, '✨'), ('Fossil Squid', 'Legendary', 1224, '✨'), ('Kite Squid', 'Legendary', 1231, '✨'), ('Crystal Squid', 'Mythic', 5138, '✨'), ('Ink Squid', 'Mythic', 5145, '✨'), ('Bubble Squid', 'Mythic', 5152, '✨'), ('Comet Penguin', 'Common', 67, '✨'), ('Bramble Penguin', 'Common', 74, '✨'), ('Clockwork Penguin', 'Common', 81, '✨'), ('Coral Penguin', 'Rare', 143, '✨'), ('Lantern Penguin', 'Rare', 150, '✨'), ('Tundra Penguin', 'Rare', 157, '✨'), ('Meteor Penguin', 'Epic', 359, '✨'), ('Circuit Penguin', 'Epic', 366, '✨'), ('Marsh Penguin', 'Epic', 373, '✨'), ('Crown Penguin', 'Legendary', 1220, '✨'), ('Fossil Penguin', 'Legendary', 1227, '✨'), ('Kite Penguin', 'Legendary', 1234, '✨'), ('Crystal Penguin', 'Mythic', 5141, '✨'), ('Ink Penguin', 'Mythic', 5148, '✨'), ('Bubble Penguin', 'Mythic', 5155, '✨')]
LOOKUP={s[0]:s for s in SPECIES}
EGGS={'Basic':{'cost':100,'weights':{'Common':60,'Rare':25,'Epic':10,'Legendary':4,'Mythic':1}},'Cyber':{'cost':1200,'weights':{'Rare':55,'Epic':30,'Legendary':13,'Mythic':2}},'Galaxy':{'cost':9000,'weights':{'Epic':40,'Legendary':40,'Mythic':20}}}

def auth(fn):
 @wraps(fn)
 def wrapped(*a,**kw):
  if not session.get('uid'): return jsonify(error='Log in first'),401
  return fn(*a,**kw)
 return wrapped

def current():return db.session.get(User,session['uid'])
def power(u):return sum(sorted((LOOKUP[o.species][2] for o in u.creatures),reverse=True)[:3])
def snapshot(u):
 owned=[{'id':o.id,'name':o.species,'rarity':LOOKUP[o.species][1],'power':LOOKUP[o.species][2],'emoji':LOOKUP[o.species][3]} for o in u.creatures]
 owned.sort(key=lambda x:-x['power'])
 return {'username':u.username,'coins':u.coins,'power':power(u),'owned':owned,'squad':owned[:3],'discovered':list({o.species for o in u.creatures}),'last_daily':u.last_daily,'streak':u.streak,'tag':u.tag}

def safe_int(v,default=0):
 try:return int(v)
 except:return default

@app.get('/')
def home():return render_template('index.html')
@app.get('/api/catalog')
def catalog():return jsonify(species=[{'name':n,'rarity':r,'power':p,'emoji':e} for n,r,p,e in SPECIES if r!='Secret'],eggs=EGGS)
@app.post('/api/register')
def register():
 d=request.get_json(silent=True) or {}; name=str(d.get('username','')).strip(); pwd=str(d.get('password',''))
 if not (3<=len(name)<=24 and name.replace('_','').isalnum() and 8<=len(pwd)<=128):return jsonify(error='Username: 3–24 letters/numbers/underscores. Password: 8+ characters.'),400
 if User.query.filter(func.lower(User.username)==name.lower()).first():return jsonify(error='Username already taken'),409
 u=User(username=name,password=generate_password_hash(pwd),coins=250)
 db.session.add(u);db.session.commit();session.clear();session['uid']=u.id
 return jsonify(state=snapshot(u))
@app.post('/api/login')
def login():
 d=request.get_json(silent=True) or {};u=User.query.filter(func.lower(User.username)==str(d.get('username','')).lower()).first()
 if not u or not check_password_hash(u.password,str(d.get('password',''))):return jsonify(error='Invalid login'),401
 session.clear();session['uid']=u.id;return jsonify(state=snapshot(u))
@app.post('/api/logout')
def logout():session.clear();return jsonify(ok=True)
@app.get('/api/me')
@auth
def me():return jsonify(state=snapshot(current()))
@app.post('/api/click')
@auth
def click_coin():
 u=current();now=time.time()
 if now-u.last_click<0.18:return jsonify(error='Too fast!'),429
 u.last_click=now;u.coins+=10;db.session.commit();return jsonify(state=snapshot(u),earned=10)
@app.post('/api/hatch')
@auth
def hatch():
 d=request.get_json(silent=True) or {};tier=d.get('tier')
 if tier not in EGGS:return jsonify(error='Unknown egg'),400
 u=current();cost=EGGS[tier]['cost']
 if u.coins<cost:return jsonify(error='Not enough coins'),400
 u.coins-=cost;weights=EGGS[tier]['weights'];rarity=random.choices(list(weights),weights=list(weights.values()))[0]
 name=random.choice([s[0] for s in SPECIES if s[1]==rarity]);db.session.add(Owned(user_id=u.id,species=name));db.session.commit()
 return jsonify(state=snapshot(u),hatch={'name':name,'rarity':rarity,'power':LOOKUP[name][2],'emoji':LOOKUP[name][3]})
@app.post('/api/fuse')
@auth
def fuse():
 name=str((request.get_json(silent=True) or {}).get('name',''))
 if name not in LOOKUP or LOOKUP[name][1] not in ('Common','Rare'):return jsonify(error='Only Common and Rare creatures can fuse'),400
 u=current();matches=Owned.query.filter_by(user_id=u.id,species=name).order_by(Owned.id).limit(3).all()
 if len(matches)<3:return jsonify(error='You need three duplicates'),400
 next_rarity='Rare' if LOOKUP[name][1]=='Common' else 'Epic'
 new=random.choice([s[0] for s in SPECIES if s[1]==next_rarity])
 for o in matches:db.session.delete(o)
 db.session.add(Owned(user_id=u.id,species=new));db.session.commit()
 return jsonify(state=snapshot(u),hatch={'name':new,'rarity':next_rarity,'power':LOOKUP[new][2],'emoji':LOOKUP[new][3]})
@app.post('/api/daily')
@auth
def daily():
 u=current();now=time.time()
 if now-u.last_daily<86400:return jsonify(error='Daily reward not ready'),400
 u.streak=u.streak+1 if now-u.last_daily<172800 else 1
 reward=500+min(u.streak,30)*100;u.coins+=reward;u.last_daily=now;db.session.commit()
 return jsonify(state=snapshot(u),earned=reward)
@app.post('/api/challenge')
@auth
def challenge():
 d=request.get_json(silent=True) or {};answer=str(d.get('answer','')).strip();token=str(d.get('token',''))
 from itsdangerous import URLSafeTimedSerializer,BadSignature,SignatureExpired
 serializer=URLSafeTimedSerializer(app.secret_key,salt='challenge')
 try:payload=serializer.loads(token,max_age=12)
 except (BadSignature,SignatureExpired):return jsonify(error='Challenge expired'),400
 u=current();now=time.time()
 if payload.get('uid')!=u.id or now-u.last_challenge<3:return jsonify(error='Wait before playing again'),429
 if answer!=str(payload['answer']):return jsonify(error='Not quite! Try another'),400
 u.last_challenge=now;u.coins+=90;db.session.commit();return jsonify(state=snapshot(u),earned=90)
@app.get('/api/challenge')
@auth
def new_challenge():
 from itsdangerous import URLSafeTimedSerializer
 a=random.randint(2,19);b=random.randint(2,19)
 token=URLSafeTimedSerializer(app.secret_key,salt='challenge').dumps({'uid':session['uid'],'answer':a+b})
 return jsonify(question=f'{a} + {b} = ?',token=token)
@app.post('/api/redeem')
@auth
def redeem():
 code=str((request.get_json(silent=True) or {}).get('code','')).strip().upper();u=current();c=db.session.get(Code,code)
 if not c:return jsonify(error='Invalid code'),400
 if Redemption.query.filter_by(user_id=u.id,code=code).first():return jsonify(error='Already redeemed'),400
 if c.max_uses and c.uses>=c.max_uses:return jsonify(error='Code exhausted'),400
 if c.reward=='coins':u.coins+=safe_int(c.value)
 elif c.reward=='creature' and c.value in LOOKUP:db.session.add(Owned(user_id=u.id,species=c.value))
 elif c.reward=='tag':u.tag=c.value[:20]
 else:return jsonify(error='Code configuration invalid'),400
 db.session.add(Redemption(user_id=u.id,code=code));c.uses+=1;db.session.commit();return jsonify(state=snapshot(u),reward=c.reward)
@app.get('/api/leaderboard')
def leaderboard():
 users=User.query.all();users.sort(key=lambda u:(-power(u),u.id))
 return jsonify(players=[{'username':u.username,'power':power(u),'tag':u.tag} for u in users[:10]])
@app.get('/health')
def health():return jsonify(ok=True)
with app.app_context():
 db.create_all()
 if not db.session.get(Code,'WELCOME'):
  db.session.add(Code(code='WELCOME',reward='coins',value='1000'))
  db.session.commit()
if __name__=='__main__':app.run(debug=os.environ.get('FLASK_DEBUG')=='1')
