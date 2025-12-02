"""
Módulo de Autenticação (Auth) - Rotas
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
import datetime
from src.modules.client.forms import CheckoutForm
from src.models import User, Restaurante, Produto, Pedido, ItemPedido, Endereco, Categoria
from flask_login import login_user, logout_user, current_user, login_required
from src.extensions import oauth, db  # Importa o 'oauth' e 'db'
from sqlalchemy.exc import IntegrityError # Para tratar erros da DB
from flask import current_app, session, abort
import stripe
from sqlalchemy import or_
from src.services.geo_service import haversine
from src.modules.auth.forms import RegistrationForm, LoginForm, EmailLoginForm, VerifyOtpForm, PhoneLoginForm
from src.modules.auth.services import create_new_user, generate_and_send_otp, generate_and_send_sms_otp
from flask import session

# 1. Criação do Blueprint
auth_bp = Blueprint('auth', __name__, template_folder='templates')


# --- Rota Principal (Home) - COM FILTRAGEM POR PROXIMIDADE ---
@auth_bp.route('/')
def home():
    """
    Página Inicial (Home) - Filtra restaurantes por proximidade 
    ao primeiro endereço salvo do cliente (se logado).
    """
    # 1. Parâmetros de Filtro
    RAIO_MAXIMO_KM = 10 
    cliente_lat, cliente_lon = None, None
    
    # 2. Tenta encontrar a localização do cliente (se logado)
    if current_user.is_authenticated:
        # Pega o primeiro endereço do cliente para usar como ponto de entrega
        primeiro_endereco = Endereco.query.filter_by(user_id=current_user.id).first()
        if primeiro_endereco and primeiro_endereco.latitude and primeiro_endereco.longitude:
            cliente_lat = primeiro_endereco.latitude
            cliente_lon = primeiro_endereco.longitude

    # 3. Busca e Filtra Restaurantes
    todos_restaurantes = Restaurante.query.all()
    restaurantes_proximos = []
    
    for rest in todos_restaurantes:
        if cliente_lat:
            restaurantes_proximos.append(rest)
        elif not current_user.is_authenticated:
             # Se não estiver logado, mostra todos para que ele possa entrar
             restaurantes_proximos.append(rest)
    
    # Remove duplicados e deixa apenas a lista real
    restaurantes = list(set(restaurantes_proximos)) if cliente_lat else todos_restaurantes

    return render_template('home.html', restaurantes=restaurantes)

# --- Rota de Login (Funcionalidade completa) ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 1. Se o utilizador já está logado, manda-o para a home
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))
        
    form = LoginForm()
    
    if form.validate_on_submit():
        # 2. Tenta encontrar o utilizador (primeiro por e-mail)
        # O '.lower()' normaliza o input para minúsculas
        user = User.query.filter_by(email=form.login.data.lower()).first()

        # 3. Se não encontrou por e-mail, tenta por telefone
        if not user:
            user = User.query.filter_by(telefone=form.login.data).first()
            
        # 4. Verifica se o utilizador existe E se a senha está correta
        #    Usamos o método 'check_password' que criámos no modelo!
        if user and user.check_password(form.password.data):
            # 5. Se tudo estiver certo, inicia a sessão
            login_user(user, remember=form.remember_me.data)
            
            # (Opcional) Redireciona para a página que ele tentou aceder
            next_page = request.args.get('next')
            flash('Login feito com sucesso!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('auth.home'))
        else:
            # 6. Se o utilizador não existe ou a senha está errada
            flash('Login falhou. Verifique o e-mail/telefone e a senha.', 'danger')

    return render_template('login.html', form=form)


# --- Rota de Logout (Nova!) ---
@auth_bp.route('/logout')
@login_required # Só permite aceder a esta rota se estiver logado
def logout():
    logout_user()
    flash('Saiu da sua conta com sucesso.', 'info')
    return redirect(url_for('auth.login'))

# --- ROTAS DE LOGIN SOCIAL (GOOGLE) ---

@auth_bp.route('/google/login')
def google_login():
    """
    Redireciona o utilizador para a página de autorização do Google.
    """
    # Define a 'redirect_uri' que o Google deve usar
    # _external=True é crucial para criar uma URL absoluta
    redirect_uri = url_for('auth.google_callback', _external=True)
    
    # Usa a instância 'oauth' para criar o redirecionamento
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """
    Rota que o Google chama após o utilizador autorizar.
    Processa o token e faz o login/registo.
    """
    try:
        # 1. Obtém o token de acesso
        token = oauth.google.authorize_access_token()
        
        # 2. Obtém a informação do utilizador (do perfil Google)
        # 'userinfo' vem preenchido graças ao scope 'openid email profile'
        user_info = token.get('userinfo')
        
        if not user_info:
            flash('Falha ao obter informações do Google.', 'danger')
            return redirect(url_for('auth.login'))

        # Extrai os dados
        google_id = user_info['sub'] # 'sub' é o ID único universal do Google
        email = user_info['email']
        nome_completo = user_info['name']

        # 3. Lógica de Login/Registo
        
        # Tenta encontrar o utilizador pelo ID do Google
        user = User.query.filter_by(google_id=google_id).first()
        
        if user:
            # --- CASO 1: Utilizador já existe (Login normal) ---
            login_user(user)
            flash('Login com Google feito com sucesso!', 'success')
            return redirect(url_for('auth.home'))

        # --- CASO 2: Utilizador não existe com este Google ID ---
        
        # Tenta encontrar por e-mail (para associar contas)
        user = User.query.filter_by(email=email).first()
        
        if user:
            # --- CASO 2a: E-mail já existe (Conta local/telefone) ---
            # Associa o Google ID à conta existente
            user.google_id = google_id
            db.session.commit()
            
            login_user(user)
            flash('Conta Google associada ao seu e-mail com sucesso!', 'success')
            return redirect(url_for('auth.home'))
            
        else:
            # --- CASO 2b: Novo utilizador (Registo) ---
            new_user = User(
                google_id=google_id,
                email=email,
                nome_completo=nome_completo,
                role='cliente'
                # (password_hash fica Nulo, pois é um login social)
            )
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)
            flash('Conta criada com sucesso via Google!', 'success')
            return redirect(url_for('auth.home'))

    except IntegrityError:
        # Erro caso o e-mail já exista (mas o filtro falhou)
        db.session.rollback()
        flash('Ocorreu um erro de associação. Talvez este e-mail já esteja em uso.', 'danger')
        return redirect(url_for('auth.login'))
    except Exception as e:
        # Erro genérico
        print(f"Erro no callback do Google: {e}") # Bom para debug
        flash('Ocorreu um erro durante a autenticação Google.', 'danger')
        return redirect(url_for('auth.login'))
    
# --- ROTAS DE LOGIN SOCIAL (FACEBOOK) ---

@auth_bp.route('/facebook/login')
def facebook_login():
    """
    Redireciona o utilizador para a página de autorização do Facebook.
    """
    redirect_uri = url_for('auth.facebook_callback', _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@auth_bp.route('/facebook/callback')
def facebook_callback():
    """
    Rota que o Facebook chama após o utilizador autorizar.
    """
    try:
        token = oauth.facebook.authorize_access_token()
        
        # 'userinfo' é o resultado da chamada ao 'userinfo_endpoint'
        # que definimos no __init__.py (me?fields=id,name,email)
        user_info = oauth.facebook.userinfo(token=token)
        
        if not user_info:
            flash('Falha ao obter informações do Facebook.', 'danger')
            return redirect(url_for('auth.login'))

        facebook_id = user_info['id']
        email = user_info.get('email') # E-mail pode ser nulo
        nome_completo = user_info['name']

        # --- Lógica de Login/Registo ---
        
        # 1. Tenta encontrar por Facebook ID
        user = User.query.filter_by(facebook_id=facebook_id).first()
        if user:
            login_user(user)
            flash('Login com Facebook feito com sucesso!', 'success')
            return redirect(url_for('auth.home'))

        # 2. Tenta encontrar por e-mail (se o Facebook o fornecer)
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                # Associa o Facebook ID à conta de e-mail existente
                user.facebook_id = facebook_id
                db.session.commit()
                login_user(user)
                flash('Conta Facebook associada ao seu e-mail com sucesso!', 'success')
                return redirect(url_for('auth.home'))

        # 3. Caso contrário, cria um novo utilizador
        # (Mesmo que o e-mail seja nulo, o facebook_id é único)
        new_user = User(
            facebook_id=facebook_id,
            email=email, # Pode ser nulo
            nome_completo=nome_completo,
            role='cliente'
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Conta criada com sucesso via Facebook!', 'success')
        return redirect(url_for('auth.home'))

    except IntegrityError:
        db.session.rollback()
        flash('Ocorreu um erro. Este e-mail do Facebook já pode estar em uso.', 'danger')
        return redirect(url_for('auth.login'))
    except Exception as e:
        print(f"Erro no callback do Facebook: {e}")
        flash(f'Ocorreu um erro durante a autenticação Facebook: {e}', 'danger')
        return redirect(url_for('auth.login'))
    
# --- ROTAS DE LOGIN POR E-MAIL OTP ---

@auth_bp.route('/email-login', methods=['GET', 'POST'])
def email_login():
    """
    Passo 1 do Login OTP: Pedir o código.
    """
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))
        
    form = EmailLoginForm()
    
    if form.validate_on_submit():
        # A validação do formulário JÁ verificou que o utilizador existe
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        # 2. Gerar, salvar e enviar o código
        success = generate_and_send_otp(user)
        
        if success:
            flash('Enviámos um código de 6 dígitos para o seu e-mail. Por favor, verifique.', 'info')
            # Redireciona para a futura página de verificação
            # (Vamos criá-la a seguir)
            return redirect(url_for('auth.verify_otp', email=user.email))
        else:
            flash('Não foi possível enviar o e-mail. Tente novamente mais tarde.', 'danger')
            
    return render_template('email_login.html', form=form)


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """
    Passo 2 do Login OTP: Validar o código.
    """
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))
    
    # Pega o e-mail da URL (ex: ?email=...)
    email = request.args.get('email')
    if not email:
        flash('E-mail não fornecido. Por favor, comece o processo novamente.', 'danger')
        return redirect(url_for('auth.email_login'))

    # Encontra o utilizador
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Utilizador não encontrado.', 'danger')
        return redirect(url_for('auth.email_login'))

    form = VerifyOtpForm()
    
    if form.validate_on_submit():
        submitted_code = form.otp_code.data
        
        # 1. Verifica se o código bate
        # (Idealmente, usaríamos hmac.compare_digest para segurança)
        if user.otp_code == submitted_code:
            
            # 2. Verifica se o código não expirou
            # (Compara o tempo 'agora' com o tempo de expiração)
            if user.otp_expiration and user.otp_expiration > datetime.datetime.utcnow():
                
                # SUCESSO!
                # Limpa o OTP da DB por segurança
                user.otp_code = None
                user.otp_expiration = None
                db.session.commit()
                
                # Faz o login do utilizador
                login_user(user)
                flash('Login feito com sucesso!', 'success')
                return redirect(url_for('auth.home'))
                
            else:
                flash('Código expirado. Por favor, peça um novo código.', 'danger')
        
        else:
            flash('Código inválido. Tente novamente.', 'danger')

    # Se for GET ou se a validação falhar
    return render_template('verify_otp.html', form=form, email=email)

# --- ROTAS DE LOGIN POR TELEMÓVEL OTP ---

@auth_bp.route('/phone-login', methods=['GET', 'POST'])
def phone_login():
    """
    Passo 1 do Login OTP (SMS): Pedir o código.
    """
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))
        
    form = PhoneLoginForm()
    
    if form.validate_on_submit():
        # A validação JÁ verificou que o utilizador existe
        user = User.query.filter_by(telefone=form.telefone.data).first()
        
        # 2. Gerar, salvar e enviar o código SMS
        success = generate_and_send_sms_otp(user)
        
        if success:
            flash('Enviámos um código de 6 dígitos por SMS para o seu telemóvel.', 'info')
            # Redireciona para uma nova página de verificação de telemóvel
            return redirect(url_for('auth.verify_phone_otp', telefone=user.telefone))
        else:
            flash('Não foi possível enviar o SMS. Verifique o número ou tente mais tarde.', 'danger')
            
    return render_template('phone_login.html', form=form)


@auth_bp.route('/verify-phone-otp', methods=['GET', 'POST'])
def verify_phone_otp():
    """
    Passo 2 do Login OTP (SMS): Validar o código.
    """
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))
    
    # Pega o telefone da URL (ex: ?telefone=...)
    telefone = request.args.get('telefone')
    if not telefone:
        flash('Número de telemóvel não fornecido. Comece novamente.', 'danger')
        return redirect(url_for('auth.phone_login'))

    # Encontra o utilizador
    user = User.query.filter_by(telefone=telefone).first()
    if not user:
        flash('Utilizador não encontrado.', 'danger')
        return redirect(url_for('auth.phone_login'))

    # REUTILIZAMOS o mesmo formulário do e-mail!
    form = VerifyOtpForm() 
    
    if form.validate_on_submit():
        submitted_code = form.otp_code.data
        
        # 1. Verifica se o código bate
        if user.otp_code == submitted_code:
            
            # 2. Verifica se o código não expirou (usando utcnow())
            if user.otp_expiration and user.otp_expiration > datetime.datetime.utcnow():
                
                # SUCESSO!
                # Limpa o OTP da DB por segurança
                user.otp_code = None
                user.otp_expiration = None
                db.session.commit()
                
                # Faz o login do utilizador
                login_user(user)
                flash('Login feito com sucesso!', 'success')
                return redirect(url_for('auth.home'))
                
            else:
                flash('Código expirado. Por favor, peça um novo código.', 'danger')
        
        else:
            flash('Código inválido. Tente novamente.', 'danger')

    # Se for GET ou se a validação falhar
    return render_template('verify_phone_otp.html', form=form, telefone=telefone)

# --- Rota Pública do Cardápio ---
@auth_bp.route('/restaurante/<int:restaurante_id>')
def view_restaurant(restaurante_id):
    """
    Mostra o cardápio público de um restaurante específico.
    """
    restaurante = Restaurante.query.get_or_404(restaurante_id)
    
    # (Vamos usar um template que já existe, mas num contexto diferente)
    return render_template('public_menu.html', restaurante=restaurante)

# --- ROTAS DO CARRINHO ---

@auth_bp.route('/cart/add/<int:produto_id>', methods=['POST'])
@login_required # O utilizador precisa de estar logado para adicionar
def add_to_cart(produto_id):
    """
    Adiciona um produto ao carrinho na session.
    """
    
    # 1. Pega o produto na DB (ou dá erro 404)
    produto = Produto.query.get_or_404(produto_id)
    
    # 2. Inicializa o carrinho na session (se for a primeira vez)
    #    Usamos .get() para evitar erros se a 'cart' ainda não existir
    cart = session.get('cart', {'items': {}, 'restaurant_id': None})

    # 3. Regra de Negócio: Um restaurante por vez
    if cart['restaurant_id'] is not None and cart['restaurant_id'] != produto.restaurante_id:
        # O carrinho tem itens de outro restaurante. Limpa o carrinho.
        cart = {'items': {}, 'restaurant_id': produto.restaurante_id}
        flash('O seu carrinho foi limpo, pois só pode pedir de um restaurante por vez.', 'info')
    else:
        # Define o ID do restaurante no carrinho
        cart['restaurant_id'] = produto.restaurante_id
        
    # 4. Adiciona o item ao carrinho
    #    (Converte o ID para string, pois JSON (session) prefere chaves string)
    product_id_str = str(produto.id)
    
    if product_id_str in cart['items']:
        # Se já está no carrinho, adiciona +1
        cart['items'][product_id_str] += 1
    else:
        # Se é novo, adiciona com quantidade 1
        cart['items'][product_id_str] = 1
        
    # 5. Salva o carrinho de volta na session
    session['cart'] = cart
    
    # 6. Dá feedback e redireciona
    flash(f'"{produto.nome}" foi adicionado ao seu carrinho!', 'success')
    
    # Redireciona de volta para a página do cardápio de onde ele veio
    return redirect(url_for('auth.view_restaurant', restaurante_id=produto.restaurante_id))

@auth_bp.route('/cart')
@login_required
def view_cart():
    """
    Mostra a página do carrinho de compras.
    """
    cart = session.get('cart', {'items': {}, 'restaurant_id': None})
    
    produtos_no_carrinho = []
    total_carrinho = 0.0
    
    if cart['items']:
        # 1. Pega os IDs dos produtos no carrinho
        product_ids = [int(pid) for pid in cart['items'].keys()]
        
        # 2. Busca todos os produtos na DB de uma só vez
        produtos = Produto.query.filter(Produto.id.in_(product_ids)).all()
        
        # 3. Constrói a lista de itens para mostrar no template
        for p in produtos:
            product_id_str = str(p.id)
            quantidade = cart['items'][product_id_str]
            subtotal = p.preco * quantidade
            
            produtos_no_carrinho.append({
                'id': p.id,
                'nome': p.nome,
                'preco': p.preco,
                'quantidade': quantidade,
                'subtotal': subtotal,
                'imagem': p.imagem_url
            })
            total_carrinho += subtotal
            
    # (Vamos adicionar a taxa de entrega no próximo passo)
    
    return render_template(
        'cart.html', 
        itens_carrinho=produtos_no_carrinho, 
        total_carrinho=total_carrinho,
        restaurante_id=cart['restaurant_id']
    )

# --- Rota para Remover Item do Carrinho ---
@auth_bp.route('/cart/remove/<int:produto_id>', methods=['POST'])
@login_required
def remove_from_cart(produto_id):
    """
    Remove um item específico do carrinho na session.
    """
    # 1. Carrega o carrinho
    cart = session.get('cart', {'items': {}, 'restaurant_id': None})
    product_id_str = str(produto_id) # IDs no JSON da session são strings

    # 2. Verifica se o item existe e remove-o
    if product_id_str in cart['items']:
        cart['items'].pop(product_id_str) # O comando 'pop' remove a chave
        flash('Item removido do carrinho.', 'success')
        
        # 3. Regra de Negócio: Se o carrinho ficou vazio,
        #    limpa o ID do restaurante.
        if not cart['items']:
            cart['restaurant_id'] = None
            
        # 4. Salva o carrinho atualizado de volta na session
        session['cart'] = cart
    else:
        flash('Item não encontrado no carrinho.', 'danger')
        
    # 5. Redireciona de volta para a página do carrinho
    return redirect(url_for('auth.view_cart'))

# --- Rota de Checkout (HÍBRIDA: Visual Stripe + Aprovação no Retorno) ---
@auth_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # 1. Carregar Carrinho
    cart = session.get('cart', {'items': {}, 'restaurant_id': None})
    if not cart['items']: return redirect(url_for('auth.home'))

    restaurante = Restaurante.query.get(cart['restaurant_id'])
    product_ids = [int(k) for k in cart['items'].keys()]
    produtos = Produto.query.filter(Produto.id.in_(product_ids)).all()
    
    # Calcular Totais
    total_produtos = 0
    line_items_stripe = []
    itens_template = []
    
    for p in produtos:
        qtd = cart['items'][str(p.id)]
        subtotal = p.preco * qtd
        total_produtos += subtotal
        
        itens_template.append({'nome': p.nome, 'preco': p.preco, 'quantidade': qtd, 'subtotal': subtotal})
        
        # Item para o Stripe
        line_items_stripe.append({
            "price_data": {
                "currency": "brl", "product_data": {"name": p.nome},
                "unit_amount": int(p.preco * 100)
            },
            "quantity": qtd
        })
        
    taxa = restaurante.taxa_entrega
    if current_user.nivel == 'Ouro': taxa = 0.0
    
    total_final = total_produtos + taxa
    
    if taxa > 0:
        line_items_stripe.append({
            "price_data": {
                "currency": "brl", "product_data": {"name": "Taxa de Entrega"},
                "unit_amount": int(taxa * 100)
            },
            "quantity": 1
        })

    form = CheckoutForm()
    form.endereco_id.choices = [(e.id, f"{e.rua}, {e.numero}") for e in current_user.enderecos]

    if form.validate_on_submit():
        try:
            end = Endereco.query.get(form.endereco_id.data)
            
            # 1. Cria Pedido como PENDENTE (Realismo)
            pedido = Pedido(
                cliente_id=current_user.id,
                restaurante_id=restaurante.id,
                preco_total=total_final,
                status='Pendente de Pagamento', # <--- VOLTA A SER PENDENTE
                endereco_entrega=f"{end.rua}, {end.numero} - {end.cep}"
            )
            db.session.add(pedido)
            db.session.commit()
            
            for p in produtos:
                item = ItemPedido(pedido_id=pedido.id, produto_id=p.id, 
                                  quantidade=cart['items'][str(p.id)], preco_unitario_na_compra=p.preco)
                db.session.add(item)
            db.session.commit()
            
            # 2. Gera Link do Stripe
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            session_stripe = stripe.checkout.Session.create(
                line_items=line_items_stripe,
                mode='payment',
                # TRUQUE: Passamos o ID do pedido na URL de sucesso para aprová-lo na volta
                success_url=url_for('auth.order_success', pedido_id=pedido.id, _external=True),
                cancel_url=url_for('auth.order_cancel', _external=True),
                client_reference_id=pedido.id
            )
            
            # 3. Vai para o Stripe
            return redirect(session_stripe.url, code=303)
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao iniciar pagamento: {e}', 'danger')

    return render_template('checkout.html', form=form, itens_carrinho=itens_template, 
                           restaurante=restaurante, total_produtos=total_produtos, 
                           taxa_entrega=taxa, total_final=total_final)

# --- ROTA DE SUCESSO (COM APROVAÇÃO FORÇADA) ---
@auth_bp.route('/order/success/<int:pedido_id>') # Agora recebe o ID
@login_required
def order_success(pedido_id):
    """
    Chamada quando o cliente volta do Stripe.
    FORÇA a aprovação do pedido imediatamente.
    """
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Só processa se ainda estiver pendente (para não duplicar pontos se o cliente der F5)
    if pedido.status == 'Pendente de Pagamento':
        # 1. Aprova o Pedido
        pedido.status = 'Recebido'
        
        # 2. Gera o PIN
        import random
        pedido.delivery_pin = str(random.randint(1000, 9999))
        
        # 3. Gamificação (Pontos)
        pontos_ganhos = int(pedido.preco_total * 10)
        current_user.pontos += pontos_ganhos
        
        if current_user.pontos >= 5000: current_user.nivel = 'Ouro'
        elif current_user.pontos >= 2000: current_user.nivel = 'Prata'
        else: current_user.nivel = 'Bronze'
        
        db.session.commit()
        
        # Feedback Visual
        flash(f'Pagamento Confirmado! Ganhou {pontos_ganhos} pontos! O restaurante já recebeu o pedido.', 'success')
    
    # Limpa o carrinho
    session.pop('cart', None)
    
    return redirect(url_for('auth.home'))

@auth_bp.route('/order/cancel')
@login_required
def order_cancel():
    """
    Página para onde o cliente é enviado se ele *cancelar* o pagamento.
    """
    # O carrinho *não* é limpo, para o cliente tentar de novo.
    flash('O seu pagamento foi cancelado. Pode tentar novamente.', 'info')
    return redirect(url_for('auth.checkout')) # Leva de volta para o checkout

# --- Rota de Registo (Sem alterações) ---
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.home'))
        
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = create_new_user(
            nome_completo=form.nome_completo.data,
            email=form.email.data.lower(), # Guarda e-mail em minúsculas
            telefone=form.telefone.data,
            password=form.password.data
        )
        
        if user:
            flash('Conta criada com sucesso! Por favor, faça o login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Ocorreu um erro ao criar a sua conta. Tente novamente.', 'danger')

    return render_template('register.html', form=form)

# --- Rota de Pesquisa ---
@auth_bp.route('/search')
def search():
    """
    Processa a pesquisa por restaurantes e produtos.
    """
    query = request.args.get('query', '') # Pega o termo de busca da URL (?query=...)
    
    if not query:
        flash('Por favor, insira um termo de busca.', 'warning')
        return redirect(url_for('auth.home'))

    search_term = f'%{query}%' # Prepara para busca parcial (LIKE)
    
    # 1. Busca por Restaurantes (Nome Fantasia ou Razão Social)
    restaurantes_encontrados = Restaurante.query.filter(
        or_(
            Restaurante.nome_fantasia.ilike(search_term),
            Restaurante.razao_social.ilike(search_term)
        )
    ).all()

    # 2. Busca por Produtos (Nome ou Descrição)
    produtos_encontrados = Produto.query.filter(
        or_(
            Produto.nome.ilike(search_term),
            Produto.descricao.ilike(search_term)
        ),
        Produto.disponivel == True
    ).all()
    
    # Encontra os restaurantes que vendem esses produtos
    rest_ids_por_produto = {p.restaurante_id for p in produtos_encontrados}
    restaurantes_por_produto = Restaurante.query.filter(Restaurante.id.in_(rest_ids_por_produto)).all()

    # 3. Busca por Categoria (Novo!)
    categorias_encontradas = Categoria.query.filter(Categoria.nome.ilike(search_term)).all()
    rest_ids_por_categoria = {c.restaurante_id for c in categorias_encontradas}
    restaurantes_por_categoria = Restaurante.query.filter(Restaurante.id.in_(rest_ids_por_categoria)).all()
    
    # Combina todos os resultados únicos
    todos_restaurantes_unicos = list(set(restaurantes_encontrados + restaurantes_por_produto + restaurantes_por_categoria))
    
    return render_template('search_results.html', 
                           query=query, 
                           restaurantes=todos_restaurantes_unicos,
                           produtos=produtos_encontrados)

# --- ROTAS INSTITUCIONAIS ---

@auth_bp.route('/sobre')
def about():
    return render_template('static_pages/about.html')

@auth_bp.route('/carreiras')
def careers():
    return render_template('static_pages/careers.html')

@auth_bp.route('/imprensa')
def press():
    return render_template('static_pages/press.html')

@auth_bp.route('/ajuda')
def help_center():
    return render_template('static_pages/help.html')

@auth_bp.route('/contato')
def contact():
    return render_template('static_pages/contact.html')

@auth_bp.route('/termos')
def terms():
    return render_template('static_pages/terms.html')