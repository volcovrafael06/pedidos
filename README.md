# Sistema de Pedidos via WhatsApp Chatbot para Pizzaria

Sistema de gerenciamento de pedidos via WhatsApp para pizzarias, permitindo que clientes façam pedidos diretamente pelo WhatsApp e que a pizzaria gerencie esses pedidos em tempo real.

## Principais Funcionalidades

- **Integração com WhatsApp**: Recebe mensagens dos clientes e envia respostas automáticas
- **Catálogo de Produtos**: Menu digital com produtos, preços e categorias
- **Fluxo de Pedido**: Interação completa de seleção de produtos até finalização do pedido
- **Área Administrativa**: Painel onde funcionários podem gerenciar pedidos e status
- **Formas de Pagamento**: Integração com serviços de pagamento
- **Notificações**: Notificações automáticas sobre status do pedido

## Configuração Inicial

1. Instale as dependências:
```
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente no arquivo `.env` (veja `.env.example`)

3. Inicialize o banco de dados:
```
flask db init
flask db migrate
flask db upgrade
```

4. Execute o servidor:
```
flask run
```

## Integrações Necessárias

Para configurar o sistema corretamente, você precisará:

1. Conta na Twilio para a API do WhatsApp
2. Configuração de webhook para receber mensagens
3. (Opcional) Integração com serviço de pagamentos
