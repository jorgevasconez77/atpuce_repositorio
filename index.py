from flask import Flask, render_template
from flask import Flask,render_template
from flask_mysqldb import MySQL


app = Flask(__name__)


app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Jorge_7789'
app.config['MYSQL_DB']='atpuce_com'
mysql=MySQL(app)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/sign_in')
def sign_in():
    return render_template('sign_in.html')
    usuario=request.form['usuario']
    password=request.form['password']


if __name__ == '__main__':
    app.run(debug=True)
