import os, sqlite3, json, re, secrets
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
INSTANCE_ID = os.environ.get("CENTINELA_INSTANCE_ID","doctor-marcos-001")
DB_PATH = os.path.join(os.path.dirname(__file__),"centinela.db")
FRONTEND = os.path.join(os.path.dirname(__file__),"..","frontend")
app = Flask(__name__, static_folder=FRONTEND)
def db():
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row; return con
def init_db():
    con=db(); con.executescript(open(os.path.join(os.path.dirname(__file__),"schema.sql")).read()); con.commit(); con.close()
@app.route("/")
def index(): return send_from_directory(FRONTEND,"index.html")
@app.route("/api/health")
def health(): return jsonify({"ok":True,"instance":INSTANCE_ID,"app":"CENTINELA MÉDICO"})
@app.route("/api/auth/register", methods=["POST"])
def register():
    d=request.json or {}; pw=d.get("password","")
    if len(pw)<8 or not re.search(r"[A-Z]",pw) or not re.search(r"[a-z]",pw) or not re.search(r"[0-9]",pw) or not re.search(r"[^A-Za-z0-9]",pw):
        return jsonify({"error":"Contraseña debe tener 8+, mayúscula, minúscula, número y símbolo"}),400
    con=db()
    try:
        con.execute("INSERT INTO medicos(nombre,especialidad,correo,password_hash,instance_id,created_at) VALUES(?,?,?,?,?,?)",(d.get("nombre"),d.get("especialidad"),d.get("correo"),generate_password_hash(pw),INSTANCE_ID,datetime.now().isoformat())); con.commit()
    except sqlite3.IntegrityError: return jsonify({"error":"Correo ya existe"}),400
    finally: con.close()
    return jsonify({"ok":True})
@app.route("/api/auth/login", methods=["POST"])
def login():
    d=request.json or {}; con=db(); row=con.execute("SELECT * FROM medicos WHERE correo=? AND instance_id=?",(d.get("correo"),INSTANCE_ID)).fetchone(); con.close()
    if not row or not check_password_hash(row["password_hash"], d.get("password","")): return jsonify({"error":"Correo o contraseña incorrecta"}),401
    return jsonify({"ok":True,"medico":{"id":row["id"],"nombre":row["nombre"],"especialidad":row["especialidad"],"correo":row["correo"]}})
@app.route("/api/pacientes", methods=["GET","POST"])
def pacientes():
    con=db()
    if request.method=="POST":
        d=request.json or {}; cur=con.execute("INSERT INTO pacientes(medico_id,nombre,edad,sexo,ciudad,telefono,alergias,medicamentos,antecedentes,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(d.get("medico_id"),d.get("nombre"),d.get("edad"),d.get("sexo"),d.get("ciudad"),d.get("telefono"),d.get("alergias"),d.get("medicamentos"),d.get("antecedentes"),datetime.now().isoformat())); con.commit(); pid=cur.lastrowid; con.close(); return jsonify({"ok":True,"id":pid})
    medico_id=request.args.get("medico_id"); rows=con.execute("SELECT * FROM pacientes WHERE medico_id=? ORDER BY created_at DESC",(medico_id,)).fetchall(); con.close(); return jsonify([dict(r) for r in rows])
@app.route("/api/pacientes/<int:pid>/chequeos", methods=["GET","POST"])
def chequeos(pid):
    con=db()
    if request.method=="POST":
        d=request.json or {}; sintomas=d.get("sintomas",[]); spo2=d.get("spo2") or 100; urgencia="VERDE"; probs=[]
        if "Dificultad respirar" in sintomas or (isinstance(spo2,(int,float)) and spo2<93):
            urgencia="ROJA"; probs=[{"label":"Requiere evaluación urgente presencial","p":72},{"label":"Infección respiratoria","p":18},{"label":"Otra causa","p":10}]
        elif "Fiebre" in sintomas and "Tos" in sintomas:
            urgencia="AMARILLA"; probs=[{"label":"Gripe / resfriado viral (probable)","p":62},{"label":"Faringitis","p":24},{"label":"Evaluación presencial","p":14}]
        elif "Fiebre" in sintomas and "Erupción piel" in sintomas:
            urgencia="AMARILLA"; probs=[{"label":"Exantema viral (probable)","p":48},{"label":"Reacción alérgica","p":30},{"label":"Dengue - requiere examen","p":22}]
        elif "Dolor abdominal" in sintomas:
            urgencia="AMARILLA"; probs=[{"label":"Gastroenteritis (probable)","p":58},{"label":"Infección alimentaria","p":26},{"label":"Evaluación presencial","p":16}]
        else: probs=[{"label":"Evaluación presencial recomendada","p":55},{"label":"Causa viral leve","p":30},{"label":"Otra causa","p":15}]
        con.execute("INSERT INTO chequeos(paciente_id,sintomas,temperatura,spo2,urgencia,probabilidades,created_at) VALUES(?,?,?,?,?,?,?)",(pid,json.dumps(sintomas,ensure_ascii=False),d.get("temperatura"),spo2,urgencia,json.dumps(probs,ensure_ascii=False),datetime.now().isoformat())); con.commit(); con.close(); return jsonify({"ok":True,"urgencia":urgencia,"probabilidades":probs})
    rows=con.execute("SELECT * FROM chequeos WHERE paciente_id=? ORDER BY created_at DESC",(pid,)).fetchall(); con.close(); return jsonify([dict(r) for r in rows])
@app.route("/api/pacientes/<int:pid>/imagenes", methods=["GET","POST"])
def imagenes(pid):
    con=db()
    if request.method=="POST":
        d=request.json or {}; con.execute("INSERT INTO imagenes(paciente_id,tipo,nombre_archivo,interpretacion,estado,created_at) VALUES(?,?,?,?,?,?)",(pid,d.get("tipo"),d.get("nombre_archivo"),d.get("interpretacion",""),d.get("estado","Pendiente de revisión"),datetime.now().isoformat())); con.commit(); con.close(); return jsonify({"ok":True})
    rows=con.execute("SELECT * FROM imagenes WHERE paciente_id=? ORDER BY created_at DESC",(pid,)).fetchall(); con.close(); return jsonify([dict(r) for r in rows])
@app.route("/api/pacientes/<int:pid>/recetas", methods=["GET","POST"])
def recetas(pid):
    con=db()
    if request.method=="POST":
        d=request.json or {}; con.execute("INSERT INTO recetas(paciente_id,medicamento,dosis,frecuencia,duracion,cantidad,indicaciones,notas,entregada,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(pid,d.get("medicamento"),d.get("dosis"),d.get("frecuencia"),d.get("duracion"),d.get("cantidad"),d.get("indicaciones"),d.get("notas"),0,datetime.now().isoformat())); con.commit(); con.close(); return jsonify({"ok":True})
    rows=con.execute("SELECT * FROM recetas WHERE paciente_id=? ORDER BY created_at DESC",(pid,)).fetchall(); con.close(); return jsonify([dict(r) for r in rows])
@app.route("/api/pacientes/<int:pid>/citas", methods=["GET","POST"])
def citas(pid):
    con=db()
    if request.method=="POST":
        d=request.json or {}; con.execute("INSERT INTO citas(paciente_id,fecha,hora,motivo,tipo,notas,atendida,created_at) VALUES(?,?,?,?,?,?,?,?)",(pid,d.get("fecha"),d.get("hora"),d.get("motivo"),d.get("tipo"),d.get("notas"),0,datetime.now().isoformat())); con.commit(); con.close(); return jsonify({"ok":True})
    rows=con.execute("SELECT * FROM citas WHERE paciente_id=? ORDER BY fecha,hora",(pid,)).fetchall(); con.close(); return jsonify([dict(r) for r in rows])
if __name__=="__main__": init_db(); app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
