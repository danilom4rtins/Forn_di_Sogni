from flask import Flask, flash, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pizzaria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretkey123'

# Configuração do upload de imagens
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_cliente'

db = SQLAlchemy(app)

# Função para verificar se a extensão do arquivo é permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Modelos
class Prato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(120), nullable=True)
    favoritos = db.relationship('Favorito', back_populates='prato', cascade="all, delete")

class Bebida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(200), nullable=True)
    favoritos = db.relationship('Favorito', back_populates='bebida', cascade="all, delete")

class Funcionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    foto = db.Column(db.String(200), nullable=True)
    apresentacao = db.Column(db.Text, nullable=True)

class Cliente(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    favoritos = db.relationship('Favorito', back_populates='cliente', cascade="all, delete")

class Favorito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    prato_id = db.Column(db.Integer, db.ForeignKey('prato.id'), nullable=True)
    bebida_id = db.Column(db.Integer, db.ForeignKey('bebida.id'), nullable=True)
    cliente = db.relationship('Cliente', back_populates='favoritos')
    prato = db.relationship('Prato', back_populates='favoritos', foreign_keys=[prato_id])
    bebida = db.relationship('Bebida', back_populates='favoritos', foreign_keys=[bebida_id])

# Rota para o menu de administração
@app.route('/admin')
def admin_menu():
    return render_template('adm/admin_menu.html')


# CRUD para Funcionários

# Rota para criar um novo funcionário (formulário)
@app.route('/funcionarios/novo', methods=['GET', 'POST'])
def criar_funcionario():
    if request.method == 'POST':
        nome = request.form['nome']
        cargo = request.form['cargo']
        apresentacao = request.form['apresentacao']
        
        # Processar o arquivo de foto
        foto = request.files.get('foto')
        if foto and allowed_file(foto.filename):
            filename = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        
        novo_funcionario = Funcionario(nome=nome, cargo=cargo, apresentacao=apresentacao, foto=filename)
        db.session.add(novo_funcionario)
        db.session.commit()
        return redirect(url_for('listar_funcionarios'))
    return render_template('adm/create_funcionario.html')

# Rota para listar todos os funcionários
@app.route('/funcionarios', methods=['GET'])
def listar_funcionarios():
    funcionarios = Funcionario.query.all()
    return render_template('adm/list_funcionarios.html', funcionarios=funcionarios)

# Rota para editar um funcionário
@app.route('/funcionarios/<int:id>/edit', methods=['GET', 'POST'])
def editar_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    if request.method == 'POST':
        funcionario.nome = request.form['nome']
        funcionario.cargo = request.form['cargo']
        funcionario.apresentacao = request.form['apresentacao']
        
        foto = request.files.get('foto')
        if foto and allowed_file(foto.filename):
            filename = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            funcionario.foto = filename
        
        db.session.commit()
        return redirect(url_for('listar_funcionarios'))
    return render_template('adm/update_funcionario.html', funcionario=funcionario)

# Rota para excluir um funcionário
@app.route('/funcionarios/<int:id>/delete', methods=['POST'])
def excluir_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    db.session.delete(funcionario)
    db.session.commit()
    return redirect(url_for('listar_funcionarios'))

# PRATOS

# Rota para criar um novo prato (formulário)
@app.route('/pratos/novo', methods=['GET', 'POST'])
def criar_prato():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = request.form['preco']
        
        # Processar o arquivo de imagem
        imagem = request.files.get('imagem')
        if imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        
        novo_prato = Prato(nome=nome, descricao=descricao, preco=preco, imagem=filename)
        db.session.add(novo_prato)
        db.session.commit()
        return redirect(url_for('listar_pratos'))
    return render_template('adm/create_prato.html')

# Rota para listar todos os pratos
@app.route('/pratos', methods=['GET'])
def listar_pratos():
    pratos = Prato.query.all()
    return render_template('adm/list_pratos.html', pratos=pratos)

# Rota para atualizar um prato existente
@app.route('/pratos/<int:id>/edit', methods=['GET', 'POST'])
def atualizar_prato(id):
    prato = Prato.query.get_or_404(id)
    if request.method == 'POST':
        prato.nome = request.form['nome']
        prato.descricao = request.form['descricao']
        prato.preco = request.form['preco']
        
        imagem = request.files.get('imagem')
        if imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            prato.imagem = filename
        
        db.session.commit()
        return redirect(url_for('listar_pratos'))
    return render_template('adm/update_prato.html', prato=prato)

# Rota para excluir um prato
@app.route('/pratos/<int:id>/delete', methods=['POST'])
def excluir_prato(id):
    prato = Prato.query.get_or_404(id)
    db.session.delete(prato)
    db.session.commit()
    return redirect(url_for('listar_pratos'))


# Bebidas

# Rota para criar uma nova bebida (formulário)
@app.route('/bebidas/novo', methods=['GET', 'POST'])
def criar_bebida():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = request.form['preco']
        
        # Processar o arquivo de imagem
        imagem = request.files.get('imagem')
        if imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None
        
        nova_bebida = Bebida(nome=nome, descricao=descricao, preco=preco, imagem=filename)
        db.session.add(nova_bebida)
        db.session.commit()
        return redirect(url_for('listar_bebidas'))
    return render_template('adm/create_bebida.html')

# Rota para listar todas as bebidas
@app.route('/bebidas', methods=['GET'])
def listar_bebidas():
    bebidas = Bebida.query.all()
    return render_template('adm/list_bebidas.html', bebidas=bebidas)

# Rota para editar uma bebida
@app.route('/bebidas/<int:id>/edit', methods=['GET', 'POST'])
def editar_bebida(id):
    bebida = Bebida.query.get_or_404(id)
    if request.method == 'POST':
        bebida.nome = request.form['nome']
        bebida.descricao = request.form['descricao']
        bebida.preco = request.form['preco']
        
        imagem = request.files.get('imagem')
        if imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            bebida.imagem = filename
        
        db.session.commit()
        return redirect(url_for('listar_bebidas'))
    return render_template('adm/update_bebida.html', bebida=bebida)

# Rota para excluir uma bebida
@app.route('/bebidas/<int:id>/delete', methods=['POST'])
def excluir_bebida(id):
    bebida = Bebida.query.get_or_404(id)
    db.session.delete(bebida)
    db.session.commit()
    return redirect(url_for('listar_bebidas'))

@app.route('/detalhes/prato/<int:prato_id>', methods=['GET'])
def detalhes_prato(prato_id):
    prato = Prato.query.get(prato_id)  # Função para buscar o prato pelo ID
    return render_template('Cliente/detalhes.html', item=prato)

@app.route('/detalhes/bebida/<int:bebida_id>', methods=['GET'])
def detalhes_bebida(bebida_id):
    bebida = Bebida.query.get(bebida_id)  # Função para buscar a bebida pelo ID
    return render_template('Cliente/detalhes.html', item=bebida)

@app.route('/', methods=['GET'])
def home():
    pratos = Prato.query.all()
    bebidas = Bebida.query.all()
    return render_template('index.html', pratos=pratos, bebidas=bebidas)


@login_manager.user_loader
def load_user(cliente_id):
    return Cliente.query.get(int(cliente_id))

# Cadastro para usuários

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = bcrypt.generate_password_hash(request.form['senha']).decode('utf-8')

        novo_cliente = Cliente(nome=nome, email=email, senha=senha)
        db.session.add(novo_cliente)
        db.session.commit()
        return redirect(url_for('login_cliente'))
    return render_template('cliente/cadastro.html')

# Login de usuário

@app.route('/login', methods=['GET', 'POST'])
def login_cliente():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        cliente = Cliente.query.filter_by(email=email).first()
        if cliente and bcrypt.check_password_hash(cliente.senha, senha):
            login_user(cliente)
            return redirect(url_for('home'))  # Redireciona para o menu principal
        else:
            flash("Login ou senha inválidos", "danger")
            return redirect(url_for('login_cliente'))
    return render_template('cliente/login.html')

# Relogar usuário

@app.route('/logout', methods=['GET'])
@login_required
def logout_cliente():
    logout_user()
    return redirect(url_for('login_cliente'))


# Rota para conhecer os funcionários

@app.route('/conhecer_funcionarios', methods=['GET'])
def conhecer_funcionarios():
    funcionarios = Funcionario.query.all()  # Consulta todos os funcionários
    return render_template('cliente/conhecer_funcionarios.html', funcionarios=funcionarios)


# Favoritos

@app.route('/adicionar_favorito', methods=['POST'])
@login_required
def adicionar_favorito():
    prato_id = request.form.get('prato_id')  # ID do prato enviado pelo formulário
    bebida_id = request.form.get('bebida_id')  # ID da bebida enviado pelo formulário

    # Verifica se ao menos um dos dois IDs foi enviado
    if not prato_id and not bebida_id:
        flash("Nenhum item selecionado para adicionar aos favoritos.", "warning")
        return redirect(request.referrer or url_for('menu'))

    # Checa se o item já está nos favoritos
    favorito_existente = Favorito.query.filter_by(
        cliente_id=current_user.id,
        prato_id=prato_id if prato_id else None,
        bebida_id=bebida_id if bebida_id else None
    ).first()

    if favorito_existente:
        flash("Esse item já está nos seus favoritos!", "info")
        return redirect(request.referrer or url_for('menu'))

    # Adiciona o item aos favoritos
    novo_favorito = Favorito(
        cliente_id=current_user.id,
        prato_id=prato_id if prato_id else None,
        bebida_id=bebida_id if bebida_id else None
    )

    db.session.add(novo_favorito)
    db.session.commit()

    flash("Item adicionado aos favoritos com sucesso!", "success")
    return redirect(request.referrer or url_for('menu'))

@app.route('/favoritos', methods=['GET'])
@login_required
def area_favoritos():
    if not current_user.is_authenticated:
        flash("Você precisa estar logado para acessar seus favoritos!", "warning")
        return redirect(url_for('login_cliente'))

    # Obter favoritos do usuário, incluindo as informações de pratos e bebidas
    favoritos = Favorito.query.filter_by(cliente_id=current_user.id).all()
    pratos = Prato.query.all()
    bebidas = Bebida.query.all()
    # Renderizar o template com a lista de favoritos
    return render_template('cliente/favoritos.html', favoritos=favoritos, prato=pratos, bebida=bebidas)

@app.route('/favoritos/<int:id>/delete', methods=['POST'])
@login_required
def excluir_favorito(id):
    favorito = Favorito.query.get_or_404(id)
    if favorito.cliente_id == current_user.id:
        db.session.delete(favorito)
        db.session.commit()
    return redirect(url_for('area_favoritos'))

# Inicializar o banco de dados
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)