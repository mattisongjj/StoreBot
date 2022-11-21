class Transaction:
    def __init__(self, store_id=None, operator=None, customer=None, items=[], type=None, loan_id=None, old_qty=None, change=None, datetime=None):
        self.store_id = store_id
        self.operator = operator
        self.customer = customer
        self.items = items
        self.type = type
        self.loan_id = loan_id
        self.old_qty = old_qty
        self.change = change
        self.datetime = datetime
    
    def toString(self):
        # Convert transaction object to string format
        return f'store_id- {self.store_id} operator- {self.operator} customer- {self.customer} items- {self.items} type- {self.type} loan_id- {self.loan_id} old_qty- {self.old_qty} change- {self.change} datetime- {self.datetime}'

def toTransaction(string):
    # Convert string to transaction object
    data = string.split()

    return Transaction(data[data.index('store_id-') + 1], data[data.index('operator-') + 1], data[data.index('customer-') + 1], data[data.index('items-') + 1], data[data.index('type-') + 1], data[data.index('loan_id-') + 1],
    data[data.index('old_qty-') + 1], data[data.index('change-') + 1], data[data.index('datetime-') + 1])
