"""
Módulo do Restaurante (Restaurant) - Rotas

Define as rotas para /portal/ (dashboard) e /portal/registar
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.modules.restaurant.forms import RestaurantRegistrationForm, CategoryForm, ProductForm, OrderStatusForm, UpdateRestaurantInfoForm
from src.extensions import db
from src.models import Restaurante, Categoria, Produto, Pedido, ItemPedido, Avaliacao
from flask import abort 
from sqlalchemy import func, case
from datetime import datetime, timedelta

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

# --- Rota de Gestão de Informações do Estabelecimento ---
@restaurant_bp.route('/info', methods=['GET', 'POST'])
@login_required
def manage_info():
    """
    Permite ao dono do restaurante atualizar as suas informações de negócio.
    """
    if current_user.role != 'restaurante':
        abort(403)
        
    restaurante = current_user.restaurante
    form = UpdateRestaurantInfoForm(obj=restaurante) # Pré-preenche o formulário
    
    if form.validate_on_submit():
        # Atualiza o objeto restaurante com os dados do formulário
        form.populate_obj(restaurante)
        db.session.commit()
        flash('Informações do restaurante atualizadas com sucesso!', 'success')
        return redirect(url_for('restaurant.dashboard'))

    return render_template('manage_info.html', form=form)

# --- Rota de Relatório de Vendas ---
@restaurant_bp.route('/relatorio', methods=['GET'])
@login_required
def orders_report():
    """
    Gera um relatório de pedidos agrupado por restaurante.
    Inclui filtros de data e dados para gráfico.
    """
    # 1. Obter filtros de data da URL (GET)
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')

    # Datas padrão (Últimos 30 dias se não for informado)
    if data_inicio_str:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
    else:
        data_inicio = datetime.now() - timedelta(days=30)
        
    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
        # Ajusta para o final do dia (23:59:59)
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
    else:
        data_fim = datetime.now()

    # 2. Consulta ao Banco de Dados (Aggregation)
    # SQL equivalente: SELECT nome, count(id), sum(total) FROM pedidos GROUP BY restaurante_id
    resultados = db.session.query(
        Restaurante.nome_fantasia,
        func.count(Pedido.id).label('qtd_pedidos'),
        func.sum(Pedido.preco_total).label('faturamento')
    ).join(Pedido).filter(
        Pedido.data_criacao >= data_inicio,
        Pedido.data_criacao <= data_fim,
        Pedido.status != 'Cancelado' # Ignora cancelados
    ).group_by(Restaurante.id).all()

    # 3. Processar Dados para a Tabela e Gráfico
    relatorio_dados = []
    total_geral_pedidos = 0
    
    # Primeiro loop para calcular o total geral (para a porcentagem)
    for r in resultados:
        total_geral_pedidos += r.qtd_pedidos

    # Segundo loop para montar os dados finais
    nomes_grafico = []
    valores_grafico = []
    cores_grafico = [] # Vamos gerar cores aleatórias ou fixas

    import random
    
    for r in resultados:
        ticket_medio = r.faturamento / r.qtd_pedidos if r.qtd_pedidos > 0 else 0
        representatividade = (r.qtd_pedidos / total_geral_pedidos * 100) if total_geral_pedidos > 0 else 0
        
        # Dados para a tabela
        relatorio_dados.append({
            'restaurante': r.nome_fantasia,
            'qtd': r.qtd_pedidos,
            'faturamento': r.faturamento,
            'ticket_medio': ticket_medio,
            'perc': representatividade
        })

        # Dados para o Chart.js
        nomes_grafico.append(r.nome_fantasia)
        valores_grafico.append(r.qtd_pedidos)
        # Gera uma cor aleatória hexadecimal
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        cores_grafico.append(color)

    return render_template(
        'orders_report.html',
        relatorio=relatorio_dados,
        total_geral=total_geral_pedidos,
        data_inicio=data_inicio.strftime('%Y-%m-%d'),
        data_fim=data_fim.strftime('%Y-%m-%d'),
        # Passa dados para o JS
        grafico_labels=nomes_grafico,
        grafico_data=valores_grafico,
        grafico_colors=cores_grafico
    )

# --- Rota de Relatório de Qualidade (Avaliações) ---
@restaurant_bp.route('/relatorio/qualidade', methods=['GET'])
@login_required
def quality_report():
    """
    Gera um relatório de qualidade (Avaliações e Reclamações).
    """
    # 1. Filtros de Data (Igual ao relatório anterior)
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')

    if data_inicio_str:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
    else:
        data_inicio = datetime.now() - timedelta(days=30)
        
    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
    else:
        data_fim = datetime.now()

    # 2. Consulta: Agrupa por Restaurante e calcula Média e Contagem de Reclamações
    resultados = db.session.query(
        Restaurante.nome_fantasia,
        func.avg(Avaliacao.nota).label('media_nota'),
        func.count(Avaliacao.id).label('qtd_total'),
        func.sum(case((Avaliacao.reclamacao == True, 1), else_=0)).label('qtd_reclamacoes')
    ).join(Avaliacao).filter(
        Avaliacao.data_criacao >= data_inicio,
        Avaliacao.data_criacao <= data_fim
    ).group_by(Restaurante.id).all()

    # 3. Processar Dados
    relatorio_dados = []
    nomes_grafico = []
    medias_grafico = []

    for r in resultados:
        media = float(r.media_nota) if r.media_nota else 0
        perc_reclamacoes = (r.qtd_reclamacoes / r.qtd_total * 100) if r.qtd_total > 0 else 0
        
        relatorio_dados.append({
            'restaurante': r.nome_fantasia,
            'media': media,
            'perc_reclamacoes': perc_reclamacoes
        })

        # Dados para o Gráfico de Barras
        nomes_grafico.append(r.nome_fantasia)
        medias_grafico.append(round(media, 1))

    return render_template(
        'quality_report.html',
        relatorio=relatorio_dados,
        data_inicio=data_inicio.strftime('%Y-%m-%d'),
        data_fim=data_fim.strftime('%Y-%m-%d'),
        grafico_labels=nomes_grafico,
        grafico_data=medias_grafico
    )