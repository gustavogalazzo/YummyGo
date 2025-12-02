"""
Modelos do Pedido: Pedido (Order) e ItemPedido (OrderItem)
"""
from src.extensions import db
import datetime

class Pedido(db.Model):
    """
    Representa um pedido (compra) feito por um cliente a um restaurante.
    """
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    
    # Chaves Estrangeiras
    cliente_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurante_id = db.Column(db.Integer, db.ForeignKey('restaurantes.id'), nullable=False)

    # Relacionamento: Permite aceder ao objeto restaurante via pedido.restaurante
    restaurante = db.relationship('Restaurante', backref='pedidos_do_restaurante', lazy=True)

    # Dados do Pedido
    preco_total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Recebido')
    # (Ex: Recebido -> Em preparo -> Em rota de entrega -> Concluído)
    
    data_criacao = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Detalhes da entrega (copiados do endereço no momento da compra)
    endereco_entrega = db.Column(db.String(255), nullable=False)

    tipo_pagamento = db.Column(db.String(50), nullable=False, default='Cartão de Crédito')

    # Relacionamento: Um Pedido tem muitos ItensPedido
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Pedido {self.id} - Status: {self.status}>'


class ItemPedido(db.Model):
    """
    Representa um item *dentro* de um Pedido
    (Ex: 3x Pizza Margherita, 2x Coca-Cola)
    """
    __tablename__ = 'itens_pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Chaves Estrangeiras
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    
    # Preço 'Congelado': O preço do produto NO MOMENTO da compra
    # (Importante, caso o preço do produto mude no futuro)
    preco_unitario_na_compra = db.Column(db.Float, nullable=False)

    # Relacionamento (para fácil acesso ao nome do produto, etc)
    produto = db.relationship('Produto', backref='itens_pedido')

    def __repr__(self):
        return f'<{self.quantidade}x (Produto ID: {self.produto_id}) no Pedido {self.pedido_id}>'