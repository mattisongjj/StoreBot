import json

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
        reply = reply + f'{item} x{changes[item]}'
    return reply