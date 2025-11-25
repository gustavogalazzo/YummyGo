# 🍔 YummyGo: Plataforma de Delivery (Projeto Final)

Bem-vindo ao repositório do YummyGo, uma plataforma de delivery completa construída com **Flask**, com foco em arquitetura modular (Blueprints) e segurança abrangente. Este projeto está na fase de "Esqueleto Funcional Completo", faltando apenas a estilização final.

---

## 🎯 Funcionalidades Implementadas (Esqueleto Funcional)

Todas as funcionalidades essenciais de Back-End (DB, Autenticação, Fluxos) estão operacionais:

### 🔐 1. Autenticação Abrangente
* Login/Registo por E-mail e Senha (com hashing BCrypt).
* Login/Registo Social via **Google** e **Facebook** (OAuth 2.0).
* Login por Código OTP (One-Time Password) via **E-mail** e **SMS (Twilio)**.

### 👥 2. Gestão de Contas
* Clientes: Área 'Meu Perfil' para gerir dados pessoais e **Gestão Completa de Endereços** (Adicionar/Apagar, com integração **ViaCEP** no Front-End para UX).
* Clientes: **Histórico e Acompanhamento** de Pedidos.

### 🍽️ 3. Portal do Restaurante
* Fluxo de Registo de Parceiro (Muda a `role` do utilizador).
* Gestão de Cardápio Completa (Adicionar/Apagar Categorias e Produtos).
* **Gestão de Pedidos (Cozinha):** Interface para o dono atualizar o `Pedido.status` (Recebido → Em Preparo → Em Rota).

### 🛒 4. Fluxo de Compra e Pagamento
* Sistema de **Carrinho de Compras** na `session` (com regra de 1 restaurante por vez).
* Página de **Checkout** com resumo e seleção de endereço.
* **Integração de Pagamento Seguro (Stripe):** Criação de Sessão de Checkout e Confirmação de Pagamento via **Webhook** seguro.

---

## 🛠️ Guia de Iniciação Rápida (Setup)

Siga os passos abaixo para configurar e rodar o YummyGo no seu ambiente local (Windows PowerShell recomendado).

### Pré-requisitos
* **Python 3.8+**
* **Git**
* Conta de Teste no **Stripe** (para chaves `pk_test_` e `sk_test_`).

### 1. Clonar e Instalar Dependências

Abra o seu terminal (PowerShell) e execute:

```bash
# 1. Clonar o repositório (substitua pelo seu URL)
git clone [URL_DO_SEU_REPOSITORIO]
cd yummygo

# 2. Criar e Ativar Ambiente Virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar as bibliotecas
pip install -r requirements.txt

2. Configurar Variáveis de Ambiente
Crie um ficheiro .env na pasta yummygo/ (a raiz) e preencha com as suas chaves secretas.

Ini, TOML

# Chave secreta do Flask (obrigatória)
SECRET_KEY='sua-chave-secreta-aleatoria-aqui' 

# Base de Dados (SQLite)
DATABASE_URL='sqlite:///dev.db'

# Google Login (Para Autenticação Social)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Twilio (Para Autenticação OTP via SMS)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# PAGAMENTOS (Stripe - Modo de Teste)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_..



Markdown
# 🍔 YummyGo: Plataforma de Delivery (Projeto Final)

Bem-vindo ao repositório do YummyGo, uma plataforma de delivery completa construída com **Flask**, com foco em arquitetura modular (Blueprints) e segurança abrangente. Este projeto está na fase de "Esqueleto Funcional Completo", faltando apenas a estilização final.

---

## 🎯 Funcionalidades Implementadas (Esqueleto Funcional)

Todas as funcionalidades essenciais de Back-End (DB, Autenticação, Fluxos) estão operacionais:

### 🔐 1. Autenticação Abrangente
* Login/Registo por E-mail e Senha (com hashing BCrypt).
* Login/Registo Social via **Google** e **Facebook** (OAuth 2.0).
* Login por Código OTP (One-Time Password) via **E-mail** e **SMS (Twilio)**.

### 👥 2. Gestão de Contas
* Clientes: Área 'Meu Perfil' para gerir dados pessoais e **Gestão Completa de Endereços** (Adicionar/Apagar, com integração **ViaCEP** no Front-End para UX).
* Clientes: **Histórico e Acompanhamento** de Pedidos.

### 🍽️ 3. Portal do Restaurante
* Fluxo de Registo de Parceiro (Muda a `role` do utilizador).
* Gestão de Cardápio Completa (Adicionar/Apagar Categorias e Produtos).
* **Gestão de Pedidos (Cozinha):** Interface para o dono atualizar o `Pedido.status` (Recebido → Em Preparo → Em Rota).

### 🛒 4. Fluxo de Compra e Pagamento
* Sistema de **Carrinho de Compras** na `session` (com regra de 1 restaurante por vez).
* Página de **Checkout** com resumo e seleção de endereço.
* **Integração de Pagamento Seguro (Stripe):** Criação de Sessão de Checkout e Confirmação de Pagamento via **Webhook** seguro.


Bash
# Certifique-se que o .venv está ativo!
flask db upgrade

4. Iniciar a Aplicação
Inicie o servidor de desenvolvimento:

Bash

flask --app run.py run