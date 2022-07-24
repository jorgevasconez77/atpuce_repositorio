
from distutils.util import execute
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

userValidado = ""


app = Flask(__name__)

# Mysql Connection

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Jorge_7789'
app.config['MYSQL_DB'] = 'atpuce_com'
mysql = MySQL(app)

# settings
app.secret_key = 'mysecretkey'


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/sign_in')
def sign_in():
    return render_template('sign_in.html')


@app.route('/valida_inicio', methods=['POST'])
def valida_inicio():

    usuario = request.form['usuario']
    password = request.form['password']

    if usuario == password:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT cl_clientes.cl_Nombres,cl_NumIdent,Cl_Estado FROM cl_clientes WHERE Cl_Estado='A' AND Cl_NumIdent='%s'" % usuario)
        data = cur.fetchall()
        print("SELECT cl_clientes.cl_Nombres,cl_NumIdent,Cl_Estado FROM cl_clientes WHERE Cl_Estado='A' AND Cl_NumIdent='%s'" % usuario)
        check = False
        print(" antes del for check:" and check)
        for d in data:
            check = True
        print(" despues del for check:" and check)
        if check == False:
            flash('Usuario/Password NO coincidentes')
            print("usuario no se encuentra en la base check:" and check)
            return redirect(url_for('sign_in'))
        else:
            global userValidado
            userValidado = usuario
            print("Usuario si encuentra en la base: UserValidado " and userValidado)
            return redirect(url_for('saldos'))
    else:
        flash('Usuario/Password NO similares')
        return redirect(url_for('sign_in'))


@app.route('/saldos')
def saldos():
    
    print("Entra a saldos")
    cur = mysql.connection.cursor()
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
    return render_template('saldos.html', captaciones=dataCp,colocaciones=dataCo )

@app.route('/saldos')
def prestamos():
    print("Entra a prestamos")
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
        co_pc_productocolocacion.co_pc_nombre, co_pr_prestamo.Co_Pr_Secuenci, co_pr_prestamo.Co_Pr_ValSoli, 
        co_pr_prestamo.Co_Pr_VSaldo, co_pr_prestamo.Co_Pr_InDeven, (co_pr_prestamo.Co_Pr_VSaldo+co_pr_prestamo.Co_Pr_InDeven)
        as SaldoTotal,co_pr_prestamo.Co_Pr_NoCuotas,co_pr_prestamo.Co_Pr_FechaAd, 
        concat(co_de_destino.Co_De_Descrip, ' ' , co_pr_prestamo.Co_Pr_Descrip) as Co_Pr_Descrip
        FROM
        cl_clientes
        INNER JOIN co_pr_prestamo on cl_clientes.Cl_Secuenci=co_pr_prestamo.Cl_Secuenci
        INNER JOIN co_de_destino on co_pr_prestamo.Co_De_Secuenci=co_de_destino.Co_De_Secuenci 
        INNER JOIN co_pc_productocolocacion on co_pr_prestamo.Co_Pc_Secuenci=co_pc_productocolocacion.Co_Pc_Secuenci
                WHERE cl_clientes.cl_estado='A'
        AND cl_clientes.cl_numident='% s'  """ % userValidado)

    dataCo = cur.fetchall()
    print (dataCo)
    return dataCo
    #return render_template('saldos.html', colocaciones=dataCo)


if __name__ == '__main__':
    app.run(debug=True)
