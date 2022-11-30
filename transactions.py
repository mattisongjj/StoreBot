import json
from telebot.util import quick_markup

# Converts transaction information to text
def transaction_info(id, db):
    cursor = db.cursor()
    cursor.execute('SELECT type, customer, ItemName, change FROM ((transactions JOIN transaction_types ON transactions.type_id = transaction_types.id) JOIN transaction_items ON transactions.id = transaction_items.transaction_id) JOIN stocks ON transaction_items.stock_id = stocks.id WHERE transaction_id = ?', (id,))
    info = cursor.fetchall()
    customer = info[0][1]
    items = {}
    for row in info:
        items[row[2]] = row[3]
    reply = f'\n\nCurrent Transaction:\n\nType - {info[0][0]}\nCustomer - {customer}\n\n'
    for item in items:
        if items[item] > 0:
            reply = reply + f'{item} +{items[item]}'
        else:
            reply = reply + f'{item} {items[item]}'
    return reply

# Inline keyboard markup for transactions
def transaction_markup(id):
    return quick_markup({'Select Items': {'callback_data': f'(select_add_items) {id}'},
                            'Remove Items': {'callback_data': f'(select_remove_items) {id}'},
                            'Add Customer (Optional)': {'callback_data': f'(add_customer) {id}'},
                            'Confirm Transaction': {'callback_data': f'(confirm_transaction) {id}'},
                            'Cancel Transaction': {'callback_data': f'(cancel) {id}'}},
                            row_width=1)
