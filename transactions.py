class Transaction:
    def __init__(self, store_id='-', operator='-', customer='-', items='-', type='-', loan_id='-', old_qty='-', change='-', new_qty='-', datetime='-'):
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
    cursor.execute('INSERT INTO transactions (store_id, Operator, Customer, Item, Type, Loan_id, Old_Qty, Change, New_Qty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (transaction.store_id,transaction.operator,transaction.customer,transaction.items,transaction.type,transaction.loan_id,transaction.old_qty,transaction.change,transaction.new_qty))
    db.commit()
    return cursor.lastrowid