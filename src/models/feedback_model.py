"""
Modelo de Avaliação (Feedback) do Pedido
"""
from src.extensions import db
import datetime

class Avaliacao(db.Model):
    __tablename__ = 'avaliacoes'

    id = db.Column(db.Integer, primary_key=True)
    
    # Ligações
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    restaurante_id = db.Column(db.Integer, db.ForeignKey('restaurantes.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Dados da Avaliação
    nota = db.Column(db.Integer, nullable=False) # 1 a 5 estrelas
    comentario = db.Column(db.Text, nullable=True)
    reclamacao = db.Column(db.Boolean, default=False) # Se o cliente marcou como reclamação
    
    data_criacao = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Avaliacao Pedido {self.pedido_id} - Nota: {self.nota}>'