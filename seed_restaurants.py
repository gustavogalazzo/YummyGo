import random
from src import create_app
from src.extensions import db
from src.models import User, Restaurante, Categoria, Produto

app = create_app()

# --- DADOS CRIATIVOS PARA OS RESTAURANTES ---
dados_categorias = {
    "Pizza": {
        "nomes": ["Pizzaria Don Luigi", "Forno D'Oro", "Pizza Planet", "Tutto Pizza", "Mamma Mia Pizzas"],
        "pratos": [
            {"nome": "Pizza Margherita", "desc": "Molho de tomate, mussarela de búfala e manjericão.", "preco": 45.00},
            {"nome": "Pizza Calabresa", "desc": "Calabresa artesanal, cebola roxa e azeitonas.", "preco": 42.00},
            {"nome": "Pizza 4 Queijos", "desc": "Gorgonzola, parmesão, mussarela e catupiry.", "preco": 48.00}
        ],
        "cor": "d32f2f" # Vermelho para logo
    },
    "Hamburguer": {
        "nomes": ["Burger King Kong", "Smash Bros Burger", "Texas Grill", "Retro Diner 50s", "Ogro Burger"],
        "pratos": [
            {"nome": "X-Bacon Duplo", "desc": "Dois hambúrgueres de 180g, muito bacon e cheddar.", "preco": 32.00},
            {"nome": "Smash Salad", "desc": "Carne prensada, alface americana, tomate e molho especial.", "preco": 22.00},
            {"nome": "Batata Rústica", "desc": "Batatas cortadas a mão com alecrim.", "preco": 12.00}
        ],
        "cor": "e65100" # Laranja
    },
    "Japonesa": {
        "nomes": ["Sushi Zen", "Tokyo Rolls", "Samurai Sashimi", "Oishii Ramen", "Monte Fuji Sushi"],
        "pratos": [
            {"nome": "Combo Salmão (20 peças)", "desc": "Sashimis, niguiris e uramakis de salmão fresco.", "preco": 65.00},
            {"nome": "Temaki Philadelfia", "desc": "Salmão, cream cheese e cebolinha.", "preco": 24.00},
            {"nome": "Yakisoba Clássico", "desc": "Macarrão, legumes e carne.", "preco": 35.00}
        ],
        "cor": "d81b60" # Rosa escuro
    },
    "Saudável": {
        "nomes": ["Green Life", "Salad Bar", "Fit Kitchen", "Organic Roots", "Fresh & Co"],
        "pratos": [
            {"nome": "Salada Caesar Fit", "desc": "Alface, frango grelhado, croutons integrais.", "preco": 28.00},
            {"nome": "Wrap de Atum", "desc": "Pão folha integral, pasta de atum e rúcula.", "preco": 22.00},
            {"nome": "Suco Detox", "desc": "Couve, limão, gengibre e maçã.", "preco": 12.00}
        ],
        "cor": "2e7d32" # Verde
    },
    "Doces": {
        "nomes": ["Sugar Rush", "Choco Dream", "Vovó Maria Bolos", "Donut World", "Gelato Italiano"],
        "pratos": [
            {"nome": "Brownie de Chocolate", "desc": "Com nozes e calda quente.", "preco": 15.00},
            {"nome": "Bolo de Cenoura", "desc": "Cobertura de chocolate belga.", "preco": 12.00},
            {"nome": "Milkshake de Morango", "desc": "Feito com a fruta e sorvete artesanal.", "preco": 18.00}
        ],
        "cor": "8e24aa" # Roxo
    },
    "Bebidas": {
        "nomes": ["Beer Point", "Adega Central", "Smoothie King", "Coffee Lab", "Rei do Suco"],
        "pratos": [
            {"nome": "Cerveja Artesanal IPA", "desc": "500ml, notas cítricas.", "preco": 25.00},
            {"nome": "Vinho Tinto Seco", "desc": "Garrafa 750ml, safra especial.", "preco": 80.00},
            {"nome": "Cappuccino Italiano", "desc": "Com canela e chocolate.", "preco": 10.00}
        ],
        "cor": "1565c0" # Azul
    }
}

def seed_restaurants():
    with app.app_context():
        print("--- INICIANDO CRIAÇÃO DE RESTAURANTES FAKES ---")
        
        count = 0
        
        for categoria_nome, dados in dados_categorias.items():
            print(f"\nCriando categoria: {categoria_nome}...")
            
            for nome_restaurante in dados["nomes"]:
                # 1. Criar Dono (User)
                # Email único: dono_nomerestaurante@teste.com (sem espaços)
                email_limpo = f"dono_{nome_restaurante.lower().replace(' ', '').replace("'", "")}@teste.com"
                
                # Verifica se já existe para não duplicar
                if User.query.filter_by(email=email_limpo).first():
                    print(f"  - {nome_restaurante} já existe. Pulando.")
                    continue

                dono = User(
                    nome_completo=f"Dono {nome_restaurante}",
                    email=email_limpo,
                    telefone=f"+55119{random.randint(10000000, 99999999)}",
                    role='restaurante'
                )
                dono.set_password("123456") # Senha padrão para testes
                db.session.add(dono)
                db.session.commit() # Commit para gerar o ID do dono

                # 2. Criar Restaurante
                # Gera uma Logo com as iniciais e cor da categoria
                iniciais = "".join([w[0] for w in nome_restaurante.split()[:2]])
                cor_bg = dados["cor"]
                logo_fake = f"https://placehold.co/200x200/{cor_bg}/white?text={iniciais}"

                novo_rest = Restaurante(
                    nome_fantasia=nome_restaurante,
                    cnpj=str(random.randint(10000000000000, 99999999999999)),
                    taxa_entrega=random.choice([0.0, 5.0, 7.50, 10.0, 12.0]),
                    tempo_medio_entrega=random.choice([20, 30, 45, 60]),
                    ativo=True,
                    logo_url=logo_fake,
                    user_id=dono.id
                )
                db.session.add(novo_rest)
                db.session.commit()

                # 3. Criar Categoria do Cardápio (Ex: "Destaques")
                cat_cardapio = Categoria(nome="Destaques", restaurante_id=novo_rest.id)
                db.session.add(cat_cardapio)
                db.session.commit()

                # 4. Adicionar Produtos
                for prato in dados["pratos"]:
                    # Gera uma imagem fake bonita para o produto
                    nome_safe = prato['nome'].replace(" ", "+")
                    img_fake = f"https://placehold.co/600x400/{cor_bg}/white?text={nome_safe}"
                    
                    prod = Produto(
                        nome=prato['nome'],
                        descricao=prato['desc'],
                        preco=prato['preco'],
                        disponivel=True,
                        categoria_id=cat_cardapio.id,
                        restaurante_id=novo_rest.id,
                        imagem_url=img_fake
                    )
                    db.session.add(prod)
                
                db.session.commit()
                count += 1
                print(f"  ✅ Criado: {nome_restaurante} (Dono: {email_limpo})")

        print(f"\n--- SUCESSO! {count} RESTAURANTES CRIADOS ---")
        print("Senha padrão para todos os donos: 123456")

if __name__ == "__main__":
    seed_restaurants()