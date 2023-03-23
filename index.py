import os

#import logging

from distutils.util import execute
from mmap import PROT_WRITE

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,json
from flaskext.mysql import MySQL

# Change the format of messages logged to Stackdriver
#logging.basicConfig(format="%(message)s", level=logging.INFO)
#config = {
 #   "DEBUG": True,  # some Flask specific configs
  #  "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
   # "CACHE_DEFAULT_TIMEOUT": 300,
#}
userValidado = ""

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp'])

app = Flask(__name__)
#app.config.from_mapping(config)
#cache = Cache(app)

#app = Flask(static_folder=('/home/jorge/Escritorio/python-website/src/static/images'))
# Mysql Connection

app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = os.environ.get("ATPUCE_DBUSER")
app.config['MYSQL_DATABASE_PASSWORD'] = os.environ.get("ATPUCE_DBPASS")
app.config['MYSQL_DATABASE_DB'] = 'atpuce_com'
mysql = MySQL(app)
mysql.init_app(app)

# settings
app.secret_key = 'mysecretkey'


@app.route('/')
def home():
    return render_template('home.html')

#@app.route("/cache")
#@cache.cached(timeout=50)
#def cachedpage():
 #   return "Cached for 50 seconds"

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/sign_in')
def sign_in():
    return render_template('sign_in.html')


@app.route('/password')
def password():
    return render_template('password.html')


@app.route('/valida_inicio', methods=['POST'])
def valida_inicio():
    
    usuario = request.form['usuario']
    password = request.form['password']

    cur = mysql.get_db().cursor()
    cur.execute(
        "SELECT cl_clientes.cl_Nombres,cl_NumIdent,Cl_Estado FROM cl_clientes WHERE Cl_Estado='A' AND Cl_NumIdent='%s'" % usuario)
    data = cur.fetchall()
    check = False
    for d in data:
        check = True
    if check == False:
        flash('Usuario NO coincidentes o no esta en estado Activo')
        return redirect(url_for('sign_in'))
    else:
        cur = mysql.get_db().cursor()
        cur.execute("SELECT cl_clientes.cl_Nombres,cl_NumIdent,Cl_Estado FROM cl_clientes WHERE Cl_Estado='A' AND Cl_NumIdent='%s' AND Cl_PWD='%s'" % (
            usuario, password))

        data = cur.fetchall()
        check = False
        for d in data:
            check = True
        if check == False:
            flash('Password NO coincidente')
            return redirect(url_for('sign_in'))
        else:
            global userValidado
            userValidado = usuario
            return redirect(url_for('saldos'))
        
@app.route('/encera_input', methods=['POST'])
def encera_input():
    texto=request.form['password']

@app.route('/cambio_password', methods=['GET', 'POST'])
def cambio_password():

    usuario = request.form.get('usuario')
    password = (request.form.get('password'))
    nuevoPassword = (request.form.get('nuevoPassword'))
    nuevoPasswordRepita = (request.form.get('nuevoPasswordRepita'))


    cur = mysql.get_db().cursor()

    cur.execute(
        "SELECT cl_clientes.cl_Nombres,cl_NumIdent,Cl_Estado FROM cl_clientes WHERE Cl_Estado='A' AND Cl_NumIdent='%s'" % usuario)
    data = cur.fetchall()
    check = False
    for d in data:
        check = True
    if check == False:
        flash('Usuario NO coincidentes o no esta en estado Activo')
        return redirect(url_for('password'))

    cur.execute("SELECT cl_clientes.cl_Nombres,cl_NumIdent,Cl_Estado FROM cl_clientes WHERE Cl_Estado='A' AND Cl_NumIdent='%s' AND Cl_PWD='%s'" % (usuario, password))
    data = cur.fetchall()
    check = False
    for d in data:
        check = True
    if check == False:
        flash('Password NO coincidente_cambio_password')
        return redirect(url_for('password'))

    if nuevoPasswordRepita != nuevoPassword:
        flash('Nuevo Password no coincidente')
        return redirect(url_for('password'))

    # aqui poner el update del password, en la base clientes

    cur.execute("UPDATE cl_clientes SET Cl_PWD = '%s' WHERE Cl_NumIdent = '%s'" %
               (nuevoPasswordRepita, usuario))
    
    mysql.get_db().commit()
    

    return redirect(url_for('sign_in'))


@app.route('/saldos')
def saldos():

    cur = mysql.get_db().cursor()
    cur.execute("""
        SELECT 
        cl_clientes.Cl_NumIdent, cl_clientes.Cl_Nombres, cp_pp_productopasivo.Cp_Pp_Secuenci, cp_pp_productopasivo.Cp_PP_NombrePP, 
        cp_sl_saldo.Cp_Sl_Saldo,
        cp_sl_saldo.Cp_Sl_Fecha, cp_sl_saldo.Cp_Sl_Secuenci 
        FROM 
        cl_clientes 
        INNER JOIN cp_sl_saldo on cl_clientes.Cl_Secuenci=cp_sl_saldo.Cl_Secuenci 
        INNER JOIN cp_pp_productopasivo on cp_sl_saldo.Cp_Pp_Secuenci=cp_pp_productopasivo.Cp_Pp_Secuenci
                WHERE cl_clientes.cl_estado='A' 
        AND cl_clientes.cl_numident='% s'  """ % userValidado)

    dataCp = cur.fetchall()
    dataCo = prestamos()

    tCapital=0
    tInteres=0
    tTotal=0

    totalCapital = 0
    totalInteres=0
    total=0

    for d in dataCo:
        totalCapital = totalCapital + d[3]
        totalInteres = totalInteres + d[4]
        total=total + d[5]


    return render_template('saldos.html', captaciones=dataCp, colocaciones=dataCo, tCapital=totalCapital, tInteres=totalInteres, tTotal=total)

def prestamos(): 
    cur = mysql.get_db().cursor()
    cur.execute("""
        SELECT 
        co_pc_productocolocacion.co_pc_nombre, co_pr_prestamo.Co_Pr_Secuenci_cesan, co_pr_prestamo.Co_Pr_ValSoli, 
        co_pr_prestamo.Co_Pr_VSaldo, co_pr_prestamo.Co_Pr_InDeven, (co_pr_prestamo.Co_Pr_VSaldo+co_pr_prestamo.Co_Pr_InDeven)
        as SaldoTotal,
        concat(co_pr_prestamo.Co_Pr_NoCuotas, '/' ,round((co_pr_prestamo.Co_Pr_ValSoli - co_pr_prestamo.Co_Pr_VSaldo)/(co_pr_prestamo.Co_Pr_ValSoli /co_pr_prestamo.Co_Pr_NoCuotas),0))
        as Cuotas,
        co_pr_prestamo.Co_Pr_FechaAd, 
        concat(co_de_destino.Co_De_Descrip, ' ' , co_pr_prestamo.Co_Pr_Descrip) as Co_Pr_Descrip,
        co_pr_prestamo.Co_Pr_Secuenci
	    FROM
        cl_clientes
        INNER JOIN co_pr_prestamo on cl_clientes.Cl_Secuenci=co_pr_prestamo.Cl_Secuenci
        INNER JOIN co_de_destino on co_pr_prestamo.Co_De_Secuenci=co_de_destino.Co_De_Secuenci 
        INNER JOIN co_pc_productocolocacion on co_pr_prestamo.Co_Pc_Secuenci=co_pc_productocolocacion.Co_Pc_Secuenci
        WHERE cl_clientes.cl_estado='A' and co_pr_prestamo.co_pr_estado='A'
        AND cl_clientes.cl_numident='% s'  """ % userValidado)

    dataCo = cur.fetchall()
    return dataCo
    # return render_template('saldos.html', colocaciones=dataCo)

@app.route('/busca_prestamos')
def busca_prestamos(): 
    listaPrestamos=prestamos()
    return render_template('prestamos.html',colocaciones=listaPrestamos)

def prestamo_transaccion(secuenci):
    print(secuenci)
    cur = mysql.get_db().cursor()
    cur.execute(
        """ SELECT Co_Tr_Tipo,Co_Tr_CVigen,Co_Tr_IntNorma,Co_Tr_Efectivo+Co_Tr_Transfer as AbonoTotal,
        Co_Tr_Fecha,Co_Tr_Saldo,Co_Tr_InDeven
        FROM co_tr_transaccion WHERE Co_Pr_Secuenci='% s'
        ORDER BY co_Tr_fecha ASC  """ % secuenci);
    dataTr = cur.fetchall()
    transacciones=dataTr
    return(transacciones)

@app.route('/prestamo_transaccion_secuenci<int:secuenci>,<string:nombreProducto>,<int:secuenciCesantiaPrestamo>')
def prestamo_transaccion_secuenci(secuenci,nombreProducto,secuenciCesantiaPrestamo):
    print(nombreProducto)
    tr=prestamo_transaccion(secuenci)
    #return(transacciones)
    # Convertir los resultados a una cadena de texto JSON
    transacciones_json = json.dumps(tr)
    # Devolver la cadena de texto JSON
    #return render_template('transaccionesAhorro.html', transacciones_json=transacciones_json)
    return render_template('transaccionesPrestamo.html', transacciones=tr,nombrePR=nombreProducto,secuenciPrestamo=secuenci,secuenciPrestamoCesantia=secuenciCesantiaPrestamo)
    #return (transacciones_json)

@app.route('/ahorro')
def ahorro():
    cur = mysql.get_db().cursor()
    cur.execute("""
        SELECT 
        cl_clientes.Cl_NumIdent, cl_clientes.Cl_Nombres, cp_pp_productopasivo.Cp_Pp_Secuenci, cp_pp_productopasivo.Cp_PP_NombrePP, 
        cp_sl_saldo.Cp_Sl_Saldo,
        cp_sl_saldo.Cp_Sl_Fecha, cp_sl_saldo.Cp_Sl_Secuenci
        FROM 
        cl_clientes 
        INNER JOIN cp_sl_saldo on cl_clientes.Cl_Secuenci=cp_sl_saldo.Cl_Secuenci 
        INNER JOIN cp_pp_productopasivo on cp_sl_saldo.Cp_Pp_Secuenci=cp_pp_productopasivo.Cp_Pp_Secuenci
                WHERE cl_clientes.cl_estado='A' 
        AND cl_clientes.cl_numident='% s'  """ % userValidado)

    dataCp = cur.fetchall()

    return render_template('ahorro.html', captaciones=dataCp)


def ahorro_transaccion(secuenci):
    cur = mysql.get_db().cursor()
    cur.execute("""
        SELECT cp_tr_transaccion.Cp_Tr_Tipo,cp_tr_transaccion.Cp_Tr_Efectivo, cp_tr_transaccion.Cp_Tr_Fecha,
        cp_tr_transaccion.Cp_Tr_Saldo FROM cp_tr_transaccion
        WHERE cp_tr_transaccion.Cp_Sl_Secuenci='% s' 
        ORDER BY cp_tr_transaccion.Cp_Tr_Fecha DESC
        LIMIT 15
        """ % secuenci)
    dataTr = cur.fetchall()
    transacciones=dataTr
    return(transacciones)

@app.route('/ahorro_transaccion_secuenci<int:secuenci>,<string:nombreProducto>')
def ahorro_transaccion_secuenci(secuenci,nombreProducto):
    print(nombreProducto)
    tr=ahorro_transaccion(secuenci)
    #return(transacciones)
    # Convertir los resultados a una cadena de texto JSON
    transacciones_json = json.dumps(tr)
    # Devolver la cadena de texto JSON
    #return render_template('transaccionesAhorro.html', transacciones_json=transacciones_json)
    return render_template('transaccionesAhorro.html', transacciones=tr,nombreCP=nombreProducto)
    #return (transacciones_json)

""" @app.route('/descuentos<int:secuenci>', methods=['GET', 'POST'])
def descuentos(secuenci):
    if request.method == 'POST':
        selected_item = request.form.get('lista')
        cur = mysql.get_db().cursor()
        cur.execute(' SELECT * FROM atpuce_com.de_fd_fechadistribucion WHERE De_Fd_Fecha= %s;' (selected_item) )
        dataItem = cur.fetchall()
        item=dataItem
        return render_template('grilla.html', items_grilla=item)
    else:
        cur = mysql.get_db().cursor()
        cur.execute('SELECT * FROM atpuce_com.de_fd_fechadistribucion order by De_Fd_Fecha desc;')
        items = cur.fetchall()
        return render_template('descuentos.html', items=items) """



if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))