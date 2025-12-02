"""
Este ficheiro contém a Application Factory 'create_app'.

É aqui que a aplicação Flask é instanciada, configurada,
e onde as extensões e blueprints são registados.
"""

from flask import Flask
from .config import Config
import datetime
from .extensions import db, migrate, bcrypt, login_manager, mail, oauth

def create_app(config_class=Config):
    """
    Função Application Factory.
    
    Cria e configura a instância da aplicação Flask.
    """
    
    # 1. Cria a instância da App
    app = Flask(__name__)
    
    app.jinja_env.globals.update(now=datetime.datetime.now)

    # 2. Carrega a Configuração
    # Carrega as configurações a partir da classe 'Config' (definida em config.py)
    app.config.from_object(config_class)

    # 3. Inicializa as Extensões
    # Passa a instância 'app' para cada extensão para ligá-las
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)

    # --- Configuração de OAuth (Google, Facebook, etc.) ---
    # Vamos registar os nossos provedores OAuth aqui.
    # Isto usa as variáveis (GOOGLE_CLIENT_ID) que carregámos em config.py
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    oauth.register(
        name='facebook',
        client_id=app.config.get('FACEBOOK_CLIENT_ID'),
        client_secret=app.config.get('FACEBOOK_CLIENT_SECRET'),
        authorize_url='https://www.facebook.com/dialog/oauth',
        access_token_url='https://graph.facebook.com/oauth/access_token',
        api_base_url='https://graph.facebook.com/',
        # 'userinfo_endpoint' diz à Authlib onde buscar os dados do perfil
        userinfo_endpoint='me?fields=id,name,email',
        client_kwargs={'scope': 'email public_profile'}
    )
    
    # (Adicionaremos o Facebook aqui mais tarde quando o configurarmos)

    # 4. Regista os Blueprints (Módulos da Aplicação)
    # Importamos e registamos os nossos "módulos" (auth, client, etc.)
    # ATENÇÃO: Fazemos a importação *dentro* da função para evitar 
    # importações circulares no arranque.
    
    from .modules.auth.routes import auth_bp
    from .modules.client.routes import client_bp
    from .modules.restaurant.routes import restaurant_bp
    # from .modules.order.routes import order_bp (ainda não criámos)

    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(client_bp, url_prefix='/perfil')
    app.register_blueprint(restaurant_bp, url_prefix='/portal')
    # app.register_blueprint(order_bp, url_prefix='/pedido')

    # Tratamento de Erro 404
    from flask import render_template
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # 5. Retorna a App pronta
    return app