"""
Modelo de Usuário (Cliente e Dono de Restaurante)
"""
from src.extensions import db, bcrypt
from flask_login import UserMixin
import datetime

# Importa o 'login_manager' de extensions para usar o 'user_loader'
from src.extensions import login_manager

@login_manager.user_loader
def load_user(user_id):
    """
    Função obrigatória do Flask-Login.
    Diz ao Flask-Login como encontrar um utilizador a partir do ID
    guardado na sessão.
    """
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """
    Representa tanto um Cliente como o Dono de um Restaurante.
    A 'role' (função) irá diferenciá-los.
    
    Herda de 'UserMixin' para incluir os métodos que o Flask-Login espera
    (como is_authenticated, is_active, get_id).
    """
    
    __tablename__ = 'users'

    # --- Colunas Principais ---
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    
    # --- Autenticação (Email/Telefone) ---
    # Email e Telefone são únicos, mas podem ser nulos (ex: login social)
    email = db.Column(db.String(120), unique=True, nullable=True)
    telefone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True) # Hash da BCrypt
    
    # --- Autenticação Social (Google, Facebook) ---
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    facebook_id = db.Column(db.String(120), unique=True, nullable=True)
    
    # --- Verificação OTP (One-Time Password) ---
    otp_code = db.Column(db.String(6), nullable=True) # Código de 6 dígitos
    otp_expiration = db.Column(db.DateTime, nullable=True) # Data/hora de expiração
    
    # --- Metadados ---
    data_criacao = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True) # Para o Flask-Login
    
    # --- Funções (Role) ---
    # Define se é 'cliente' ou 'restaurante'
    role = db.Column(db.String(20), nullable=False, default='cliente')

    # --- Relacionamentos ---
    # 'Enderecos' (Um User pode ter muitos Enderecos)
    # 'lazy=True' significa que o SQLAlchemy só carrega os endereços quando acedemos
    enderecos = db.relationship('Endereco', backref='user', lazy=True)
    
    # 'Pedidos' (Um User (cliente) pode ter muitos Pedidos)
    pedidos_cliente = db.relationship('Pedido', backref='cliente', lazy=True, foreign_keys='Pedido.cliente_id')

    # 'Restaurante' (Um User (dono) pode ter UM Restaurante)
    # 'uselist=False' diz ao SQLAlchemy que isto é "Um-para-Um"
    restaurante = db.relationship('Restaurante', backref='dono', uselist=False)

    pontos = db.Column(db.Integer, default=0)
    nivel = db.Column(db.String(20), default='Bronze')

    
    def __repr__(self):
        return f'<User {self.nome_completo} (ID: {self.id})>'

    # --- Métodos de Palavra-passe ---
    
    def set_password(self, password):
        """Gera o hash da palavra-passe e guarda-o."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica se a palavra-passe fornecida corresponde ao hash guardado."""
        if not self.password_hash:
            return False
        return bcrypt.check_password_hash(self.password_hash, password)