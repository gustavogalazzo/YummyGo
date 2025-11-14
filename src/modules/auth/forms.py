"""
Formulários do Módulo de Autenticação (Flask-WTF)
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from src.models import User

class RegistrationForm(FlaskForm):
    """
    Formulário de Registo de novo utilizador.
    """
    nome_completo = StringField('Nome Completo', 
                                validators=[DataRequired(), Length(min=3, max=100)])
    
    email = StringField('E-mail',
                        validators=[DataRequired(), Email()])
    
    telefone = StringField('Telefone',
                           validators=[DataRequired(), Length(min=9, max=20)]) # Validação simples
    def validate_telefone(self, telefone):
        """Verifica se o telefone já existe E se o formato é internacional."""
        
        # 1. Checagem de Existência (Lógica existente)
        user = User.query.filter_by(telefone=telefone.data).first()
        if user:
            raise ValidationError('Este telefone já está registado. Por favor, escolha outro.')
            
        # 2. Checagem de Formato (Nova!)
        if not telefone.data.startswith('+'):
            raise ValidationError('Por favor, inclua o código internacional do país (ex: +55). O formato deve ser +DDDnúmero.')
    
    password = PasswordField('Senha', 
                             validators=[DataRequired(), Length(min=6)])
    
    confirm_password = PasswordField('Confirmar Senha',
                                     validators=[DataRequired(), EqualTo('password', message='As senhas devem coincidir.')])
    
    submit = SubmitField('Criar Conta')

    # --- Validadores Personalizados ---
    
    def validate_email(self, email):
        """Verifica se o e-mail já existe na base de dados."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este e-mail já está registado. Por favor, escolha outro.')

    def validate_telefone(self, telefone):
        """Verifica se o telefone já existe na base de dados."""
        user = User.query.filter_by(telefone=telefone.data).first()
        if user:
            raise ValidationError('Este telefone já está registado. Por favor, escolha outro.')
        
class LoginForm(FlaskForm):
    """
    Formulário de Login.
    O utilizador pode usar e-mail OU telefone.
    """
    # Usamos 'login' como nome do campo genérico
    login = StringField('E-mail ou Telefone',
                        validators=[DataRequired()])
    
    password = PasswordField('Senha',
                             validators=[DataRequired()])
    
    remember_me = BooleanField('Lembrar-me') # Checkbox "Lembrar-me"
    
    submit = SubmitField('Entrar')

class EmailLoginForm(FlaskForm):
    """
    Formulário para pedir um código OTP por e-mail.
    """
    email = StringField('E-mail',
                        validators=[DataRequired(), Email()])
    
    submit = SubmitField('Enviar-me o código')

    def validate_email(self, email):
        """Verifica se o e-mail JÁ EXISTE na base de dados."""
        user = User.query.filter_by(email=email.data.lower()).first()
        if not user:
            # Neste fluxo, SÓ queremos enviar o código se a conta existir.
            # (Podemos mudar isto para permitir registo por OTP mais tarde)
            raise ValidationError('Nenhuma conta encontrada com este e-mail.')
        
class VerifyOtpForm(FlaskForm):
    """
    Formulário para verificar o código OTP de 6 dígitos.
    """
    otp_code = StringField('Código de 6 dígitos',
                           validators=[DataRequired(), Length(min=6, max=6)])
    
    submit = SubmitField('Verificar e Entrar')

class PhoneLoginForm(FlaskForm):
    """
    Formulário para pedir um código OTP por telemóvel/telefone.
    """
    telefone = StringField('Número de Telemóvel',
                           validators=[DataRequired(), Length(min=9, max=20)])
    
    submit = SubmitField('Enviar-me o código')

    def validate_telefone(self, telefone):
        """Verifica se o telefone JÁ EXISTE na base de dados."""
        # NOTA: Assumimos que o telefone na DB está num formato
        # que o utilizador consegue digitar (ex: 551199999...)
        user = User.query.filter_by(telefone=telefone.data).first()
        if not user:
            raise ValidationError('Nenhum conta encontrada com este número.')