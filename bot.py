import telebot
from telebot.util import quick_markup
from telebot import types
import sqlite3
from sqlite3 import Error
import re

# Set API key
API_KEY = '5691173475:AAGF7nfwSMKzd4UyPpveJ2OYuu6PGSTJzLs'
bot = telebot.TeleBot(API_KEY, parse_mode=None)

# Connect to database
try:
    db = sqlite3.connect('stores.db', check_same_thread=False)
except Error as e:
    print(f"Error '{e}' occured when establishing connection to database")
cursor = db.cursor()

n_item = ''

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


def isadmin(chat, user):
    # Check if user is admin in chat
    member = bot.get_chat_member(chat.id, user.id)
    if member.status not in ['creator', 'administrator']:
        bot.send_message(chat.id, 'Sorry you are not an administrator of this chat.')
        return False
    return True

# Handle /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def index(message):
# Start bot

    # Bot was started in a group chat
    if message.chat.type == 'group':

        # Check for existing store
        cursor.execute("SELECT * FROM stores WHERE id = ?", (message.chat.id,))
        rows = cursor.fetchall()
        if len(rows) != 1:
            bot.send_message(message.chat.id, 'This group currently does not have a store. Enter /create_store to initialize store.')
            return
        # Show Options
        else:
            bot.send_message(message.chat.id, 'Choose an option', reply_markup=quick_markup({
                'View Current Stock': {'callback_data': 'View Current Stock'},
                'Add New Item': {'callback_data': 'Add New Item'},
                'Adjust Quantity/ New Transaction': {'callback_data': 'Adjust Qty'},
                'View Transaction History': {'callback_data': 'View Transaction History'}},
                row_width=1))


    # Bot was started in a private chat
    elif message.chat.type == 'private':

        # Ask for store name
        bot.send_message(message.chat.id, 'Enter a store name')
        # Show options










# Handles viewing of stock
@bot.callback_query_handler(func=lambda call: call.data == 'View Current Stock')
def view_stock(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    # Ensure user is admin
    if not isadmin(call.message.chat, call.from_user):
        return
    # Query database for items
    cursor.execute('SELECT ItemName FROM stocks WHERE store_id = ? ORDER BY ItemName ASC', (call.message.chat.id,))
    items = cursor.fetchall()
    if len(items) == 0:
        bot.send_message(call.message.chat.id, 'Store does not have any items.')
        return
    # Display options
    options = {'View Full Stock': {'callback_data': 'View Full Stock'}}
    for item in items:
        options[item[0]] = {'callback_data': f'(view) {item[0]}'}
    bot.send_message(call.message.chat.id, 'What would you like to view?', reply_markup=quick_markup(options, row_width=1))

@bot.callback_query_handler(func=lambda call: '(view)' == call.data.split()[0])
def view_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    # Query database
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE store_id = ? AND ItemName = ?', (call.message.chat.id, re.sub('(\(view\) )', '', call.data)))
    item = cursor.fetchone()
    bot.send_message(call.message.chat.id, f'No. of {item[0]} in store: {item[1]}')

@bot.callback_query_handler(func=lambda call: call.data == 'View Full Stock')
def full_stock(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    # Query database for items
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE store_id = ? ORDER BY ItemName ASC', (call.message.chat.id,))
    items = cursor.fetchall()
    reply = 'Total Stock:\n'
    for item in items:
        reply = reply + f'{item[0]} x{item[1]}\n'
    bot.send_message(call.message.chat.id, reply)
    

    







# Handles creation of new item
@bot.callback_query_handler(func=lambda call: call.data == 'Add New Item')
def new_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    msg = bot.send_message(call.message.chat.id, 'Name of new item?\n(Reply to this message)')
    bot.register_next_step_handler(msg, get_total)

def get_total(message):
    # Ensure message is text
    if not message.text:
        bot.reply_to(message, 'Invalid item name.')
    # Check database if item already exist
    cursor.execute('SELECT * FROM stocks WHERE store_id = ? AND ItemName = ?', (message.chat.id, message.text))
    if len(cursor.fetchall()) != 0:
        bot.reply_to(message, 'Item already exist in store.')
    # Remember item name
    global n_item 
    n_item = message.text
    # Get quantity
    msg = bot.reply_to(message,'Quantity of item?', reply_markup=types.ForceReply(True, 'Quantity of item'))
    bot.register_next_step_handler(msg, add_item)

def add_item(message):
    # Validate quantity
    try:
        int(message.text)
        if int(message.text) <= 0:
            bot.send_message(message.chat.id, 'Invalid Quantity')
    except:
        bot.send_message(message.chat.id, 'Invalid Quantity')

    # Add item to database
    global n_item
    cursor.execute('INSERT INTO stocks (store_id, ItemName, Quantity) VALUES (?, ?, ?)', (message.chat.id, n_item, int(message.text)))
    db.commit()
    bot.send_message(message.chat.id, f'x{message.text} {n_item} has been created and added to stock.')









# Handles quantity adjustment/new transactions
@bot.callback_query_handler(func=lambda call: call.data == 'Adjust Qty')
def choose_type(call):

    # Add default types
    types = {
        'Add New Transaction Type': {'callback_data': 'Add New Transaction Type'},
        'Remove Transaction Type': {'callback_data': 'Remove Transaction Type'},
        'Issue': {'callback_data': '(trans_type) Issue'},
        'Loan': {'callback_data': '(trans_type) Loan'}
        }
    
    # Get additional transaction types from store
    cursor.execute('SELECT type FROM transaction_types WHERE store_id = ?', (call.message.chat.id,))
    rows = cursor.fetchall()
    for row in rows:
        types[row[0]] = {'callback_data': f'(trans_type) {row[0]}'}

    # Create transaction types markup
    markup = quick_markup(types, row_width=1)

    # Display transaction types
    bot.delete_message(call.message.chat.id, call.message.id)
    bot.send_message(call.message.chat.id, 'Select Reason For Adjustment/Transaction Type.', reply_markup=markup)





# Handles creation of new transaction type
@bot.callback_query_handler(func=lambda call: call.data == 'Add New Transaction Type')
def new_type(call):
    # Ensure user is admin
    if not isadmin(call.message.chat, call.from_user):
        return
    # Get type name
    bot.delete_message(call.message.chat.id, call.message.id)
    msg = bot.send_message(call.message.chat.id, 'Name of new transaction type?\n (Reply this message)')
    bot.register_next_step_handler(msg, add_type)

def add_type(message):
    type = message.text
    # Validate type
    cursor.execute('SELECT * FROM transaction_types WHERE store_id = ? AND type = ?', (message.chat.id, type))
    if len(cursor.fetchall()) != 0 or not type:
        bot.reply_to(message, 'Invalid type name.')
        return
    # Add type to database
    cursor.execute('INSERT INTO transaction_types (store_id, type) VALUES (?, ?)', (message.chat.id, type))
    db.commit()
    bot.reply_to(message, 'New type successfully added.')





# Handles removal of transaction type
@bot.callback_query_handler(func=lambda call: call.data == 'Remove Transaction Type')
def remove_type(call):

    bot.delete_message(call.message.chat.id, call.message.id)

    # Ensure user is admin
    if not isadmin(call.message.chat, call.from_user):
        return

    # Get transaction types
    cursor.execute('SELECT type FROM transaction_types WHERE store_id = ?', (call.message.chat.id,))
    types = cursor.fetchall()

    # Ensure that created types exist
    if len(types) == 0:
        bot.send_message(call.message.chat.id, "There are currently no transaction types to be removed.\n Note: 'Issue' and 'Loan' cannot be removed.")
        return

    # Create markup
    markup = {}
    for type in types:
        markup[type[0]] = {'callback_data': f'(del) {type[0]}'} 

    # Query for type to be removed
    bot.send_message(call.message.chat.id, 'Select Transaction Type to be removed.', reply_markup=quick_markup(markup,row_width=1))

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(del)')
def remove_type_db(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Update database
    cursor.execute('DELETE FROM transaction_types WHERE store_id = ? AND type = ?', (call.message.chat.id, re.sub('(\(del\)) ', '', call.data)))
    db.commit()
    bot.send_message(call.message.chat.id, 'Transaction type succesfully deleted')




# Handles issue/loan transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(trans_type)')
def open_new_transaction(call):

    bot.delete_message(call.message.chat.id, call.message.id)

    # Start a new transaction
    transaction = Transaction(store_id=call.message.chat.id ,type=re.sub('(\(trans_type\) )', '', call.data))

    # Get items in store
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE store_id = ?', (call.message.chat.id,))
    items = cursor.fetchall()

    # Ensure at least one item
    if len(items) == 0:
        bot.send_message(call.message.chat.id, 'There are no items in currently in this store.')

    # Create markup
    markup = {}
    for item in items:
        markup[f'{item[0]} ({item[1]})'] = {'callback_data': f'(trans_item) {item[0]}' }

    # Query for item
    bot.send_message(call.message.chat.id, 'Select item involved in transaction', reply_markup=quick_markup(markup, row_width=1))




















# Handle /create_store command
@bot.message_handler(commands=['create_store'])
def create_store(message):
    # Ensure group does not already have a store
    cursor.execute('SELECT * FROM stores WHERE id = ?', (message.chat.id,))
    rows = cursor.fetchall()
    if len(rows) != 0:
        bot.reply_to(message, 'This groupchat already has a store.')
        return
    # Ensure that message was sent in a group chat
    if message.chat.type != 'group':
        bot.send_message(message.chat.id, 'Can only create store in a group chat')
        return
    
    # Ensure User is creator or adminstrator of chat
    if not isadmin(message.chat, message.from_user):
        return
    
    # Prompt user for store name
    msg = bot.reply_to(message,'What would you like to name your store?', reply_markup=types.ForceReply(True, 'Store Name'))
    bot.register_next_step_handler(msg, created_store)

def created_store(message):
    # Ensure store name is a string
    if not message.text:
        bot.reply_to(message, 'Invalid store name')
        
    # Check if store name already exist
    cursor.execute('SELECT * FROM stores WHERE StoreName = ?', (message.text,))
    rows = cursor.fetchall()
    if len(rows) != 0:
        bot.send_message(message.chat.id, 'Store name has already been taken.')
        return
            
    # Initialise store
    cursor.execute('INSERT INTO stores (id, StoreName) VALUES (?, ?)', (message.chat.id, message.text))
    db.commit()
    bot.send_message(message.chat.id, 'Store successfully initizalised. Enter /start to begin.')


# Enable saving next step handlers
bot.enable_save_next_step_handlers(delay=2)

# Load next step handlers
bot.load_next_step_handlers

# Constantly check for new messages
bot.infinity_polling()