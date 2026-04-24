from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3
import csv
import io
import os
from datetime import date

app = Flask(__name__)
app.secret_key = "clave_secreta"


# 🔥 CONEXIÓN SQLITE CORREGIDA PARA RENDER
def conectar():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "inventario.db")

    conexion = sqlite3.connect(db_path)
    conexion.row_factory = sqlite3.Row
    return conexion


# 🔥 CREAR TABLAS AUTOMÁTICO
def crear_bd():
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        precio REAL,
        stock INTEGER,
        categoria TEXT,
        fecha TEXT
    )
    """)

    # usuario por defecto
    cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (?, ?)", ("admin", "123"))

    conexion.commit()
    conexion.close()


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario=? AND password=?",
            (usuario, password)
        )

        user = cursor.fetchone()

        conexion.close()

        if user:
            session["usuario"] = usuario
            return redirect(url_for("inventario"))

        return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


@app.route("/inventario")
def inventario():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    conexion.close()

    return render_template("index.html", productos=productos)


@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        categoria = request.form["categoria"]
        fecha = date.today()

        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO productos (nombre, precio, stock, categoria, fecha) VALUES (?, ?, ?, ?, ?)",
            (nombre, precio, stock, categoria, fecha)
        )
        conexion.commit()
        conexion.close()

        return redirect(url_for("inventario"))

    return render_template("agregar.html")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor()

    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        categoria = request.form["categoria"]

        cursor.execute(
            "UPDATE productos SET nombre=?, precio=?, stock=?, categoria=? WHERE id=?",
            (nombre, precio, stock, categoria, id)
        )
        conexion.commit()
        conexion.close()

        return redirect(url_for("inventario"))

    cursor.execute("SELECT * FROM productos WHERE id=?", (id,))
    producto = cursor.fetchone()

    conexion.close()

    return render_template("editar.html", producto=producto)


@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM productos WHERE id=?", (id,))
    conexion.commit()
    conexion.close()

    return redirect(url_for("inventario"))


@app.route("/reporte", methods=["GET", "POST"])
def reporte():
    if "usuario" not in session:
        return redirect(url_for("login"))

    resultados = []
    desde = ""
    hasta = ""

    if request.method == "POST":
        desde = request.form["desde"]
        hasta = request.form["hasta"]

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT * FROM productos
            WHERE date(fecha) BETWEEN ? AND ?
            ORDER BY fecha DESC
            """,
            (desde, hasta)
        )

        resultados = cursor.fetchall()
        conexion.close()

    return render_template("reporte.html", resultados=resultados, desde=desde, hasta=hasta)


@app.route("/exportar_csv")
def exportar_csv():
    if "usuario" not in session:
        return redirect(url_for("login"))

    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        """
        SELECT * FROM productos
        WHERE date(fecha) BETWEEN ? AND ?
        ORDER BY fecha DESC
        """,
        (desde, hasta)
    )

    productos = cursor.fetchall()
    conexion.close()

    salida = io.StringIO()
    writer = csv.writer(salida)

    writer.writerow(["ID", "Nombre", "Precio", "Stock", "Categoria", "Fecha"])

    for p in productos:
        writer.writerow([
            p["id"],
            p["nombre"],
            p["precio"],
            p["stock"],
            p["categoria"],
            p["fecha"]
        ])

    respuesta = Response(salida.getvalue(), mimetype="text/csv")
    respuesta.headers["Content-Disposition"] = "attachment; filename=reporte_productos.csv"

    return respuesta


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    crear_bd()  # 🔥 crea todo automático
    app.run(debug=True)