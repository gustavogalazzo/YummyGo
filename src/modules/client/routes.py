"""
Módulo do Cliente (Client) - Rotas

Define as rotas para /perfil, /perfil/enderecos, /perfil/pedidos, etc.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.modules.client.forms import UpdateProfileForm
from src.extensions import db
from src.modules.client.forms import UpdateProfileForm, AddressForm
from src.models import User, Endereco, Pedido
from flask import abort
from src.services.geo_service import get_coordinates
from io import BytesIO
from xhtml2pdf import pisa
from flask import make_response

# 1. Criação do Blueprint
client_bp = Blueprint('client', __name__, template_folder='templates')


# 2. Rota Principal do Perfil (/perfil/)
@client_bp.route('/', methods=['GET', 'POST'])
@login_required 
def profile():
    """
    Mostra e processa o formulário de atualização de perfil.
    """
    form = UpdateProfileForm()

    if form.validate_on_submit():
        current_user.nome_completo = form.nome_completo.data
        current_user.email = form.email.data.lower()
        current_user.telefone = form.telefone.data
        
        try:
            db.session.commit()
            flash('Seu perfil foi atualizado com sucesso!', 'success')
            return redirect(url_for('client.profile')) 
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados. Tente novamente.', 'danger')
            print(f"Erro no perfil: {e}")

    elif request.method == 'GET':
        form.nome_completo.data = current_user.nome_completo
        form.email.data = current_user.email
        form.telefone.data = current_user.telefone

    return render_template('profile.html', form=form)

# --- Rota de Gestão de Endereços ---
@client_bp.route('/enderecos', methods=['GET', 'POST'])
@login_required
def manage_addresses():
    """
    Lista todos os endereços (GET) e processa a 
    adição de um novo endereço (POST).
    """
    form = AddressForm()
    
    if form.validate_on_submit():
        novo_endereco = Endereco(
            rua=form.rua.data,
            numero=form.numero.data,
            complemento=form.complemento.data,
            bairro=form.bairro.data,
            cidade=form.cidade.data,
            estado=form.estado.data.upper(),
            cep=form.cep.data,
            user_id=current_user.id 
        )
        
        # PASSO 4: SIMULAÇÃO DA API DE GEOCODING (ou chamada real se tiver a chave)
        # Se tiver a chave configurada, use: lat, lon = get_coordinates(f"{form.rua.data}, ...")
        # Caso contrário, usamos a simulação para não quebrar o código:
        novo_endereco.latitude = -23.550520 
        novo_endereco.longitude = -46.633308

        try:
            db.session.add(novo_endereco)
            db.session.commit()
            flash('Endereço adicionado com sucesso!', 'success')
            return redirect(url_for('client.manage_addresses')) 
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar o endereço. Tente novamente.', 'danger')
            print(f"Erro ao salvar endereço: {e}")
            
    enderecos_do_utilizador = current_user.enderecos
    
    return render_template(
        'manage_addresses.html', 
        form=form, 
        enderecos=enderecos_do_utilizador
    )


# --- Rota para Apagar Endereço ---
@client_bp.route('/enderecos/apagar/<int:endereco_id>', methods=['POST'])
@login_required
def delete_address(endereco_id):
    """
    Apaga um endereço específico.
    """
    endereco = Endereco.query.get_or_404(endereco_id)
    
    if endereco.user_id != current_user.id:
        abort(403) 
        
    try:
        db.session.delete(endereco)
        db.session.commit()
        flash('Endereço apagado com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao apagar o endereço.', 'danger')
        print(f"Erro ao apagar endereço: {e}")
        
    return redirect(url_for('client.manage_addresses'))

# --- Rota de Histórico de Pedidos do Cliente ---
@client_bp.route('/pedidos')
@login_required
def order_history():
    """
    Mostra todos os pedidos feitos pelo cliente.
    """
    pedidos = current_user.pedidos_cliente 
    
    return render_template(
        'order_history.html',
        pedidos=pedidos
    )

# --- Rota para Acompanhar Pedido (CORRIGIDA A INDENTAÇÃO) ---
@client_bp.route('/pedido/<int:pedido_id>')
@login_required
def track_order(pedido_id):
    """
    Tela detalhada de acompanhamento de um pedido específico.
    """
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Segurança: Garante que o pedido pertence ao cliente logado
    if pedido.cliente_id != current_user.id:
        abort(403)
        
    # Definição simples dos passos para a barra de progresso
    steps = ['Recebido', 'Em Preparo', 'Em Rota de Entrega', 'Concluído']
    
    # Calcula em qual passo estamos (0 a 3)
    try:
        current_step_index = steps.index(pedido.status)
    except ValueError:
        current_step_index = 0 # Fallback se o status for estranho
        
    return render_template(
        'track_order.html', 
        pedido=pedido, 
        steps=steps,
        current_step_index=current_step_index
    )

@client_bp.route('/pedido/<int:pedido_id>/pdf')
@login_required
def download_invoice(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Segurança: Só o dono ou o restaurante podem ver
    if pedido.cliente_id != current_user.id and current_user.role != 'restaurante':
        abort(403)

    # Renderiza o HTML da nota
    html = render_template('invoice_pdf.html', pedido=pedido)
    
    # Converte para PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = make_response(result.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Nota_Fiscal_{pedido.id}.pdf'
        return response
    
    return "Erro ao gerar PDF", 500