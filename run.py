import sys
import os
from dotenv import load_dotenv

# 1. SOLUÇÃO CRÍTICA: Carrega as variáveis (.env) ANTES de qualquer outra coisa
# Isso resolve o erro "RuntimeError: Either SQLALCHEMY_DATABASE_URI..."
load_dotenv()

from src import create_app
from flask import request
from src.extensions import db 
from src.models import Pedido, User 
import stripe
import click
from src.services.email_service import send_email
from src.services.sms_service import send_sms

# Cria a instância da aplicação
app = create_app()

# --- ROTA DO WEBHOOK (ISOLADA E COM GAMIFICAÇÃO) ---
@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """
    Rota chamada pelo servidor do Stripe para notificar eventos (pagamento aprovado).
    """
    endpoint_secret = app.config.get('STRIPE_WEBHOOK_SECRET')
    payload = request.data
    sig_header = request.headers.get('stripe-signature')

    event = None
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print(f'ERRO WEBHOOK (Assinatura): {e}')
        return 'Bad Request', 400

    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        pedido_id = session_data.get('client_reference_id')
        
        if pedido_id:
            with app.app_context(): 
                pedido = Pedido.query.get(int(pedido_id))
                
                if pedido and pedido.status == 'Pendente de Pagamento':
                    # 1. Atualiza Status
                    pedido.status = 'Recebido'
                    
                    # 2. Lógica de Gamificação (YummyRewards)
                    try:
                        user = User.query.get(pedido.cliente_id)
                        # 10 pontos por cada Real gasto
                        pontos_ganhos = int(pedido.preco_total * 10)
                        user.pontos += pontos_ganhos
                        
                        # Verifica Level Up
                        if user.pontos >= 5000:
                            user.nivel = 'Ouro'
                        elif user.pontos >= 2000:
                            user.nivel = 'Prata'
                        else:
                            user.nivel = 'Bronze'
                            
                        print(f"✅ GAMIFICATION: {user.nome_completo} ganhou {pontos_ganhos} pts (Nível: {user.nivel})")
                    except Exception as e:
                        print(f"⚠️ Erro ao atualizar pontos: {e}")

                    # 3. Salva tudo
                    db.session.commit() 
                    print(f"✅ WEBHOOK: Pedido #{pedido_id} processado com sucesso.")

                    # --- ENVIAR E-MAIL DE CONFIRMAÇÃO ---
                    user = User.query.get(pedido.cliente_id)
                    send_email(
                        subject=f"YummyGo: Pedido #{pedido.id} Confirmado!",
                        recipients=[user.email],
                        template_name="order_confirmed", # Precisamos criar este template
                        pedido=pedido,
                        nome=user.nome_completo
                    )
                
    return 'OK', 200


# --- COMANDOS DE TESTE (Úteis para Debug) ---
@app.cli.command("test-email")
@click.argument("recipient")
def test_email_command(recipient):
    """Teste de envio de e-mail."""
    print(f"A tentar enviar e-mail para: {recipient}...")
    success = send_email("Teste YummyGo", [recipient], "otp_verification", nome="Tester", codigo_otp="123456")
    if success: print("✅ Sucesso!")
    else: print("❌ Falha.")

@app.cli.command("test-sms")
@click.argument("to_number")
def test_sms_command(to_number):
    """Teste de envio de SMS."""
    print(f"A tentar enviar SMS para: {to_number}...")
    success = send_sms(to_number, "Teste YummyGo SMS")
    if success: print("✅ Sucesso!")
    else: print("❌ Falha.")


if __name__ == '__main__':
    app.run()