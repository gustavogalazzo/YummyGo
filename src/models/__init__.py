"""
Este __init__.py serve para expor os modelos para o resto da aplicação,
especialmente para o Flask-Migrate.

Ao importar os modelos aqui, o Alembic (motor do Migrate) 
consegue detetá-los quando corre o 'flask db migrate'.
"""

from .user_model import User
from .restaurant_model import Restaurante, Endereco
from .menu_model import Categoria, Produto
from .order_model import Pedido, ItemPedido
from .feedback_model import Avaliacao
# from .payment_model import FormaPagamento (ainda não criámos)