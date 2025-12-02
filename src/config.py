import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente dos ficheiros .env e .flaskenv
# (Isto é necessário para o ambiente local/desenvolvimento)
load_dotenv()

class Config:
    """
    Configurações base da aplicação.
    Carrega variáveis do ficheiro .env para o ambiente local e usa as variáveis
    do sistema (os.environ) para o ambiente de produção (Render).
    """
    
    # --- Configurações Core ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'voce-deve-mudar-isto'
    
    # --- Configurações da Base de Dados ---
    # Para Produção/Render: Lê a variável 'DATABASE_URL' fornecida pelo ambiente.
    # Para Desenvolvimento: Usa o SQLite local como fallback.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    if SQLALCHEMY_DATABASE_URI is None:
        # Fallback para SQLite local
        SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'
        
    # Desativa uma funcionalidade do SQLAlchemy que não usamos e emite avisos
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- Configurações de APIs Externas (carregadas do os.environ) ---
    
    # Google (OAuth)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # Facebook (OAuth)
    FACEBOOK_CLIENT_ID = os.environ.get('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET = os.environ.get('FACEBOOK_CLIENT_SECRET')

    # Stripe (Pagamentos)
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Twilio (SMS OTP)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # E-mail (OTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'

    # Geolocalização
    OPENCAGE_API_KEY = os.environ.get('OPENCAGE_API_KEY')

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')