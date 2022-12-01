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
    reply = f'\n\nCurrent Transaction:\n\nType - {type}\nCustomer - {customer}\n\n'
    if not items:
        return reply + 'No items in current transaction.'
    for item in items:
        if items[item] > 0:
            reply = reply + f'{item} +{items[item]}\n'
        else:
            reply = reply + f'{item} {items[item]}\n'
    return reply

# Inline keyboard markup for transactions
def transaction_markup(id):
    return quick_markup({'Select Items': {'callback_data': f'(select_add_items) {id}'},
                            'Remove Items': {'callback_data': f'(select_remove_items) {id}'},
                            'Add Customer (Optional)': {'callback_data': f'(add_customer) {id}'},
                            'Remove Customer': {'callback_data': f'(remove_customer) {id}'},
                            'Confirm Transaction': {'callback_data': f'(confirm_transaction) {id}'},
                            'Cancel Transaction': {'callback_data': f'(cancel) {id}'}},
                            row_width=1)
