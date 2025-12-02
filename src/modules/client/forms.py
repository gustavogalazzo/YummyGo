"""
Formulários do Módulo do Cliente (Flask-WTF)
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from src.models import User
from flask_login import current_user
from wtforms import RadioField

class UpdateProfileForm(FlaskForm):
    """
    Formulário para o utilizador atualizar os seus dados.
    (Não inclui senha, isso será um formulário separado)
    """
    nome_completo = StringField('Nome Completo',
                                validators=[DataRequired(), Length(min=3, max=100)])
    
    email = StringField('E-mail',
                        validators=[DataRequired(), Email()])
    
    telefone = StringField('Telefone',
                           validators=[DataRequired(), Length(min=9, max=20)])
    
    submit = SubmitField('Salvar Alterações')

    
    def validate_email(self, email):
        """
        Validação inteligente:
        Verifica se o e-mail novo (email.data) já está a ser
        usado por OUTRO utilizador.
        """
        if email.data != current_user.email: # Só valida se o e-mail mudou
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Este e-mail já está registado. Use outro.')

    def validate_telefone(self, telefone):
        """
        Validação inteligente:
        Verifica se o telefone novo (telefone.data) já está a ser
        usado por OUTRO utilizador.
        """
        if telefone.data != current_user.telefone: # Só valida se o n. mudou
            user = User.query.filter_by(telefone=telefone.data).first()
            if user:
                raise ValidationError('Este telemóvel já está registado. Use outro.')
            
class AddressForm(FlaskForm):
    """
    Formulário para adicionar ou editar um Endereço.
    """
    rua = StringField('Rua / Logradouro', validators=[DataRequired(), Length(max=255)])
    numero = StringField('Número', validators=[DataRequired(), Length(max=20)])
    complemento = StringField('Complemento (Opcional)', validators=[Length(max=100)])
    bairro = StringField('Bairro', validators=[DataRequired(), Length(max=100)])
    cidade = StringField('Cidade', validators=[DataRequired(), Length(max=100)])
    estado = StringField('Estado (UF)', validators=[DataRequired(), Length(min=2, max=2)])
    cep = StringField('CEP', validators=[DataRequired(), Length(min=8, max=10)])
    
    submit = SubmitField('Salvar Endereço')

class CheckoutForm(FlaskForm):
    """
    Formulário para o checkout.
    Permite ao utilizador selecionar um endereço de entrega.
    """
    # Vamos preencher as 'choices' (opções) dinamicamente na rota
    endereco_id = RadioField('Selecione o Endereço de Entrega', 
                             coerce=int, 
                             validators=[DataRequired()])
    
    submit = SubmitField('Confirmar Pedido e Ir para Pagamento')

    
class ReviewForm(FlaskForm):
    """
    Formulário para avaliar um pedido concluído.
    """
    nota = SelectField('Nota', choices=[
        ('5', '5 Estrelas - Excelente'),
        ('4', '4 Estrelas - Bom'),
        ('3', '3 Estrelas - Razoável'),
        ('2', '2 Estrelas - Ruim'),
        ('1', '1 Estrela - Péssimo')
    ], validators=[DataRequired()])
    
    comentario = TextAreaField('Comentário (Opcional)', validators=[Length(max=500)])
    
    submit = SubmitField('Enviar Avaliação')