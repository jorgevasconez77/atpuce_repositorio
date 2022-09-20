import os

#import logging

from distutils.util import execute
from mmap import PROT_WRITE

from flask import Flask, render_template, request, redirect, url_for, flash
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
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Jorge_7789'
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

# @app.route('/saldos')
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
        concat(co_de_destino.Co_De_Descrip, ' ' , co_pr_prestamo.Co_Pr_Descrip) as Co_Pr_Descrip
	    FROM
        cl_clientes
        INNER JOIN co_pr_prestamo on cl_clientes.Cl_Secuenci=co_pr_prestamo.Cl_Secuenci
        INNER JOIN co_de_destino on co_pr_prestamo.Co_De_Secuenci=co_de_destino.Co_De_Secuenci 
        INNER JOIN co_pc_productocolocacion on co_pr_prestamo.Co_Pc_Secuenci=co_pc_productocolocacion.Co_Pc_Secuenci
        WHERE cl_clientes.cl_estado='A' and co_pr_prestamo.co_pr_estado='A'
        AND cl_clientes.cl_numident='% s'  """ % userValidado)

    dataCo = cur.fetchall()
    # print(dataCo)
    return dataCo
    # return render_template('saldos.html', colocaciones=dataCo)


if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))