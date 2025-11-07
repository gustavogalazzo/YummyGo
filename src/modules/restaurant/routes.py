"""
Módulo do Restaurante (Restaurant) - Rotas

Define as rotas para /portal/ (dashboard) e /portal/registar
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.modules.restaurant.forms import RestaurantRegistrationForm, CategoryForm, ProductForm, OrderStatusForm
from src.extensions import db
from src.models import Restaurante, Categoria, Produto, Pedido, ItemPedido
from flask import abort 

# 1. Criação do Blueprint
restaurant_bp = Blueprint('restaurant', __name__, template_folder='templates')


# 2. Rota do Painel (Dashboard)
@restaurant_bp.route('/')
@login_required
def dashboard():
    """
    Página principal do Portal do Restaurante.
    A URL completa será /portal/
    """
    # 3. VERIFICAÇÃO DE SEGURANÇA:
    # Garante que só utilizadores com 'role' de restaurante
    # podem aceder a este painel.
    if current_user.role != 'restaurante':
        flash('Acesso negado. Registe o seu restaurante primeiro.', 'danger')
        return redirect(url_for('restaurant.register')) # Manda-o registar
        
    # Se ele for um restaurante, mostra o painel
    # (Usamos 'current_user.restaurante' da nossa relação One-to-One)
    return render_template('dashboard.html')


# 4. Rota de Registo de Restaurante
@restaurant_bp.route('/registar', methods=['GET', 'POST'])
@login_required
def register():
    """
    Página para um cliente ('cliente') registar o seu restaurante.
    A URL completa será /portal/registar
    """
    
    # 5. Se o utilizador JÁ É um restaurante, manda-o para o painel
    if current_user.role == 'restaurante':
        return redirect(url_for('restaurant.dashboard'))
        
    form = RestaurantRegistrationForm()
    
    if form.validate_on_submit():
        # 6. Cria o novo objeto Restaurante
        novo_restaurante = Restaurante(
            nome_fantasia=form.nome_fantasia.data,
            cnpj=form.cnpj.data,
            taxa_entrega=form.taxa_entrega.data,
            tempo_medio_entrega=form.tempo_medio_entrega.data,
            ativo=False # Começa inativo (precisa de aprovação do Admin, etc)
        )
        
        try:
            # 7. A MÁGICA DA RELAÇÃO:
            # Liga o restaurante ao 'dono' (o utilizador logado)
            novo_restaurante.dono = current_user
            
            # 8. MUDA A FUNÇÃO (ROLE) DO UTILIZADOR
            current_user.role = 'restaurante'
            
            db.session.add(novo_restaurante)
            db.session.commit()
            
            flash('Restaurante registado com sucesso! Bem-vindo ao Portal!', 'success')
            return redirect(url_for('restaurant.dashboard')) # Manda para o novo painel

        except Exception as e:
            db.session.rollback()
            flash('Erro ao registar o restaurante. Tente novamente.', 'danger')
            print(f"Erro ao registar restaurante: {e}")

    return render_template('register_restaurant.html', form=form)

# --- Rota de Gestão do Cardápio (Menu) ---
@restaurant_bp.route('/cardapio', methods=['GET', 'POST'])
@login_required
def manage_menu():
    """
    Página principal de gestão do Cardápio.
    GET: Lista tudo.
    POST: Adiciona Categoria OU Adiciona Produto.
    """
    # 1. Garante que é um restaurante
    if current_user.role != 'restaurante':
        abort(403) # Proibido
        
    restaurante = current_user.restaurante
    
    # 2. Instancia os DOIS formulários
    category_form = CategoryForm()
    product_form = ProductForm()

    # 3. Preenche as 'choices' (opções) do <select> de categorias
    #    no formulário de produto.
    #    (Pega todas as categorias deste restaurante)
    product_form.categoria_id.choices = [
        (cat.id, cat.nome) for cat in Categoria.query.filter_by(restaurante_id=restaurante.id).order_by(Categoria.nome).all()
    ]

    # 4. Lógica de Adicionar (POST)
    #    Temos de descobrir qual formulário foi enviado
    
    # Se o botão 'submit_category' foi clicado...
    if category_form.submit_category.data and category_form.validate_on_submit():
        nova_categoria = Categoria(
            nome=category_form.nome.data,
            restaurante_id=restaurante.id
        )
        db.session.add(nova_categoria)
        db.session.commit()
        flash('Categoria adicionada com sucesso!', 'success')
        return redirect(url_for('restaurant.manage_menu')) # Recarrega a página

    # Se o botão 'submit_product' foi clicado...
    if product_form.submit_product.data and product_form.validate_on_submit():
        novo_produto = Produto(
            nome=product_form.nome.data,
            descricao=product_form.descricao.data,
            preco=product_form.preco.data,
            disponivel=product_form.disponivel.data,
            categoria_id=product_form.categoria_id.data,
            restaurante_id=restaurante.id # Facilita buscas
        )
        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('restaurant.manage_menu'))

    # 5. Lógica GET (Listar)
    #    Busca todas as categorias do restaurante
    categorias = Categoria.query.filter_by(restaurante_id=restaurante.id).order_by(Categoria.nome).all()
    
    return render_template(
        'manage_menu.html',
        category_form=category_form,
        product_form=product_form,
        categorias=categorias
    )


# --- Rota para Apagar Categoria ---
@restaurant_bp.route('/cardapio/categoria/apagar/<int:categoria_id>', methods=['POST'])
@login_required
def delete_category(categoria_id):
    if current_user.role != 'restaurante':
        abort(403)
        
    categoria = Categoria.query.get_or_404(categoria_id)
    
    # Segurança: Garante que a categoria pertence ao restaurante logado
    if categoria.restaurante_id != current_user.restaurante.id:
        abort(403)
        
    # Graças ao 'cascade="all, delete-orphan"' no modelo,
    # apagar a categoria também apaga todos os produtos dentro dela.
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoria (e todos os seus produtos) apagada com sucesso.', 'success')
    return redirect(url_for('restaurant.manage_menu'))


# --- Rota para Apagar Produto ---
@restaurant_bp.route('/cardapio/produto/apagar/<int:produto_id>', methods=['POST'])
@login_required
def delete_product(produto_id):
    if current_user.role != 'restaurante':
        abort(403)
        
    produto = Produto.query.get_or_404(produto_id)
    
    # Segurança: Garante que o produto pertence ao restaurante logado
    if produto.restaurante_id != current_user.restaurante.id:
        abort(403)
        
    db.session.delete(produto)
    db.session.commit()
    flash('Produto apagado com sucesso.', 'success')
    return redirect(url_for('restaurant.manage_menu'))

# --- Rota de Gestão de Pedidos (A COZINHA) ---
STATUS_FLUXO = ['Recebido', 'Em Preparo', 'Em Rota de Entrega', 'Concluído']

@restaurant_bp.route('/pedidos', methods=['GET', 'POST'])
@login_required
def manage_orders():
    """
    Lista todos os pedidos do restaurante e permite mudar o status.
    A URL é /portal/pedidos
    """
    if current_user.role != 'restaurante':
        abort(403)
        
    restaurante = current_user.restaurante
    form = OrderStatusForm()
    
    # Busca todos os pedidos, exceto os 'Concluído'
    pedidos = Pedido.query.filter(
        Pedido.restaurante_id == restaurante.id,
        Pedido.status.notin_(['Concluído', 'Cancelado'])
    ).order_by(Pedido.data_criacao.desc()).all()

    if form.validate_on_submit():
        # Lógica POST: Atualizar o Status
        
        # Pega o ID do pedido que veio do botão
        pedido_id = request.form.get('pedido_id') 
        pedido = Pedido.query.get(pedido_id)
        
        if pedido and pedido.restaurante_id == restaurante.id:
            # Encontra o índice do status atual no nosso fluxo (STATUS_FLUXO)
            try:
                current_index = STATUS_FLUXO.index(pedido.status)
                
                # Se não é o último status, avança para o próximo
                if current_index < len(STATUS_FLUXO) - 1:
                    pedido.status = STATUS_FLUXO[current_index + 1]
                    db.session.commit()
                    flash(f"Pedido #{pedido.id} atualizado para '{pedido.status}'", 'success')
                else:
                    flash('Este pedido já está no status final (Concluído).', 'info')
            except ValueError:
                flash('Não é possível atualizar o status deste pedido.', 'danger')
                
        return redirect(url_for('restaurant.manage_orders'))

    return render_template(
        'manage_orders.html', 
        pedidos=pedidos, 
        form=form,
        status_fluxo=STATUS_FLUXO
    )