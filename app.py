from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import sqlite3
import datetime
import os
import json
from iq_connect import conectar_iq

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

DB_PATH = 'historico.db'

def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE entradas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    par TEXT,
                    direcao TEXT,
                    resultado TEXT
                )
            ''')
        print("Banco de dados criado.")

init_db()

USUARIO = {
    "username": "admin",
    "password": "1234"
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logado' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def dashboard():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM entradas ORDER BY id DESC LIMIT 50")
        dados = c.fetchall()

    saldo = 50
    historico = []
    for row in reversed(dados):
        resultado = row[4]
        if resultado == "win":
            saldo += 1.6
        elif resultado == "loss":
            saldo -= 2
        historico.append({"data": row[1], "saldo": round(saldo, 2)})

    chart_data = json.dumps(historico)

    html = "<h2>Histórico de Entradas</h2><table border='1'><tr><th>Data</th><th>Par</th><th>Direção</th><th>Resultado</th></tr>"
    for row in dados:
        html += f"<tr><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td></tr>"
    html += "</table><br><a href='/logout'>Sair</a>"

    html += '''
    <h3>Evolução da Banca</h3>
    <canvas id='grafico' width='600' height='300'></canvas>
    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
    <script>
        const dados = JSON.parse(''' + f'"{chart_data}"' + ''');
        const labels = dados.map(d => d.data);
        const valores = dados.map(d => d.saldo);
        const ctx = document.getElementById('grafico').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Banca (R$)',
                    data: valores,
                    borderColor: 'green',
                    borderWidth: 2,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    </script>
    '''

    return html

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USUARIO['username'] and password == USUARIO['password']:
            session['logado'] = True
            return redirect(url_for('dashboard'))
        else:
            erro = 'Credenciais inválidas'
    return '''
    <form method="post">
        <input type="text" name="username" placeholder="Usuário"><br>
        <input type="password" name="password" placeholder="Senha"><br>
        <input type="submit" value="Entrar">
    </form>
    <p>{}</p>
    '''.format(erro if erro else '')

@app.route('/logout')
@login_required
def logout():
    session.pop('logado', None)
    return redirect(url_for('login'))

def salvar_entrada(par, direcao, resultado):
    data = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO entradas (data, par, direcao, resultado) VALUES (?, ?, ?, ?)",
                  (data, par, direcao, resultado))
        conn.commit()

@app.route('/iq-login', methods=['GET', 'POST'])
def iq_login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        tipo_conta = request.form['tipo_conta']
        iq = conectar_iq(email, senha, tipo_conta)

        if iq:
            session['iq_email'] = email
            session['iq_tipo'] = tipo_conta
            session['iq_logado'] = True
            return redirect('/')
        else:
            return "Falha ao conectar com a IQ Option"

    return render_template('login_iq.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)