import random
from datetime import datetime, timedelta
from src import create_app
from src.extensions import db
from src.models import User, Restaurante, Pedido, Avaliacao, ItemPedido, Produto

# Inicializa a aplicação para ter acesso ao Banco de Dados
app = create_app()

def gerar_dados():
    with app.app_context():
        print("--- INICIANDO GERAÇÃO DE DADOS FALSOS PARA VÍDEO ---")

        # 1. Encontrar o Restaurante e o Cliente Principal
        # (Assumindo que você já criou o 'Omega' e o seu usuário)
        restaurante = Restaurante.query.first()
        cliente = User.query.filter_by(role='cliente').first()

        if not restaurante or not cliente:
            print("ERRO: Crie pelo menos um restaurante e um cliente no site primeiro!")
            return

        print(f"Gerando dados para Restaurante: {restaurante.nome_fantasia}")

        # Opções para aleatoriedade
        tipos_pagamento = ['Cartão de Crédito', 'Cartão de Débito', 'Pix', 'Dinheiro']
        status_possiveis = ['Concluído', 'Concluído', 'Concluído', 'Cancelado'] # Mais concluídos que cancelados
        
        # Pega alguns produtos reais para vincular (se existirem)
        produtos = Produto.query.filter_by(restaurante_id=restaurante.id).all()

        # 2. Gerar 50 Pedidos Falsos nos últimos 30 dias
        novos_pedidos = []
        for i in range(50):
            # Data aleatória nos últimos 30 dias
            dias_atras = random.randint(0, 30)
            data_pedido = datetime.now() - timedelta(days=dias_atras)
            
            # Valor aleatório entre 30.00 e 150.00
            valor = random.uniform(30.00, 150.00)
            
            pagamento = random.choice(tipos_pagamento)
            status = random.choice(status_possiveis)

            pedido = Pedido(
                cliente_id=cliente.id,
                restaurante_id=restaurante.id,
                preco_total=valor,
                status=status,
                endereco_entrega="Endereço Gerado Automaticamente, 123 - Centro",
                tipo_pagamento=pagamento,
                data_criacao=data_pedido
            )
            
            db.session.add(pedido)
            novos_pedidos.append(pedido)
        
        # Commit para salvar os pedidos e gerar os IDs
        db.session.commit()
        print(f"✅ {len(novos_pedidos)} Pedidos gerados com sucesso!")

        # 3. Gerar Avaliações para esses pedidos
        # (Apenas para pedidos Concluídos)
        avaliacoes_count = 0
        for pedido in novos_pedidos:
            if pedido.status == 'Concluído':
                # 80% de chance de ter avaliação
                if random.random() > 0.2:
                    nota = random.randint(1, 5)
                    
                    # Se nota baixa, marca como reclamação
                    reclamacao = True if nota <= 2 else False
                    
                    avaliacao = Avaliacao(
                        pedido_id=pedido.id,
                        restaurante_id=restaurante.id,
                        cliente_id=cliente.id,
                        nota=nota,
                        comentario="Comentário gerado automaticamente.",
                        reclamacao=reclamacao,
                        data_criacao=pedido.data_criacao + timedelta(hours=2) # Avaliou 2h depois
                    )
                    db.session.add(avaliacao)
                    avaliacoes_count += 1

        db.session.commit()
        print(f"✅ {avaliacoes_count} Avaliações geradas com sucesso!")
        print("--- PROCESSO CONCLUÍDO ---")
        print("Agora abra os relatórios no painel e veja os gráficos coloridos!")

if __name__ == "__main__":
    gerar_dados()