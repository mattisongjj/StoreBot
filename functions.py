from telebot.util import quick_markup

# Converts transaction information to text
def transaction_info(id, db):
    cursor = db.cursor()
    cursor.execute('SELECT type, customer FROM transactions JOIN transaction_types ON transactions.type_id = transaction_types.id WHERE transactions.id = ?', (id,))
    row = cursor.fetchone()
    type = row[0]
    customer = row[1]
    cursor.execute('SELECT ItemName, change FROM (transactions JOIN transaction_items ON transactions.id = transaction_items.transaction_id) JOIN stocks ON transaction_items.stock_id = stocks.id WHERE transactions.id = ? ORDER BY ItemName ASC', (id,))
    rows = cursor.fetchall()
    items = {}
    for row in rows:
        items[row[0]] = row[1]
    reply = f'\n\n<u>Transaction Information</u>\n\n<b>Type</b> - {type}\n<b>Customer</b> - {customer}\n\n<u>Items</u>\n'
    if not items:
        return reply + 'No items in current transaction.'
    for item in items:
        if items[item] > 0:
            reply = reply + f'<b>{item}:</b> +{items[item]}\n'
        else:
            reply = reply + f'<b>{item}:</b> {items[item]}\n'
    return reply

# Inline keyboard markup for transactions
def transaction_markup(id):
    return quick_markup({'Select Items': {'callback_data': f'(select_add_items) {id}'},
                            'Remove Items': {'callback_data': f'(select_remove_items) {id}'},
                            'Add/Change Customer (Optional)': {'callback_data': f'(add_customer) {id}'},
                            'Remove Customer': {'callback_data': f'(remove_customer) {id}'},
                            'Confirm Transaction': {'callback_data': f'(confirm) {id}'},
                            'Cancel Transaction': {'callback_data': f'(cancel) {id}'}},
                            row_width=1)

# Check if user is admin in chat        
def isadmin(bot, chat, user):
    member = bot.get_chat_member(chat.id, user.id)
    if member.status not in ['creator', 'administrator']:
        bot.send_message(chat.id, 'Access only for administrators of this chat.')
        return False
    return True

# Send index options in chat
def send_index(bot, chat):
    bot.send_message(chat.id, 'Select an option.', reply_markup=quick_markup({
                'View Current Stock': {'callback_data': 'View Current Stock'},
                'Manage Items': {'callback_data': 'Manage Items'},
                'New Transaction': {'callback_data': 'Adjust Qty'},
                'View Transaction History': {'callback_data': 'View Transaction History'},
                'Edit Store Details': {'callback_data': 'Edit Store Details'},
                'Exit': {'callback_data': 'Exit'}},
                row_width=1))

# Send index options in private chat
def private_index(bot, chat):
    bot.send_message(chat.id, 'Select an option.', reply_markup=quick_markup({'Request Items': {'callback_data': '(Request)'}, 'Contact Store': {'callback_data': 'Contact Store'}, 'Exit': {'callback_data': 'Exit'}}, row_width=1))

# Inline keyboard markup for request
def request_markup(id):
    return quick_markup({'Select Items': {'callback_data': f'(select_items_req) {id}'}, 
                        'Remove Items': {'callback_data': f'(select_remove_req) {id}'},
                        'Change/Remove Remarks': {'callback_data': f'(add_remove_req) {id}'},
                         'Confirm Request': {'callback_data': f'(confirm_req) {id}'},
                          'Cancel Request': {'callback_data': f'(cancel_req) {id}'}},
                          row_width=1)

# Converts request information into text
def request_info(id, db):
    cursor = db.cursor()

    # Get store name and remarks
    cursor.execute('SELECT store_id, remarks FROM request WHERE id = ?', (id,))
    row = cursor.fetchone()
    store_id = row[0]
    remarks = row[1]
    cursor.execute('SELECT StoreName FROM stores WHERE id = ?', (store_id,))
    storename = cursor.fetchone()[0]

    # Get items
    cursor.execute('SELECT ItemName, request_items.quantity FROM (request JOIN request_items ON request.id = request_items.request_id) JOIN stocks  ON request_items.stock_id = stocks.id WHERE request.id = ? ORDER BY ItemName ASC', (id,))
    items = cursor.fetchall()

    
    # Create reply
    reply = f"\n\n<u>Request Information</u>\n\n<b>Requesting From</b>: {storename}\n\n<u>Items</u>\n\n"

    # Check for items
    if not items:
        reply += 'No items in request.'
        return reply
    
    # Add items to reply
    for item in items:
        reply += f'<b>{item[0]}</b>: {item[1]}\n'

    # Add remarks to reply
    reply += '\n<u>Remarks</u>\n'
    if remarks:
        reply += remarks
    else:
        reply += 'No remarks.'

    return reply


