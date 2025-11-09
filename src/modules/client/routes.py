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

# 1. Criação do Blueprint
# 'client' é o nome interno
# 'template_folder' diz ao Flask para procurar templates nesta pasta
client_bp = Blueprint('client', __name__, template_folder='templates')


# 2. Rota Principal do Perfil (/perfil/)
@client_bp.route('/', methods=['GET', 'POST'])
@login_required # Protege esta rota!
def profile():
    """
    Mostra e processa o formulário de atualização de perfil.
    A URL completa será /perfil/ (devido ao url_prefix no __init__.py)
    """
    
    # Instancia o formulário
    form = UpdateProfileForm()

    # Se for um POST e o formulário for válido...
    if form.validate_on_submit():
        # A magia do Flask-WTF: atualiza o objeto 'current_user'
        # com os dados validados do formulário.
        current_user.nome_completo = form.nome_completo.data
        current_user.email = form.email.data.lower()
        current_user.telefone = form.telefone.data
        
        try:
            db.session.commit()
            flash('Seu perfil foi atualizado com sucesso!', 'success')
            return redirect(url_for('client.profile')) # Recarrega a página
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados. Tente novamente.', 'danger')
            print(f"Erro no perfil: {e}")

    # Se for um pedido GET (primeira vez que carrega a página):
    # Pré-preenche o formulário com os dados atuais do utilizador.
    elif request.method == 'GET':
        form.nome_completo.data = current_user.nome_completo
        form.email.data = current_user.email
        form.telefone.data = current_user.telefone

    # Renderiza o template, passando o formulário
    return render_template('profile.html', form=form)

# --- Rota de Gestão de Endereços ---
@client_bp.route('/enderecos', methods=['GET', 'POST'])
@login_required
def manage_addresses():
    """
    Lista todos os endereços (GET) e processa a 
    adição de um novo endereço (POST).
    """
    
    # Este formulário é para ADICIONAR um novo endereço
    form = AddressForm()
    
    # Lógica POST (Adicionar Endereço)
    if form.validate_on_submit():
        # Cria o novo objeto Endereco
        novo_endereco = Endereco(
            rua=form.rua.data,
            numero=form.numero.data,
            complemento=form.complemento.data,
            bairro=form.bairro.data,
            cidade=form.cidade.data,
            estado=form.estado.data.upper(),
            cep=form.cep.data,
            user_id=current_user.id  # Liga o endereço ao utilizador logado
        )
        
        # Usamos coordenadas de São Paulo (exemplos) para garantir que o campo não é NULO na DB
        novo_endereco.latitude = -23.550520  # Exemplo de Latitude
        novo_endereco.longitude = -46.633308 # Exemplo de Longitude

        try:
            db.session.add(novo_endereco)
            db.session.commit()
            flash('Endereço adicionado com sucesso!', 'success')
            return redirect(url_for('client.manage_addresses')) # Recarrega a página
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar o endereço. Tente novamente.', 'danger')
            print(f"Erro ao salvar endereço: {e}")
            
    # Lógica GET (Listar Endereços)
    # Busca todos os endereços ligados a este utilizador
    # Usamos a relação 'enderecos' que definimos no user_model!
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
    Apenas aceita POST por segurança.
    """
    
    # 1. Encontra o endereço ou dá erro 404
    endereco = Endereco.query.get_or_404(endereco_id)
    
    # 2. VERIFICAÇÃO DE SEGURANÇA CRÍTICA:
    # Garante que o endereço a ser apagado pertence ao utilizador logado.
    if endereco.user_id != current_user.id:
        abort(403) # Erro "Forbidden" (Proibido)
        
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
    A URL é /perfil/pedidos
    """
    # Usa a relação 'pedidos_cliente' que definimos no user_model
    pedidos = current_user.pedidos_cliente 
    
    return render_template(
        'order_history.html',
        pedidos=pedidos
    )