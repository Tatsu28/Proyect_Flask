import os
import sqlite3
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, session, g, flash
)

app = Flask(__name__)
app.secret_key = "admin1234"

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE BASE DE DATOS
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "bdprueba.db")


def get_connection():
    """Devuelve una conexión a SQLite con row_factory para diccionarios."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  
    return conn


def init_db():
    """Crea tablas y datos iniciales si aún no existen."""
    conn = get_connection()
    cur = conn.cursor()

    # Tabla de usuarios
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        """
    )

    # Tabla de tipos de cartera
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tipocartera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        );
        """
    )

    # Tabla de carteras
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cartera (
            CODCAR INTEGER PRIMARY KEY AUTOINCREMENT,
            DESCRIPCAR TEXT NOT NULL,
            PRECIOCAR REAL NOT NULL,
            FECHACAR TEXT NOT NULL,
            CODTIPCAR INTEGER NOT NULL,
            FOREIGN KEY (CODTIPCAR) REFERENCES tipocartera(id)
        );
        """
    )

    # Poblar tipocartera si está vacía
    cur.execute("SELECT COUNT(*) FROM tipocartera")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO tipocartera (nombre) VALUES (?)",
            [("Andino",), ("Tradicional",), ("Selvático",), ("Costeño",)],
        )

    # Crear usuario demo si no existe
    cur.execute("SELECT COUNT(*) FROM usuario")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO usuario (username, password) VALUES (?, ?)",
            ("joselyn", "1234"),
        )

    conn.commit()
    conn.close()


# Ejecutar una sola vez al arrancar
init_db()

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------


def query_db(query: str, args: tuple = (), one: bool = False):
    """Ejecuta SELECT y devuelve lista de dicts o un único dict."""
    conn = get_connection()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query: str, args: tuple = ()):  # Para INSERT / UPDATE / DELETE
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    cur.close()
    conn.close()


# ---------------------------------------------------------------------------
# RUTAS DE AUTENTICACIÓN
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        user = query_db(
            "SELECT * FROM usuario WHERE username = ? AND password = ?",
            (username, password),
            one=True,
        )
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("principal"))
        flash("Usuario o clave incorrectos", "danger")
    return render_template("Login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# RUTA PRINCIPAL (MENÚ)
# ---------------------------------------------------------------------------


@app.route("/principal")
def principal():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("Principal.html")


# ---------------------------------------------------------------------------
# REGISTRO DE CARTERA
# ---------------------------------------------------------------------------


@app.route("/RegistrarCartera")
def RegistrarCartera():
    if "user_id" not in session:
        return redirect(url_for("login"))
    tipos = query_db("SELECT * FROM tipocartera")
    return render_template("RegistrarCartera.html", tipos=tipos)


@app.route("/GrabarCartera", methods=["POST"])
def GrabarCartera():
    if "user_id" not in session:
        return redirect(url_for("login"))

    descricar = request.form["descripcion"].strip()
    precio = float(request.form["precio"])
    fechacar = request.form["fecha"]
    codtipcar = int(request.form["tipo"])

    execute_db(
        "INSERT INTO cartera (DESCRIPCAR, PRECIOCAR, FECHACAR, CODTIPCAR) VALUES (?, ?, ?, ?)",
        (descricar, precio, fechacar, codtipcar),
    )

    tipos = query_db("SELECT * FROM tipocartera")
    mensaje = "Se grabó el registro satisfactoriamente"
    return render_template("RegistrarCartera.html", tipos=tipos, mensaje=mensaje)


# ---------------------------------------------------------------------------
# CONSULTA DE CARTERA
# ---------------------------------------------------------------------------


@app.route("/ConsultarCartera")
def ConsultarCartera():
    if "user_id" not in session:
        return redirect(url_for("login"))
    tipos = query_db("SELECT * FROM tipocartera")
    return render_template("ConsultarCartera.html", tipos=tipos)


@app.route("/BuscarCartera", methods=["POST"])
def BuscarCartera():
    if "user_id" not in session:
        return redirect(url_for("login"))

    codtipcar = int(request.form["tipo"])

    tipos = query_db("SELECT * FROM tipocartera")
    resultados = query_db(
        """
        SELECT c.DESCRIPCAR, c.CODCAR, c.FECHACAR, c.PRECIOCAR
        FROM cartera AS c
        WHERE c.CODTIPCAR = ?
        ORDER BY c.FECHACAR DESC
        """,
        (codtipcar,),
    )

    return render_template(
        "ConsultarCartera.html", tipos=tipos, resultados=resultados
    )


# ---------------------------------------------------------------------------
# EJECUCIÓN
# ---------------------------------------------------------------------------


if __name__ == '__main__':
    if not os.path.exists(app.config ['UPLOAD_FOLDER']):
        os.makedirs(app.config [ 'UPLOAD_FOLDER'])
    app.run(debug=True, host="0.0.0.0", port=os.getenv("PORT", default=5000))


# if __name__ == "__main__":
#    app.run(debug=True)




