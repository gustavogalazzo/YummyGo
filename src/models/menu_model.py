"""
Modelos do Cardápio (Menu): Categoria e Produto
"""
from src.extensions import db
import datetime

class Categoria(db.Model):
    """
    Categorias do cardápio (ex: Pizzas, Bebidas, Sobremesas).
    Cada categoria pertence a UM restaurante.
    """
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    
    # Chave Estrangeira: A que restaurante esta categoria pertence?
    restaurante_id = db.Column(db.Integer, db.ForeignKey('restaurantes.id'), nullable=False)

    # Relacionamento: Uma Categoria tem muitos Produtos
    # 'cascade="all, delete-orphan"' significa que se apagarmos
    # uma categoria, todos os produtos dentro dela também são apagados.
    produtos = db.relationship('Produto', backref='categoria', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Categoria {self.nome}>'


class Produto(db.Model):
    """
    Produtos do cardápio (ex: Pizza Margherita).
    Cada produto pertence a UMA categoria e a UM restaurante.
    """
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    imagem_url = db.Column(db.String(255), nullable=True)
    disponivel = db.Column(db.Boolean, default=True)
    
    # Chave Estrangeira: A que categoria este produto pertence?
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)

    # Chave Estrangeira: A que restaurante este produto pertence?
    # (Isto é tecnicamente redundante, pois já temos categoria.restaurante,
    # mas torna as nossas buscas por 'todos os produtos de um restaurante'
    # muito mais rápidas e fáceis)
    restaurante_id = db.Column(db.Integer, db.ForeignKey('restaurantes.id'), nullable=False)

    def __repr__(self):
        return f'<Produto {self.nome} - {self.preco}>'