from telebot.util import quick_markup

# Converts transaction information to text
def transaction_info(id, db):
    cursor = db.cursor()
    cursor.execute('SELECT type, customer FROM transactions JOIN transaction_types ON transactions.type_id = transaction_types.id WHERE transactions.id = ?', (id,))
    row = cursor.fetchone()
    type = row[0]
    customer = row[1]
    cursor.execute('SELECT ItemName, change FROM (transactions JOIN transaction_items ON transactions.id = transaction_items.transaction_id) JOIN stocks ON transaction_items.stock_id = stocks.id WHERE transactions.id = ?', (id,))
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
                'Adjust Quantity/ New Transaction': {'callback_data': 'Adjust Qty'},
                'View Transaction History': {'callback_data': 'View Transaction History'},
                'Edit Store Details': {'callback_data': 'Edit Store Details'},
                'Exit': {'callback_data': 'Exit'}},
                row_width=1))
