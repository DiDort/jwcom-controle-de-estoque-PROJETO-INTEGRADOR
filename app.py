
import os

import sqlite3

from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'chave_dev_padrao')

DB_FILE = os.path.join(os.path.dirname(__file__), 'jwcom.db')

def get_db_connection():

    conn = sqlite3.connect(DB_FILE)

    conn.row_factory = sqlite3.Row

    return conn

def init_db():

    conn = get_db_connection()

    cur = conn.cursor()

    cur.execute('''

        CREATE TABLE IF NOT EXISTS usuario (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT NOT NULL,

            usuario TEXT UNIQUE NOT NULL,

            senha TEXT NOT NULL,

            ativo INTEGER DEFAULT 1,

            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP

        );

    ''')

    cur.execute('''

        CREATE TABLE IF NOT EXISTS produto (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sku TEXT UNIQUE NOT NULL,

            nome TEXT NOT NULL,

            quantidade INTEGER DEFAULT 0,

            estoque_minimo INTEGER DEFAULT 5,

            ativo INTEGER DEFAULT 1,

            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP

        );

    ''')

    cur.execute('''

        CREATE TABLE IF NOT EXISTS movimentacao (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            produto_id INTEGER NOT NULL,

            usuario_id INTEGER NOT NULL,

            tipo TEXT NOT NULL,

            quantidade INTEGER NOT NULL,

            estoque_anterior INTEGER NOT NULL,

            estoque_posterior INTEGER NOT NULL,

            canal TEXT,

            justificativa TEXT,

            data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (produto_id) REFERENCES produto (id),

            FOREIGN KEY (usuario_id) REFERENCES usuario (id)

        );

    ''')

    admin_user = os.getenv('ADMIN_USER', 'admin')

    admin_pass = os.getenv('ADMIN_PASSWORD', 'admin123')

    cur.execute("SELECT id FROM usuario WHERE usuario = ?;", (admin_user,))

    if not cur.fetchone():

        cur.execute(

            "INSERT INTO usuario (nome, usuario, senha, ativo) VALUES (?, ?, ?, 1);",

            ("Administrador JWCOM", admin_user, admin_pass)

        )

    conn.commit()

    conn.close()

init_db()

def login_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:

            flash('Por favor, faça login para acessar esta página.', 'warning')

            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function

@app.route('/login', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        usuario_input = request.form.get('usuario', '').strip()

        senha_input = request.form.get('senha', '').strip()

        if not usuario_input or not senha_input:

            flash('Preencha os campos de usuário e senha.', 'danger')

            return render_template('login.html')

        conn = get_db_connection()

        user = conn.execute(

            "SELECT id, nome, usuario, senha, ativo FROM usuario WHERE usuario = ?;",

            (usuario_input,)

        ).fetchone()

        conn.close()

        if user and user['senha'] == senha_input:

            if not user['ativo']:

                flash('Usuário inativo. Entre em contato com o administrador.', 'danger')

                return render_template('login.html')

            session['user_id'] = user['id']

            session['user_nome'] = user['nome']

            session['user_login'] = user['usuario']

            flash(f'Bem-vindo, {user["nome"]}!', 'success')

            return redirect(url_for('index'))

        else:

            flash('Usuário ou senha inválidos.', 'danger')

    return render_template('login.html')

@app.route('/logout')

def logout():

    session.clear()

    flash('Sessão encerrada com sucesso.', 'info')

    return redirect(url_for('login'))

@app.route('/')

@app.route('/dashboard')

@login_required

def index():

    conn = get_db_connection()

    total_produtos = conn.execute("SELECT COUNT(*) FROM produto WHERE ativo = 1;").fetchone()[0]

    total_unidades = conn.execute("SELECT COALESCE(SUM(quantidade), 0) FROM produto WHERE ativo = 1;").fetchone()[0]

    estoque_baixo_count = conn.execute("SELECT COUNT(*) FROM produto WHERE quantidade <= estoque_minimo AND ativo = 1;").fetchone()[0]

    movimentacoes_hoje = conn.execute("SELECT COUNT(*) FROM movimentacao WHERE date(data_hora) = date('now');").fetchone()[0]

    produtos_baixo = conn.execute(

        "SELECT * FROM produto WHERE quantidade <= estoque_minimo AND ativo = 1 ORDER BY quantidade ASC LIMIT 5;"

    ).fetchall()

    ultimas_movimentacoes = conn.execute('''

        SELECT m.*, p.sku, p.nome as produto_nome, u.nome as usuario_nome

        FROM movimentacao m

        JOIN produto p ON m.produto_id = p.id

        JOIN usuario u ON m.usuario_id = u.id

        ORDER BY m.data_hora DESC LIMIT 5;

    ''').fetchall()

    conn.close()

    return render_template(

        'dashboard.html',

        total_produtos=total_produtos,

        total_unidades=total_unidades,

        estoque_baixo_count=estoque_baixo_count,

        movimentacoes_hoje=movimentacoes_hoje,

        produtos_baixo=produtos_baixo,

        ultimas_movimentacoes=ultimas_movimentacoes

    )

dashboard = index

@app.route('/produtos')

@login_required

def produtos():

    busca = request.args.get('busca', '').strip()

    conn = get_db_connection()

    if busca:

        produtos_lista = conn.execute(

            "SELECT * FROM produto WHERE sku LIKE ? OR nome LIKE ? ORDER BY id DESC;",

            (f'%{busca}%', f'%{busca}%')

        ).fetchall()

    else:

        produtos_lista = conn.execute("SELECT * FROM produto ORDER BY id DESC;").fetchall()

    conn.close()

    return render_template('produtos.html', produtos=produtos_lista, busca=busca)

@app.route('/produtos/cadastrar', methods=['POST'])

@login_required

def cadastrar_produto():

    sku = request.form.get('sku', '').strip().upper()

    nome = request.form.get('nome', '').strip()

    quantidade = request.form.get('quantidade', 0)

    estoque_minimo = request.form.get('estoque_minimo', 5)

    if not sku or not nome:

        flash('SKU e Nome do Produto são obrigatórios!', 'danger')

        return redirect(url_for('produtos'))

    try:

        conn = get_db_connection()

        conn.execute(

            "INSERT INTO produto (sku, nome, quantidade, estoque_minimo, ativo) VALUES (?, ?, ?, ?, 1);",

            (sku, nome, int(quantidade), int(estoque_minimo))

        )

        conn.commit()

        conn.close()

        flash(f'Produto "{sku} - {nome}" cadastrado com sucesso!', 'success')

    except sqlite3.IntegrityError:

        flash(f'Erro: O SKU "{sku}" já está cadastrado no sistema!', 'danger')

    except Exception as e:

        flash(f'Erro ao cadastrar produto: {e}', 'danger')

    return redirect(url_for('produtos'))

@app.route('/produtos/editar/<int:id>', methods=['POST'])

@login_required

def editar_produto(id):

    nome = request.form.get('nome', '').strip()

    estoque_minimo = request.form.get('estoque_minimo', 5)

    conn = get_db_connection()

    conn.execute(

        "UPDATE produto SET nome = ?, estoque_minimo = ? WHERE id = ?;",

        (nome, int(estoque_minimo), id)

    )

    conn.commit()

    conn.close()

    flash('Produto atualizado com sucesso!', 'success')

    return redirect(url_for('produtos'))

@app.route('/produtos/inativar/<int:id>', methods=['POST'])

@login_required

def inativar_produto(id):

    conn = get_db_connection()

    conn.execute("UPDATE produto SET ativo = 0 WHERE id = ?;", (id,))

    conn.commit()

    conn.close()

    flash('Produto inativado com sucesso!', 'warning')

    return redirect(url_for('produtos'))

@app.route('/produtos/reativar/<int:id>', methods=['POST'])

@login_required

def reativar_produto(id):

    conn = get_db_connection()

    conn.execute("UPDATE produto SET ativo = 1 WHERE id = ?;", (id,))

    conn.commit()

    conn.close()

    flash('Produto reativado com sucesso!', 'success')

    return redirect(url_for('produtos'))

@app.route('/produtos/exportar-pdf')

@login_required

def exportar_pdf():

    flash('Relatório pronto para impressão/PDF.', 'info')

    return redirect(url_for('produtos'))

@app.route('/movimentacao')

@login_required

def movimentacao():

    conn = get_db_connection()

    produtos_ativos = conn.execute("SELECT id, sku, nome, quantidade FROM produto WHERE ativo = 1 ORDER BY nome;").fetchall()

    conn.close()

    return render_template('movimentacao.html', produtos=produtos_ativos)

@app.route('/movimentacao/salvar', methods=['POST'])

@login_required

def salvar_movimentacao():

    produto_id = request.form.get('produto_id')

    tipo = request.form.get('tipo')

    quantidade = request.form.get('quantidade', type=int)

    canal = request.form.get('canal', '').strip()

    justificativa = request.form.get('justificativa', '').strip()

    usuario_id = session.get('user_id')

    if not produto_id or not tipo or quantidade is None or quantidade <= 0:

        flash('Preencha todos os campos obrigatórios corretamente!', 'danger')

        return redirect(url_for('movimentacao'))

    conn = get_db_connection()

    produto = conn.execute("SELECT * FROM produto WHERE id = ?;", (produto_id,)).fetchone()

    if not produto:

        conn.close()

        flash('Produto não encontrado!', 'danger')

        return redirect(url_for('movimentacao'))

    estoque_anterior = produto['quantidade']

    if tipo == 'entrada':

        estoque_posterior = estoque_anterior + quantidade

    elif tipo == 'saida':

        if quantidade > estoque_anterior:

            conn.close()

            flash(f'Estoque insuficiente! Saldo atual: {estoque_anterior}', 'danger')

            return redirect(url_for('movimentacao'))

        estoque_posterior = estoque_anterior - quantidade

    elif tipo == 'ajuste':

        estoque_posterior = quantidade

        quantidade = abs(estoque_posterior - estoque_anterior)

    try:

        conn.execute("UPDATE produto SET quantidade = ? WHERE id = ?;", (estoque_posterior, produto_id))

        conn.execute('''

            INSERT INTO movimentacao (produto_id, usuario_id, tipo, quantidade, estoque_anterior, estoque_posterior, canal, justificativa)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?);

        ''', (produto_id, usuario_id, tipo, quantidade, estoque_anterior, estoque_posterior, canal, justificativa))

        conn.commit()

        flash('Movimentação registrada com sucesso!', 'success')

    except Exception as e:

        conn.rollback()

        flash(f'Erro ao registrar movimentação: {e}', 'danger')

    finally:

        conn.close()

    return redirect(url_for('movimentacao'))

@app.route('/historico')

@login_required

def historico():

    conn = get_db_connection()

    movimentacoes = conn.execute('''

        SELECT m.*, p.sku, p.nome as produto_nome, u.nome as usuario_nome

        FROM movimentacao m

        JOIN produto p ON m.produto_id = p.id

        JOIN usuario u ON m.usuario_id = u.id

        ORDER BY m.data_hora DESC;

    ''').fetchall()

    conn.close()

    return render_template('historico.html', movimentacoes=movimentacoes)

if __name__ == '__main__':

    app.run(debug=True)

