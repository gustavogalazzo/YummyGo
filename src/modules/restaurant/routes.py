"""
Módulo do Restaurante (Restaurant) - Rotas

Define as rotas para /portal/ (dashboard), /portal/registar, /portal/cardapio, etc.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.modules.restaurant.forms import RestaurantRegistrationForm, CategoryForm, ProductForm, OrderStatusForm, UpdateRestaurantInfoForm
from src.extensions import db
from src.models import Restaurante, Categoria, Produto, Pedido, ItemPedido, Avaliacao
from flask import abort 
from sqlalchemy import func, case
from src.services.upload_service import upload_image
from datetime import datetime, timedelta

# 1. CRIAÇÃO DO BLUEPRINT (Isto é essencial para o __init__.py encontrar)
restaurant_bp = Blueprint('restaurant', __name__, template_folder='templates')


# 2. ROTA DO DASHBOARD (Esta é a rota que o erro diz que falta!)
@restaurant_bp.route('/')
@login_required
def dashboard():
    """
    Página principal do Portal do Restaurante.
    A URL completa será /portal/ (devido ao prefixo no __init__.py)
    """
    # Verifica se é restaurante
    if current_user.role != 'restaurante':
        flash('Acesso negado. Registe o seu restaurante primeiro.', 'danger')
        return redirect(url_for('restaurant.register')) 
        
    return render_template('dashboard.html')


# 3. Rota de Registo de Restaurante
@restaurant_bp.route('/registar', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role == 'restaurante':
        return redirect(url_for('restaurant.dashboard'))
        
    form = RestaurantRegistrationForm()
    
    if form.validate_on_submit():
        novo_restaurante = Restaurante(
            nome_fantasia=form.nome_fantasia.data,
            cnpj=form.cnpj.data,
            taxa_entrega=form.taxa_entrega.data,
            tempo_medio_entrega=form.tempo_medio_entrega.data,
            ativo=False 
        )
        
        try:
            novo_restaurante.dono = current_user
            current_user.role = 'restaurante'
            
            db.session.add(novo_restaurante)
            db.session.commit()
            
            flash('Restaurante registado com sucesso! Bem-vindo ao Portal!', 'success')
            return redirect(url_for('restaurant.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Erro ao registar o restaurante. Tente novamente.', 'danger')
            print(f"Erro ao registar restaurante: {e}")

    return render_template('register_restaurant.html', form=form)


# 4. Rota de Gestão do Cardápio
@restaurant_bp.route('/cardapio', methods=['GET', 'POST'])
@login_required
def manage_menu():
    if current_user.role != 'restaurante':
        abort(403)
        
    restaurante = current_user.restaurante
    
    category_form = CategoryForm()
    product_form = ProductForm()

    product_form.categoria_id.choices = [
        (cat.id, cat.nome) for cat in Categoria.query.filter_by(restaurante_id=restaurante.id).order_by(Categoria.nome).all()
    ]

    # Adicionar Categoria
    if category_form.submit_category.data and category_form.validate_on_submit():
        nova_categoria = Categoria(
            nome=category_form.nome.data,
            restaurante_id=restaurante.id
        )
        db.session.add(nova_categoria)
        db.session.commit()
        flash('Categoria adicionada com sucesso!', 'success')
        return redirect(url_for('restaurant.manage_menu'))

    # Adicionar Produto (COM UPLOAD)
    if product_form.submit_product.data and product_form.validate_on_submit():
        
        imagem_url = None
        if product_form.imagem.data:
            arquivo = product_form.imagem.data
            imagem_url = upload_image(arquivo) # Upload para Cloudinary

        novo_produto = Produto(
            nome=product_form.nome.data,
            descricao=product_form.descricao.data,
            preco=product_form.preco.data,
            disponivel=product_form.disponivel.data,
            categoria_id=product_form.categoria_id.data,
            restaurante_id=restaurante.id,
            imagem_url=imagem_url # Salva URL
        )
        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('restaurant.manage_menu'))

    # Listar
    categorias = Categoria.query.filter_by(restaurante_id=restaurante.id).order_by(Categoria.nome).all()
    
    return render_template(
        'manage_menu.html',
        category_form=category_form,
        product_form=product_form,
        categorias=categorias
    )


# 5. Rotas de Apagar (Categoria/Produto)
@restaurant_bp.route('/cardapio/categoria/apagar/<int:categoria_id>', methods=['POST'])
@login_required
def delete_category(categoria_id):
    if current_user.role != 'restaurante': abort(403)
    categoria = Categoria.query.get_or_404(categoria_id)
    if categoria.restaurante_id != current_user.restaurante.id: abort(403)
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoria apagada.', 'success')
    return redirect(url_for('restaurant.manage_menu'))

@restaurant_bp.route('/cardapio/produto/apagar/<int:produto_id>', methods=['POST'])
@login_required
def delete_product(produto_id):
    if current_user.role != 'restaurante': abort(403)
    produto = Produto.query.get_or_404(produto_id)
    if produto.restaurante_id != current_user.restaurante.id: abort(403)
    db.session.delete(produto)
    db.session.commit()
    flash('Produto apagado.', 'success')
    return redirect(url_for('restaurant.manage_menu'))


# 6. Rota de Edição (Categoria/Produto)
@restaurant_bp.route('/cardapio/categoria/editar/<int:categoria_id>', methods=['GET', 'POST'])
@login_required
def edit_category(categoria_id):
    categoria = Categoria.query.get_or_404(categoria_id)
    if categoria.restaurante_id != current_user.restaurante.id: abort(403)
    form = CategoryForm(obj=categoria)
    if form.validate_on_submit():
        categoria.nome = form.nome.data
        db.session.commit()
        flash('Categoria atualizada!', 'success')
        return redirect(url_for('restaurant.manage_menu'))
    return render_template('edit_item.html', form=form, title="Editar Categoria")

@restaurant_bp.route('/cardapio/produto/editar/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def edit_product(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    if produto.restaurante_id != current_user.restaurante.id: abort(403)
    form = ProductForm(obj=produto)
    form.categoria_id.choices = [(c.id, c.nome) for c in Categoria.query.filter_by(restaurante_id=current_user.restaurante.id).all()]
    
    if form.validate_on_submit():
        form.populate_obj(produto)
        if form.imagem.data:
            url = upload_image(form.imagem.data)
            if url: produto.imagem_url = url
        db.session.commit()
        flash('Produto atualizado!', 'success')
        return redirect(url_for('restaurant.manage_menu'))
    return render_template('edit_item.html', form=form, title="Editar Produto", produto=produto)


# 7. Rota de Gestão de Pedidos
STATUS_FLUXO = ['Recebido', 'Em Preparo', 'Em Rota de Entrega', 'Concluído']

@restaurant_bp.route('/pedidos', methods=['GET', 'POST'])
@login_required
def manage_orders():
    if current_user.role != 'restaurante': abort(403)
    restaurante = current_user.restaurante
    form = OrderStatusForm()
    
    pedidos = Pedido.query.filter(
        Pedido.restaurante_id == restaurante.id,
        Pedido.status.notin_(['Concluído', 'Cancelado'])
    ).order_by(Pedido.data_criacao.desc()).all()

    if form.validate_on_submit():
        pedido_id = request.form.get('pedido_id') 
        pedido = Pedido.query.get(pedido_id)
        
        if pedido and pedido.restaurante_id == restaurante.id:
            try:
                current_index = STATUS_FLUXO.index(pedido.status)
                if current_index < len(STATUS_FLUXO) - 1:
                    pedido.status = STATUS_FLUXO[current_index + 1]
                    db.session.commit()
                    flash(f"Pedido #{pedido.id} atualizado para '{pedido.status}'", 'success')
            except ValueError:
                flash('Não é possível atualizar este status.', 'danger')
        return redirect(url_for('restaurant.manage_orders'))

    return render_template('manage_orders.html', pedidos=pedidos, form=form, status_fluxo=STATUS_FLUXO)


# 8. Rota de Informações
@restaurant_bp.route('/info', methods=['GET', 'POST'])
@login_required
def manage_info():
    if current_user.role != 'restaurante': abort(403)
    restaurante = current_user.restaurante
    form = UpdateRestaurantInfoForm(obj=restaurante)
    
    if form.validate_on_submit():
        form.populate_obj(restaurante)
        if form.logo.data:
            url = upload_image(form.logo.data)
            if url: restaurante.logo_url = url
        
        db.session.commit()
        flash('Informações atualizadas!', 'success')
        return redirect(url_for('restaurant.dashboard'))

    return render_template('manage_info.html', form=form, restaurante=restaurante)


# 9. Rotas de Relatórios
@restaurant_bp.route('/relatorio', methods=['GET'])
@login_required
def orders_report():
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    
    if data_inicio_str: data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
    else: data_inicio = datetime.now() - timedelta(days=30)
    
    if data_fim_str: 
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
        data_fim = data_fim.replace(hour=23, minute=59, second=59)
    else: data_fim = datetime.now()

    resultados = db.session.query(
        Restaurante.nome_fantasia,
        func.count(Pedido.id).label('qtd_pedidos'),
        func.sum(Pedido.preco_total).label('faturamento')
    ).join(Pedido).filter(
        Pedido.data_criacao >= data_inicio,
        Pedido.data_criacao <= data_fim,
        Pedido.status != 'Cancelado'
    ).group_by(Restaurante.id).all()

    relatorio_dados = []
    total_geral_pedidos = 0
    nomes_grafico = []
    valores_grafico = []
    cores_grafico = []
    import random

    for r in resultados: total_geral_pedidos += r.qtd_pedidos

    for r in resultados:
        ticket_medio = r.faturamento / r.qtd_pedidos if r.qtd_pedidos > 0 else 0
        perc = (r.qtd_pedidos / total_geral_pedidos * 100) if total_geral_pedidos > 0 else 0
        relatorio_dados.append({'restaurante': r.nome_fantasia, 'qtd': r.qtd_pedidos, 'faturamento': r.faturamento, 'ticket_medio': ticket_medio, 'perc': perc})
        nomes_grafico.append(r.nome_fantasia)
        valores_grafico.append(r.qtd_pedidos)
        cores_grafico.append("#{:06x}".format(random.randint(0, 0xFFFFFF)))

    return render_template('orders_report.html', relatorio=relatorio_dados, total_geral=total_geral_pedidos, 
                           data_inicio=data_inicio.strftime('%Y-%m-%d'), data_fim=data_fim.strftime('%Y-%m-%d'),
                           grafico_labels=nomes_grafico, grafico_data=valores_grafico, grafico_colors=cores_grafico)


@restaurant_bp.route('/relatorio/qualidade', methods=['GET'])
@login_required
def quality_report():
    # (Mesma lógica de datas)
    data_inicio = datetime.now() - timedelta(days=30)
    data_fim = datetime.now()
    
    resultados = db.session.query(
        Restaurante.nome_fantasia,
        func.avg(Avaliacao.nota).label('media_nota'),
        func.count(Avaliacao.id).label('qtd_total'),
        func.sum(case((Avaliacao.reclamacao == True, 1), else_=0)).label('qtd_reclamacoes')
    ).join(Avaliacao).group_by(Restaurante.id).all()

    relatorio_dados = []
    nomes_grafico = []
    medias_grafico = []

    for r in resultados:
        media = float(r.media_nota) if r.media_nota else 0
        perc_reclamacoes = (r.qtd_reclamacoes / r.qtd_total * 100) if r.qtd_total > 0 else 0
        relatorio_dados.append({'restaurante': r.nome_fantasia, 'media': media, 'perc_reclamacoes': perc_reclamacoes})
        nomes_grafico.append(r.nome_fantasia)
        medias_grafico.append(round(media, 1))

    return render_template('quality_report.html', relatorio=relatorio_dados, 
                           data_inicio=data_inicio.strftime('%Y-%m-%d'), data_fim=data_fim.strftime('%Y-%m-%d'),
                           grafico_labels=nomes_grafico, grafico_data=medias_grafico)

@restaurant_bp.route('/relatorio/pagamentos', methods=['GET'])
@login_required
def payment_report():
    # (Mesma lógica de datas)
    data_inicio = datetime.now() - timedelta(days=30)
    data_fim = datetime.now()

    resultados = db.session.query(
        Pedido.tipo_pagamento,
        func.sum(Pedido.preco_total).label('valor_total'),
        func.count(Pedido.id).label('qtd')
    ).filter(
        Pedido.restaurante_id == current_user.restaurante.id,
        Pedido.status != 'Cancelado'
    ).group_by(Pedido.tipo_pagamento).all()

    faturamento_total_geral = sum([r.valor_total for r in resultados]) or 0
    relatorio_dados = []
    labels_grafico = []
    valores_grafico = []
    
    for r in resultados:
        perc = (r.valor_total / faturamento_total_geral * 100) if faturamento_total_geral > 0 else 0
        relatorio_dados.append({'tipo': r.tipo_pagamento, 'valor': r.valor_total, 'perc': perc})
        labels_grafico.append(r.tipo_pagamento)
        valores_grafico.append(r.valor_total)

    return render_template('payment_report.html', relatorio=relatorio_dados, total_geral=faturamento_total_geral,
                           data_inicio=data_inicio.strftime('%Y-%m-%d'), data_fim=data_fim.strftime('%Y-%m-%d'),
                           grafico_labels=labels_grafico, grafico_data=valores_grafico)