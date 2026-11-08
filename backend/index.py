import os, json, sqlite3, hashlib, secrets
from flask import Flask, request, jsonify, send_from_directory, send_file

BASE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(BASE, "..", "frontend")
DB = os.path.join(BASE, "centinela.db")
INSTANCE = os.environ.get("CENTINELA_INSTANCE_ID", "doctor-marcos-001")

app = Flask(__name__)

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS medicos(id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, especialidad TEXT, correo TEXT UNIQUE, password_hash TEXT, salt TEXT);
    CREATE TABLE IF NOT EXISTS pacientes(id INTEGER PRIMARY KEY AUTOINCREMENT, medico_id INTEGER, nombre TEXT, edad INTEGER, ciudad TEXT, alergias TEXT, antecedentes TEXT);
    CREATE TABLE IF NOT EXISTS chequeos(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, sintomas TEXT, temperatura REAL, spo2 REAL, urgencia TEXT, probabilidades TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS recetas(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, medicamento TEXT, dosis TEXT, frecuencia TEXT, duracion TEXT, cantidad TEXT, indicaciones TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS citas(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, fecha TEXT, hora TEXT, motivo TEXT, tipo TEXT);
    CREATE TABLE IF NOT EXISTS examenes(id INTEGER PRIMARY KEY AUTOINCREMENT, paciente_id INTEGER, tipo TEXT, nombre_archivo TEXT, interpretacion TEXT, estado TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
    """)
    con.commit(); con.close()

init_db()

def hash_pw(pw, salt):
    return hashlib.sha256((salt+pw).encode()).hexdigest()

@app.route("/")
def index():
    # Sirve SIEMPRE el frontend/index.html completo, no la pantalla vieja
    p = os.path.join(FRONTEND, "index.html")
    if os.path.exists(p):
        return send_file(p)
    return "Falta frontend/index.html", 404

@app.route("/api/health")
def health():
    return jsonify({"ok": True, "instance": INSTANCE, "status": "Conectado"})

@app.route("/api/auth/register", methods=["POST"])
def register():
    d = request.get_json(force=True)
    nombre=d.get("nombre","").strip(); correo=d.get("correo","").strip().lower(); pw=d.get("password","")
    if not nombre or not correo or len(pw)<8:
        return jsonify({"ok":False,"error":"Completa nombre, correo y contraseña de 8+ caracteres"}),400
    import re
    if not re.search(r"[A-Z]",pw) or not re.search(r"[a-z]",pw) or not re.search(r"[0-9]",pw) or not re.search(r"[^A-Za-z0-9]",pw):
        return jsonify({"ok":False,"error":"Contraseña debe tener mayúscula, minúscula, número y símbolo"}),400
    salt=secrets.token_hex(8); h=hash_pw(pw,salt)
    con=db()
    try:
        cur=con.execute("INSERT INTO medicos(nombre,especialidad,correo,password_hash,salt) VALUES(?,?,?,?,?)",(nombre,d.get("especialidad",""),correo,h,salt))
        con.commit(); mid=cur.lastrowid
    except sqlite3.IntegrityError:
        con.close(); return jsonify({"ok":False,"error":"Ese correo ya tiene cuenta. Inicia sesión."}),400
    con.close()
    return jsonify({"ok":True,"medico":{"id":mid,"nombre":nombre,"especialidad":d.get("especialidad",""),"correo":correo}})

@app.route("/api/auth/login", methods=["POST"])
def login():
    d=request.get_json(force=True); correo=d.get("correo","").strip().lower(); pw=d.get("password","")
    con=db(); row=con.execute("SELECT * FROM medicos WHERE correo=?",(correo,)).fetchone(); con.close()
    if not row or hash_pw(pw,row["salt"])!=row["password_hash"]:
        return jsonify({"ok":False,"error":"Correo o contraseña incorrectos"}),401
    return jsonify({"ok":True,"medico":{"id":row["id"],"nombre":row["nombre"],"especialidad":row["especialidad"],"correo":row["correo"]}})

@app.route("/api/pacientes", methods=["GET","POST"])
def pacientes():
    con=db()
    if request.method=="POST":
        d=request.get_json(force=True)
        cur=con.execute("INSERT INTO pacientes(medico_id,nombre,edad,ciudad,alergias,antecedentes) VALUES(?,?,?,?,?,?)",(d.get("medico_id"),d.get("nombre"),d.get("edad"),d.get("ciudad",""),d.get("alergias",""),d.get("antecedentes","")))
        con.commit(); pid=cur.lastrowid; con.close(); return jsonify({"ok":True,"id":pid})
    medico_id=request.args.get("medico_id")
    rows=con.execute("SELECT * FROM pacientes WHERE medico_id=? ORDER BY id DESC",(medico_id,)).fetchall(); con.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/pacientes/<int:pid>/chequeos", methods=["POST"])
def chequeo(pid):
    d=request.get_json(force=True); sintomas=d.get("sintomas",[]); spo2=float(d.get("spo2") or 100)
    if "Dificultad respirar" in sintomas or spo2<93:
        urg="ROJA"; probs=[{"label":"Requiere evaluación urgente presencial","p":72},{"label":"Infección respiratoria","p":18},{"label":"Otra causa","p":10}]
    elif "Fiebre" in sintomas and "Tos" in sintomas:
        urg="AMARILLA"; probs=[{"label":"Gripe / resfriado viral (probable)","p":62},{"label":"Faringitis","p":24},{"label":"Evaluación presencial","p":14}]
    elif "Fiebre" in sintomas and "Erupción piel" in sintomas:
        urg="AMARILLA"; probs=[{"label":"Exantema viral (probable)","p":48},{"label":"Reacción alérgica","p":30},{"label":"Dengue - requiere examen","p":22}]
    elif "Dolor abdominal" in sintomas:
        urg="AMARILLA"; probs=[{"label":"Gastroenteritis (probable)","p":58},{"label":"Infección alimentaria","p":26},{"label":"Evaluación presencial","p":16}]
    else:
        urg="VERDE"; probs=[{"label":"Evaluación presencial recomendada","p":55},{"label":"Causa viral leve","p":30},{"label":"Otra causa","p":15}]
    con=db(); con.execute("INSERT INTO chequeos(paciente_id,sintomas,temperatura,spo2,urgencia,probabilidades) VALUES(?,?,?,?,?,?)",(pid,json.dumps(sintomas),d.get("temperatura"),d.get("spo2"),urg,json.dumps(probs))); con.commit(); con.close()
    return jsonify({"ok":True,"urgencia":urg,"probabilidades":probs})

@app.route("/api/pacientes/<int:pid>/recetas", methods=["POST"])
def receta(pid):
    d=request.get_json(force=True); con=db(); con.execute("INSERT INTO recetas(paciente_id,medicamento,dosis,frecuencia,duracion,cantidad,indicaciones) VALUES(?,?,?,?,?,?,?)",(pid,d.get("medicamento"),d.get("dosis"),d.get("frecuencia"),d.get("duracion"),d.get("cantidad"),d.get("indicaciones"))); con.commit(); con.close(); return jsonify({"ok":True})

@app.route("/api/pacientes/<int:pid>/citas", methods=["POST"])
def cita(pid):
    d=request.get_json(force=True); con=db(); con.execute("INSERT INTO citas(paciente_id,fecha,hora,motivo,tipo) VALUES(?,?,?,?,?)",(pid,d.get("fecha"),d.get("hora"),d.get("motivo"),d.get("tipo"))); con.commit(); con.close(); return jsonify({"ok":True})

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    print(f"Running on http://127.0.0.1:{port}")
    print(f"Available at your primary URL https://centinela-medico.onrender.com")
    print("Your service is live")
    app.run(host="0.0.0.0", port=port)
