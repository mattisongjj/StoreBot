import json
from telebot.util import quick_markup

class Transaction:
    def __init__(self, store_id=None, operator=None, customer=None, items='[]', type=None, loan_id=None, old_qty='{}', change='{}', new_qty='{}', datetime=None):
        self.store_id = store_id
        self.operator = operator
        self.customer = customer
        self.items = items
        self.type = type
        self.loan_id = loan_id
        self.old_qty = old_qty
        self.change = change
        self.new_qty = new_qty
        self.datetime = datetime


# Inserts transction into transaction table and returns the transaction
def insertTransaction(transaction,db):
    cursor = db.cursor()
    cursor.execute('INSERT INTO transactions (store_id, operator, customer, items, type, loan_id, old_qty, change, new_qty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (transaction.store_id,transaction.operator,transaction.customer,transaction.items,transaction.type,transaction.loan_id,transaction.old_qty,transaction.change,transaction.new_qty))
    db.commit()
    return cursor.lastrowid

# Converts transaction information to string
def transaction_info(id, db):
    cursor = db.cursor()
    cursor.execute('SELECT type, customer, items, change FROM transactions WHERE transaction_id = ?', (id,))
    info = cursor.fetchone()
    customer = info[1]
    items = json.loads(info[2])
    changes = json.loads(info[3])
    reply = f'\n\nCurrent Transaction:\n\nType - {info[0]}\nCustomer - {customer}\n\n'
    for item in items:
        if changes[item] > 0:
            reply = reply + f'{item} +{changes[item]}'
        else:
            reply = reply + f'{item} {changes[item]}'
    return reply

# Inline keyboard markup for transactions
def transaction_markup(id):
    return quick_markup({'Select Items': {'callback_data': f'(select_add_items) {id}'},
                            'Remove Items': {'callback_data': f'(select_remove_items) {id}'},
                            'Add Customer (Optional)': {'callback_data': f'(add_customer) {id}'},
                            'Confirm Transaction': {'callback_data': f'(confirm_transaction) {id}'},
                            'Cancel Transaction': {'callback_data': f'(cancel) {id}'}},
                            row_width=1)