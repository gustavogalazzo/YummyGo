"""
Modelos de Restaurante e Endereço
"""
from src.extensions import db
import datetime

class Restaurante(db.Model):
    __tablename__ = 'restaurantes'

    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String(100), nullable=False)
    razao_social = db.Column(db.String(100), unique=True, nullable=True)
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    
    # Chave Estrangeira (Foreign Key) para ligar ao Dono (User)
    # Esta é a ligação "Um-para-Um"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # --- Dados de Gestão ---
    logo_url = db.Column(db.String(255), nullable=True)
    tempo_medio_entrega = db.Column(db.Integer, nullable=True) # Em minutos
    taxa_entrega = db.Column(db.Float, nullable=True)
    ativo = db.Column(db.Boolean, default=False) # Se está aceitando pedidos
    
    # Relacionamentos
    categorias = db.relationship('Categoria', backref='restaurante', lazy=True, cascade="all, delete-orphan")
    produtos = db.relationship('Produto', backref='restaurante', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Restaurante {self.nome_fantasia}>'


class Endereco(db.Model):
    __tablename__ = 'enderecos'

    id = db.Column(db.Integer, primary_key=True)
    rua = db.Column(db.String(255), nullable=False)
    numero = db.Column(db.String(20), nullable=False)
    complemento = db.Column(db.String(100), nullable=True)
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False) # Ex: SP
    cep = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Chave Estrangeira (Foreign Key) para ligar ao User
    # (Um cliente pode ter vários endereços, um restaurante pode ter o seu)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    

    def __repr__(self):
        return f'<Endereco {self.rua}, {self.numero} - {self.cidade}>'