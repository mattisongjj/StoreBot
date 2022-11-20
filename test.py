class Transaction:
    def __init__(self, store_id=None, id=None, type=None, operator=None, customer=None, items=None, loan_id=None, old_qty=None, change=None, new_qty=None, datetime=None):
        self.store_id = store_id
        self.id = id
        self.type = type
        self.operator = operator
        self.customer = customer
        self.items = items
        self.loan_id = loan_id
        self.old_qty = old_qty
        self.change = change
        self.new_qty = new_qty
        self.datetime = datetime