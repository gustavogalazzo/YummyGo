from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed 
from wtforms import StringField, SubmitField, IntegerField, FloatField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, ValidationError
from src.models import Restaurante

class RestaurantRegistrationForm(FlaskForm):
   
    nome_fantasia = StringField('Nome do Restaurante (Nome Fantasia)', 
                                validators=[DataRequired(), Length(max=100)])
    
    cnpj = StringField('CNPJ (apenas números)', 
                       validators=[DataRequired(), Length(min=14, max=14)])
    
    taxa_entrega = FloatField('Taxa de Entrega (ex: 5.50)', 
                              validators=[DataRequired()])
    
    tempo_medio_entrega = IntegerField('Tempo Médio de Entrega (em minutos, ex: 30)',
                                       validators=[DataRequired()])
    
    submit = SubmitField('Finalizar Registo')

    # --- Validadores Personalizados ---
    
    def validate_cnpj(self, cnpj):
        """Verifica se o CNPJ já existe na base de dados."""
        rest = Restaurante.query.filter_by(cnpj=cnpj.data).first()
        if rest:
            raise ValidationError('Este CNPJ já está registado.')

    def validate_nome_fantasia(self, nome_fantasia):
        """Verifica se o nome do restaurante já existe."""
        rest = Restaurante.query.filter_by(nome_fantasia=nome_fantasia.data).first()
        if rest:
            raise ValidationError('Este nome de restaurante já está em uso.')

class CategoryForm(FlaskForm):
    """
    Formulário para adicionar/editar uma Categoria.
    """
    nome = StringField('Nome da Categoria', validators=[DataRequired(), Length(max=50)])
    submit_category = SubmitField('Salvar Categoria')


class ProductForm(FlaskForm):
    """
    Formulário para adicionar/editar um Produto.
    """
    nome = StringField('Nome do Produto', validators=[DataRequired(), Length(max=100)])
    descricao = TextAreaField('Descrição (opcional)')
    preco = FloatField('Preço (ex: 12.50)', validators=[DataRequired()])
    
    # --- NOVO CAMPO DE IMAGEM ---
    imagem = FileField('Foto do Produto', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Apenas imagens são permitidas!')
    ])
    # ----------------------------

    disponivel = BooleanField('Disponível', default=True)
    
    # Este campo será preenchido dinamicamente pela nossa rota
    categoria_id = SelectField('Categoria', coerce=int, validators=[DataRequired()])
    
    submit_product = SubmitField('Salvar Produto')

class OrderStatusForm(FlaskForm):
    """
    Formulário para mudar o status do pedido (botão de Ação).
    """
    submit = SubmitField('Atualizar Status')

class UpdateRestaurantInfoForm(FlaskForm):
    """
    Formulário para o Dono do Restaurante editar as informações básicas.
    """
    nome_fantasia = StringField('Nome do Restaurante (Nome Fantasia)', 
                                validators=[DataRequired(), Length(max=100)])
    cnpj = StringField('CNPJ (apenas números)', 
                       validators=[DataRequired(), Length(min=14, max=14)])
    taxa_entrega = FloatField('Taxa de Entrega (ex: 5.50)', 
                              validators=[DataRequired()])
    tempo_medio_entrega = IntegerField('Tempo Médio de Entrega (em minutos, ex: 30)',
                                       validators=[DataRequired()])
    logo = FileField('Logomarca do Restaurante', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Apenas imagens são permitidas!')
    ])
    
    submit = SubmitField('Salvar Informações')