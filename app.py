from flask import Flask, render_template, request, redirect, url_for, session, Response
import mysql.connector
import csv
import io
from datetime import date

app = Flask(__name__)
app.secret_key = "clave_secreta"


def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="inventario_db"
    )


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario=%s AND password=%s",
            (usuario, password)
        )

        user = cursor.fetchone()

        cursor.close()
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
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    cursor.close()
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
            "INSERT INTO productos (nombre, precio, stock, categoria, fecha) VALUES (%s, %s, %s, %s, %s)",
            (nombre, precio, stock, categoria, fecha)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        return redirect(url_for("inventario"))

    return render_template("agregar.html")


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]
        categoria = request.form["categoria"]

        cursor.execute(
            "UPDATE productos SET nombre=%s, precio=%s, stock=%s, categoria=%s WHERE id=%s",
            (nombre, precio, stock, categoria, id)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        return redirect(url_for("inventario"))

    cursor.execute("SELECT * FROM productos WHERE id=%s", (id,))
    producto = cursor.fetchone()

    cursor.close()
    conexion.close()

    return render_template("editar.html", producto=producto)


@app.route("/eliminar/<int:id>")
def eliminar(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
    conexion.commit()
    cursor.close()
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
        cursor = conexion.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT * FROM productos
            WHERE DATE(fecha) BETWEEN %s AND %s
            ORDER BY fecha DESC
            """,
            (desde, hasta)
        )

        resultados = cursor.fetchall()

        cursor.close()
        conexion.close()

    return render_template("reporte.html", resultados=resultados, desde=desde, hasta=hasta)


@app.route("/exportar_csv")
def exportar_csv():
    if "usuario" not in session:
        return redirect(url_for("login"))

    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT * FROM productos
        WHERE DATE(fecha) BETWEEN %s AND %s
        ORDER BY fecha DESC
        """,
        (desde, hasta)
    )

    productos = cursor.fetchall()

    cursor.close()
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
    app.run(debug=True)