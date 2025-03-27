import os
import sys
import datetime
import requests
from flask import Flask, render_template, request, flash, redirect, url_for
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'  # Necesario para los mensajes flash

# ---------------------------
# Función para obtener la ruta de un recurso
# ---------------------------
def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, tanto en desarrollo como en ejecutable."""
    try:
        base_path = sys._MEIPASS  # cuando está empaquetado con PyInstaller
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------------------------
# Inicialización de Firebase Admin SDK
# ---------------------------
# Asegúrate de que el archivo de credenciales JSON se encuentre en static/assets/
cred = credentials.Certificate(resource_path("static/assets/escaneosqr-firebase-adminsdk-fbsvc-80cc9e5f82.json"))
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://escaneosqr-default-rtdb.firebaseio.com/"
})

# ---------------------------
# Función para verificar conexión a Internet
# ---------------------------
def check_internet(timeout=3):
    try:
        r = requests.head("https://www.google.com", timeout=timeout)
        return r.status_code == 200
    except:
        return False

# ---------------------------
# Función para obtener usuarios desde Firebase
# ---------------------------
def obtener_usuarios():
    try:
        usuarios = db.reference("usuarios").get()
        return usuarios, True
    except Exception as e:
        print("Error al obtener datos de Firebase:", e)
        return None, False

# ---------------------------
# Función para verificar si una persona es huésped
# ---------------------------
def verificar_huesped(dni):
    dni = dni.strip()
    if not dni or len(dni) != 8:
        return {"message": "Ingrese un DNI válido de 8 dígitos.", "status": "error"}
    
    usuarios, online = obtener_usuarios()
    if not online:
        return {"message": "No se pudo obtener datos en línea.", "status": "error"}
    
    if usuarios:
        for usuario in usuarios.values():
            if str(usuario.get("dni")) == dni:
                fecha_sal = usuario.get("fecha_sal")
                if fecha_sal:
                    fecha_sin_hora = fecha_sal.split()[0]
                    fecha_salida = datetime.datetime.strptime(fecha_sin_hora, "%Y-%m-%d").date()
                    fecha_actual = datetime.datetime.today().date()
                    if fecha_actual > fecha_salida:
                        return {"message": "Esta persona no es huésped.", "status": "error"}
                return {"message": "Esta persona es huésped.", "status": "success"}
    return {"message": "Esta persona no es huésped.", "status": "error"}

# ---------------------------
# Rutas de la aplicación Flask
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        dni = request.form.get("dni", "")
        resultado = verificar_huesped(dni)
        flash(resultado["message"], resultado["status"])
        return redirect(url_for("index"))
    return render_template("index.html", online=check_internet())


if __name__ == "__main__":
    app.run(debug=True)
