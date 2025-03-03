from flask import Blueprint, request, jsonify, render_template
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from models import db, Customer, Order, OrderItem, Product, WhatsAppMessage, Category, User
import json
from datetime import datetime
from flask_login import login_required, current_user

whatsapp_bp = Blueprint('whatsapp_bp', __name__)

# Configurar cliente Twilio
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None

# Funções auxiliares para o processamento do chatbot
def get_or_create_customer(phone):
    customer = Customer.query.filter_by(phone=phone).first()
    if not customer:
        customer = Customer(phone=phone)
        db.session.add(customer)
        db.session.commit()
    return customer

def send_whatsapp_message(to, body):
    if not twilio_client:
        print(f"Mensagem WhatsApp seria enviada para {to}: {body}")
        return

    message = twilio_client.messages.create(
        from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
        body=body,
        to=f'whatsapp:{to}'
    )
    
    return message.sid

def save_message(customer_id, message, direction, is_human=False):
    message_log = WhatsAppMessage(
        customer_id=customer_id,
        message=message,
        direction=direction,
        is_human=is_human
    )
    db.session.add(message_log)
    db.session.commit()

def get_welcome_message():
    return ("Olá! Bem-vindo à Pizzaria. 😊🍕\n\n"
            "Como posso ajudar você hoje?\n\n"
            "1️⃣ - Ver o cardápio\n"
            "2️⃣ - Fazer um pedido\n"
            "3️⃣ - Consultar status do pedido\n"
            "4️⃣ - Falar com atendente")

def get_menu_message():
    categories = Category.query.all()
    menu_text = "🍕 *CARDÁPIO* 🍕\n\n"
    
    for category in categories:
        menu_text += f"*{category.name}*\n"
        products = Product.query.filter_by(category_id=category.id, available=True).all()
        
        for product in products:
            menu_text += f"- {product.name}: R$ {product.price:.2f}\n"
            if product.description:
                menu_text += f"  {product.description}\n"
        
        menu_text += "\n"
    
    menu_text += "Para fazer um pedido, digite o número 2."
    return menu_text

def process_order_start(customer):
    customer.conversation_state = 'ordering'
    
    # Criar um novo pedido
    new_order = Order(customer_id=customer.id)
    db.session.add(new_order)
    db.session.commit()
    
    customer.current_order_id = new_order.id
    db.session.commit()
    
    response = ("Ótimo! Vamos iniciar seu pedido. 🛒\n\n"
                "Por favor, digite o nome do item que deseja pedir (um por vez).\n"
                "Exemplo: 'Pizza de Calabresa Grande'\n\n"
                "Digite 'FINALIZAR' quando terminar de adicionar itens.")
    
    return response

def process_ordering(customer, message):
    if message.lower() == 'finalizar':
        return finalize_order(customer)
    
    # Verificar se a mensagem corresponde a algum produto
    product_terms = message.lower().split()
    matching_products = []
    
    for term in product_terms:
        if len(term) > 3:  # Ignorar termos muito curtos
            products = Product.query.filter(Product.name.ilike(f'%{term}%')).all()
            for product in products:
                if product not in matching_products:
                    matching_products.append(product)
    
    if not matching_products:
        return ("Desculpe, não encontrei esse produto no nosso cardápio. 😕\n"
                "Por favor, verifique o nome ou digite '1' para ver o cardápio.\n"
                "Digite 'FINALIZAR' para concluir seu pedido.")
    
    if len(matching_products) > 1:
        response = "Encontrei vários produtos que correspondem ao seu pedido. Por favor, escolha um:\n\n"
        for i, product in enumerate(matching_products, 1):
            response += f"{i}. {product.name} - R$ {product.price:.2f}\n"
        customer.conversation_state = 'selecting_product'
        # Salvar os produtos encontrados temporariamente
        customer.temp_data = json.dumps([p.id for p in matching_products])
        db.session.commit()
        return response
    
    # Adicionar o produto ao pedido atual
    product = matching_products[0]
    add_product_to_order(customer, product)
    
    return (f"Adicionado: {product.name} - R$ {product.price:.2f} ✅\n\n"
            "Deseja adicionar mais algum item?\n"
            "Digite o nome do próximo item ou 'FINALIZAR' para concluir o pedido.")

def add_product_to_order(customer, product, quantity=1):
    order = Order.query.get(customer.current_order_id)
    
    if not order:
        # Se não houver pedido ativo, criar um novo
        order = Order(customer_id=customer.id)
        db.session.add(order)
        db.session.commit()
        customer.current_order_id = order.id
        db.session.commit()
    
    # Verificar se o item já existe no pedido
    existing_item = OrderItem.query.filter_by(
        order_id=order.id,
        product_id=product.id
    ).first()
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=product.price
        )
        db.session.add(new_item)
    
    # Atualizar o total do pedido
    order.total += product.price * quantity
    
    db.session.commit()
    return order

def finalize_order(customer):
    order = Order.query.get(customer.current_order_id)
    
    if not order or not order.items:
        return ("Seu carrinho está vazio. Por favor, adicione alguns produtos antes de finalizar.\n"
                "Digite '1' para ver o cardápio.")
    
    # Resumo do pedido
    order_summary = "📋 *RESUMO DO PEDIDO* 📋\n\n"
    
    for item in order.items:
        product = Product.query.get(item.product_id)
        order_summary += f"- {item.quantity}x {product.name}: R$ {item.price * item.quantity:.2f}\n"
    
    order_summary += f"\n*Total: R$ {order.total:.2f}*\n\n"
    
    # Verificar se o cliente tem endereço cadastrado
    if not customer.address:
        customer.conversation_state = 'address'
        db.session.commit()
        return order_summary + "Por favor, informe seu endereço completo para entrega:"
    
    # Se já tem endereço, perguntar forma de pagamento
    order.address = customer.address
    db.session.commit()
    
    customer.conversation_state = 'payment'
    db.session.commit()
    
    return order_summary + (
        f"Endereço de entrega: {customer.address}\n\n"
        "Escolha a forma de pagamento:\n"
        "1️⃣ - Dinheiro\n"
        "2️⃣ - Cartão na entrega\n"
        "3️⃣ - PIX"
    )

def process_address(customer, message):
    # Salvar o endereço
    customer.address = message
    db.session.commit()
    
    # Atualizar o pedido atual
    order = Order.query.get(customer.current_order_id)
    order.address = message
    db.session.commit()
    
    # Avançar para pagamento
    customer.conversation_state = 'payment'
    db.session.commit()
    
    # Resumo do pedido
    order_summary = "📋 *RESUMO DO PEDIDO* 📋\n\n"
    
    for item in order.items:
        product = Product.query.get(item.product_id)
        order_summary += f"- {item.quantity}x {product.name}: R$ {item.price * item.quantity:.2f}\n"
    
    order_summary += f"\n*Total: R$ {order.total:.2f}*\n\n"
    
    return order_summary + (
        f"Endereço de entrega: {customer.address}\n\n"
        "Escolha a forma de pagamento:\n"
        "1️⃣ - Dinheiro\n"
        "2️⃣ - Cartão na entrega\n"
        "3️⃣ - PIX"
    )

def process_payment(customer, message):
    payment_methods = {
        '1': 'dinheiro',
        '2': 'cartao',
        '3': 'pix'
    }
    
    payment_method = payment_methods.get(message.strip(), None)
    
    if not payment_method:
        return ("Por favor, escolha uma forma de pagamento válida:\n"
                "1️⃣ - Dinheiro\n"
                "2️⃣ - Cartão na entrega\n"
                "3️⃣ - PIX")
    
    order = Order.query.get(customer.current_order_id)
    order.payment_method = payment_method
    order.status = 'novo'
    db.session.commit()
    
    # Resetar o estado da conversa
    customer.conversation_state = 'initial'
    customer.current_order_id = None
    db.session.commit()
    
    # Mensagem de confirmação
    if payment_method == 'pix':
        return (f"Pedido #{order.id} confirmado! 🎉\n\n"
                "Para pagar com PIX, utilize a chave abaixo:\n"
                "pizzaria@exemplo.com.br\n\n"
                "Seu pedido será preparado assim que o pagamento for confirmado.\n"
                "Você pode acompanhar o status do seu pedido digitando '3'.")
    else:
        return (f"Pedido #{order.id} confirmado! 🎉\n\n"
                f"Forma de pagamento: {payment_method.upper()}\n"
                "Seu pedido foi enviado para a cozinha e logo estará em preparação.\n"
                "Você receberá atualizações sobre o status do seu pedido.\n"
                "Para consultar o status a qualquer momento, digite '3'.")

def get_order_status(customer):
    # Buscar pedidos recentes do cliente
    recent_orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.created_at.desc()).limit(3).all()
    
    if not recent_orders:
        return "Você não possui pedidos recentes. Para fazer um novo pedido, digite '2'."
    
    status_messages = {
        'novo': 'Recebido e aguardando confirmação',
        'em_preparo': 'Em preparação na cozinha',
        'pronto': 'Pronto e aguardando entregador',
        'em_entrega': 'Saiu para entrega',
        'entregue': 'Entregue',
        'cancelado': 'Cancelado'
    }
    
    response = "📊 *SEUS PEDIDOS RECENTES* 📊\n\n"
    
    for order in recent_orders:
        status_text = status_messages.get(order.status, 'Status desconhecido')
        created_at = order.created_at.strftime('%d/%m/%Y %H:%M')
        
        response += f"Pedido #{order.id} - {created_at}\n"
        response += f"Status: {status_text}\n"
        response += f"Total: R$ {order.total:.2f}\n\n"
    
    response += "Para fazer um novo pedido, digite '2'."
    return response

@whatsapp_bp.route('/webhook', methods=['POST'])
def webhook():
    # Processar mensagens recebidas do WhatsApp
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '').replace('whatsapp:', '')
    
    # Obter ou criar cliente
    customer = get_or_create_customer(sender_phone)
    
    # Atualizar última interação
    customer.last_interaction = datetime.utcnow()
    
    # Salvar mensagem recebida
    save_message(customer.id, incoming_msg, 'inbound')
    
    # Verificar se o cliente está em modo de atendimento humano
    if customer.human_support:
        # Notificar atendentes sobre mensagem recebida
        response = "Sua mensagem foi encaminhada ao atendente. Aguarde a resposta."
        
        # Salvar resposta automática
        save_message(customer.id, response, 'outbound')
        
        # Enviamos apenas o "recebemos sua mensagem" - o atendente responderá em breve
        resp = MessagingResponse()
        resp.message(response)
        
        return str(resp)
    
    # Processar a mensagem com base no estado da conversa
    if incoming_msg == '1':
        response = get_menu_message()
    elif incoming_msg == '2':
        response = process_order_start(customer)
    elif incoming_msg == '3':
        response = get_order_status(customer)
    elif incoming_msg == '4':
        # Opção para falar com atendente
        customer.human_support = True
        db.session.commit()
        
        response = "Você será atendido por um de nossos colaboradores em breve. Aguarde, por favor."
    elif customer.conversation_state == 'ordering':
        response = process_ordering(customer, incoming_msg)
    elif customer.conversation_state == 'selecting_product':
        # Processar seleção de produto específico
        try:
            choice_idx = int(incoming_msg) - 1
            product_ids = json.loads(customer.temp_data)
            
            if 0 <= choice_idx < len(product_ids):
                product = Product.query.get(product_ids[choice_idx])
                add_product_to_order(customer, product)
                
                customer.conversation_state = 'ordering'
                customer.temp_data = None
                db.session.commit()
                
                response = (f"Adicionado: {product.name} - R$ {product.price:.2f} ✅\n\n"
                            "Deseja adicionar mais algum item?\n"
                            "Digite o nome do próximo item ou 'FINALIZAR' para concluir o pedido.")
            else:
                response = "Por favor, escolha um número válido da lista."
        except:
            response = "Por favor, escolha um número válido da lista."
    elif customer.conversation_state == 'address':
        response = process_address(customer, incoming_msg)
    elif customer.conversation_state == 'payment':
        response = process_payment(customer, incoming_msg)
    else:
        response = get_welcome_message()
    
    # Salvar resposta enviada
    save_message(customer.id, response, 'outbound')
    
    # Enviar resposta via Twilio
    resp = MessagingResponse()
    resp.message(response)
    
    return str(resp)

@whatsapp_bp.route('/send_notification', methods=['POST'])
def send_notification():
    # Endpoint para enviar notificações manualmente para clientes
    data = request.json
    
    if not data or 'customer_id' not in data or 'message' not in data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    customer = Customer.query.get(data['customer_id'])
    
    if not customer:
        return jsonify({'error': 'Cliente não encontrado'}), 404
    
    # Enviar mensagem
    send_whatsapp_message(customer.phone, data['message'])
    
    # Salvar na base
    is_human = data.get('is_human', False)
    save_message(customer.id, data['message'], 'outbound', is_human=is_human)
    
    return jsonify({'success': True})

@whatsapp_bp.route('/update_order_status', methods=['POST'])
def update_order_status():
    # Endpoint para atualizar status do pedido e notificar cliente
    data = request.json
    
    if not data or 'order_id' not in data or 'status' not in data:
        return jsonify({'error': 'Dados inválidos'}), 400
    
    order = Order.query.get(data['order_id'])
    
    if not order:
        return jsonify({'error': 'Pedido não encontrado'}), 404
    
    # Atualizar status
    old_status = order.status
    order.status = data['status']
    db.session.commit()
    
    # Notificar cliente se houver mudança de status
    if old_status != data['status']:
        customer = Customer.query.get(order.customer_id)
        
        status_messages = {
            'em_preparo': f'Seu pedido #{order.id} já está sendo preparado! 👨‍🍳',
            'pronto': f'Seu pedido #{order.id} está pronto e será enviado para entrega em breve! 📦',
            'em_entrega': f'Seu pedido #{order.id} saiu para entrega e logo chegará até você! 🛵',
            'entregue': f'Seu pedido #{order.id} foi entregue. Bom apetite! 😋\nAgradecemos a preferência!',
            'cancelado': f'Seu pedido #{order.id} foi cancelado. Entre em contato conosco para mais informações.'
        }
        
        if data['status'] in status_messages:
            message = status_messages[data['status']]
            send_whatsapp_message(customer.phone, message)
            save_message(customer.id, message, 'outbound')
    
    return jsonify({'success': True})

# Interface de administração para conversas 
@whatsapp_bp.route('/conversations')
@login_required
def conversations():
    # Obter clientes com conversas recentes, ordenados por data da última interação
    customers_with_conversations = Customer.query.filter(
        Customer.messages.any()
    ).order_by(Customer.last_interaction.desc()).all()
    
    # Listar clientes com suporte humano ativo
    human_support_customers = Customer.query.filter_by(human_support=True).all()
    
    return render_template('admin/conversations.html', 
                          customers=customers_with_conversations,
                          human_support_customers=human_support_customers)

@whatsapp_bp.route('/conversation/<int:id>')
@login_required
def view_conversation(id):
    customer = Customer.query.get_or_404(id)
    messages = WhatsAppMessage.query.filter_by(customer_id=customer.id).order_by(WhatsAppMessage.timestamp).all()
    
    return render_template('admin/conversation_detail.html', 
                          customer=customer,
                          messages=messages)

@whatsapp_bp.route('/conversation/reply/<int:id>', methods=['POST'])
@login_required
def reply_to_conversation(id):
    customer = Customer.query.get_or_404(id)
    message = request.form.get('message')
    
    if message:
        # Enviar mensagem via WhatsApp
        send_whatsapp_message(customer.phone, message)
        
        # Registrar mensagem enviada pelo atendente
        save_message(customer.id, message, 'outbound', is_human=True)
        
        flash('Mensagem enviada com sucesso!', 'success')
    
    return redirect(url_for('whatsapp_bp.view_conversation', id=customer.id))

@whatsapp_bp.route('/conversation/take/<int:id>', methods=['POST'])
@login_required
def take_conversation(id):
    customer = Customer.query.get_or_404(id)
    
    # Atribuir ao atendente atual
    customer.assigned_to = current_user.id
    db.session.commit()
    
    flash(f'Você assumiu a conversa com {customer.name or customer.phone}', 'success')
    return redirect(url_for('whatsapp_bp.view_conversation', id=customer.id))

@whatsapp_bp.route('/conversation/release/<int:id>', methods=['POST'])
@login_required
def release_conversation(id):
    customer = Customer.query.get_or_404(id)
    
    # Desatribuir e retornar ao modo bot
    customer.assigned_to = None
    customer.human_support = False
    db.session.commit()
    
    # Enviar mensagem informando o retorno ao bot
    message = "Seu atendimento humano foi finalizado. Para continuar, use nosso menu automático ou digite 4 para falar com um atendente novamente."
    send_whatsapp_message(customer.phone, message)
    save_message(customer.id, message, 'outbound', is_human=True)
    
    flash('Atendimento finalizado e cliente retornado ao bot', 'success')
    return redirect(url_for('whatsapp_bp.conversations'))

@whatsapp_bp.route('/settings')
@login_required
def whatsapp_settings():
    return render_template('admin/whatsapp_settings.html',
                          account_sid=TWILIO_ACCOUNT_SID or '',
                          auth_token=TWILIO_AUTH_TOKEN or '',
                          phone_number=TWILIO_PHONE_NUMBER or '')

@whatsapp_bp.route('/settings/update', methods=['POST'])
@login_required
def update_whatsapp_settings():
    # Esta rota apenas mostra como atualizar as configurações
    # Na prática, você precisaria editar o arquivo .env e reiniciar o servidor
    
    account_sid = request.form.get('account_sid')
    auth_token = request.form.get('auth_token')
    phone_number = request.form.get('phone_number')
    
    # Aqui mostramos a configuração, mas não a salvamos realmente no arquivo
    flash('Para aplicar estas configurações, edite o arquivo .env com as informações acima e reinicie o servidor', 'info')
    
    return redirect(url_for('whatsapp_bp.whatsapp_settings'))
