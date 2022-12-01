import telebot
from telebot.util import quick_markup
from telebot import types
import sqlite3
from sqlite3 import Error
import re
import json
from transactions import transaction_info, transaction_markup

# Set API key
API_KEY = '5691173475:AAGF7nfwSMKzd4UyPpveJ2OYuu6PGSTJzLs'
bot = telebot.TeleBot(API_KEY, parse_mode=None)

# Connect to database
try:
    db = sqlite3.connect('stores.db', check_same_thread=False)
except Error as e:
    print(f"Error '{e}' occured when establishing connection to database")
cursor = db.cursor()




def isadmin(chat, user):
    # Check if user is admin in chat
    member = bot.get_chat_member(chat.id, user.id)
    if member.status not in ['creator', 'administrator']:
        bot.send_message(chat.id, 'Sorry you are not an administrator of this chat.')
        return False
    return True

def send_index(chat):
    # Send index options in chat
    bot.send_message(chat.id, 'Choose an option', reply_markup=quick_markup({
                'View Current Stock': {'callback_data': 'View Current Stock'},
                'Add New Item': {'callback_data': 'Add New Item'},
                'Rename Item': {'callback_data': 'Rename Item'},
                'Adjust Quantity/ New Transaction': {'callback_data': 'Adjust Qty'},
                'View Transaction History': {'callback_data': 'View Transaction History'},
                'Edit Store Details': {'callback_data': 'Edit Store Details'}},
                row_width=1))

    
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
            send_index(message.chat)


    # Bot was started in a private chat
    elif message.chat.type == 'private':

        # Ask for store name
        bot.send_message(message.chat.id, 'Enter a store name')
        # Show options










# Handles viewing of stock
@bot.callback_query_handler(func=lambda call: call.data == 'View Current Stock')
def view_stock(call):
    bot.delete_message(call.message.chat.id, call.message.id)
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
    # Ensure user is admin
    if not isadmin(call.message.chat, call.from_user):
        return
    msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this message name of new item.', parse_mode='HTML')
    bot.register_next_step_handler(msg, get_total)

def get_total(message):
    # Ensure message is text
    item = message.text
    if not item:
        bot.reply_to(message, 'Invalid item name.')
    # Check database if item already exist
    cursor.execute('SELECT * FROM stocks WHERE store_id = ? AND ItemName = ?', (message.chat.id, item))
    if len(cursor.fetchall()) != 0:
        bot.reply_to(message, 'Item already exist in store.')
    # Get quantity
    msg = bot.reply_to(message,'Quantity of item?', reply_markup=types.ForceReply(True, 'Quantity of item'))
    bot.register_next_step_handler(msg, get_minimum, item)

def get_minimum(message, item):
    # Validate quantity
    try:
        qty = int(message.text)
        if qty <= 0:
            bot.reply_to(message, 'Invalid Quantity')
            return
    except:
        bot.reply_to(message, 'Invalid Quantity')
        return

    msg = bot.reply_to(message, f"Reply to this message the minimum quantity of '{item}' required in store.\n(Reply '0' if item does not have a mimimum requirement)", reply_markup=types.ForceReply(True, 'Minimum quantity.'))
    bot.register_next_step_handler(msg, add_item, item, qty)

def add_item(message, item, qty):
    # Validate minimum
    try:
        min = int(message.text)
        if min < 0:
            bot.reply_to(message, 'Invalid Quantity')
            return
    except:
        bot.reply_to(message, 'Invalid quantity')
        return
    
    # Add item to database
    cursor.execute('INSERT INTO stocks (store_id, ItemName, Quantity, Min_req) VALUES (?, ?, ?, ?)', (message.chat.id, item, qty, min))
    db.commit()
    bot.send_message(message.chat.id, f'x{qty} {item} has been added to store. (Minimum requirement: {min})')
    send_index(message.chat)




    
# Handles renaming of item
@bot.callback_query_handler(func=lambda call: call.data == 'Rename Item')
def rename_item_query(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Ensure user is admin
    if not isadmin(call.message.chat, call.from_user):
        return

    # Get current items in store
    cursor.execute('SELECT ItemName, stock_id FROM stocks WHERE store_id = ?', (call.message.chat.id,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        bot.send_message(call.message.chat.id, 'There is currently no items in store.')
        return

    # Create markup
    markup = {}
    for item in rows:
        markup[item[0]] = {'callback_data': f'(rename_item) {item[1]}'}

    # Query for item to be renamed
    bot.send_message(call.message.chat.id, 'Choose item to be renamed.', reply_markup=quick_markup(markup, row_width=1))

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(rename_item)')
def new_itemname_query(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get item information
    stock_id = int(call.data.split()[1])
    cursor.execute('SELECT ItemName FROM stocks WHERE stock_id = ?', (stock_id,))
    item = cursor.fetchone()[0]

    # Query for new name
    msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message new name of '{item}'.", parse_mode='HTML')
    bot.register_next_step_handler(msg, rename_item_db, stock_id, item)

def rename_item_db(message, stock_id, item):
    # Validate new name
    new_name = message.text
    if not new_name:
        bot.reply_to(message, 'Invalid item name')
        return
    cursor.execute('SELECT * FROM stocks WHERE ItemName = ? AND store_id = ?', (new_name, message.chat.id))
    if len(cursor.fetchall()) > 0:
        bot.reply_to(message, 'This item is already in store')
        return
    
    # Update database
    cursor.execute('UPDATE stocks SET ItemName = ? WHERE stock_id = ?', (new_name, stock_id))
    db.commit()

    bot.send_message(message.chat.id, f"'{item}' renamed to '{new_name}'.")
    send_index(message.chat)








# Handles quantity adjustment/new transactions
@bot.callback_query_handler(func=lambda call: call.data == 'Adjust Qty')
def choose_type(call):

    # Add default types
    types = {
        'Add New Transaction Type': {'callback_data': 'Add New Transaction Type'},
        'Remove Transaction Type': {'callback_data': 'Remove Transaction Type'},
        'Rename Transaction Type': {'callback_data': 'Rename Transaction Type'},
        'Issue': {'callback_data': '(n_trans) 1'},
        'Loan': {'callback_data': '(n_trans) 2'}
        }
    
    # Get additional transaction types from store
    cursor.execute('SELECT type, id FROM transaction_types WHERE store_id = ?', (call.message.chat.id,))
    rows = cursor.fetchall()
    for row in rows:
        types[row[0]] = {'callback_data': f'(n_trans) {row[1]}'}

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
    msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this message name of new transaction type', parse_mode='HTML')
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
    send_index(message.chat)





# Handles removal of transaction type
@bot.callback_query_handler(func=lambda call: call.data == 'Remove Transaction Type')
def remove_type(call):

    bot.delete_message(call.message.chat.id, call.message.id)

    # Ensure user is admin
    if not isadmin(call.message.chat, call.from_user):
        return

    # Get transaction types
    cursor.execute('SELECT type, id FROM transaction_types WHERE store_id = ?', (call.message.chat.id,))
    types = cursor.fetchall()

    # Ensure that created types exist
    if len(types) == 0:
        bot.send_message(call.message.chat.id, "There are currently no transaction types to be removed.\n<b>Note</b>: 'Issue' and 'Loan' cannot be removed.", parse_mode='HTML')
        send_index(call.message.chat)
        return

    # Create markup
    markup = {}
    for type in types:
        markup[type[0]] = {'callback_data': f'(del_type) {type[1]}'} 

    # Query for type to be removed
    bot.send_message(call.message.chat.id, 'Select Transaction Type to be removed.', reply_markup=quick_markup(markup,row_width=1))

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(del_type)')
def remove_type_db(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    id = int(call.data.split()[1])

    # Get type name
    cursor.execute('SELECT type FROM transaction_types WHERE id = ?', (id,))
    type = cursor.fetchone()[0]

    # Update database
    cursor.execute('DELETE FROM transaction_types WHERE id = ?', (id,))
    db.commit()
    bot.send_message(call.message.chat.id, f"Transaction type '{type}' removed.")
    send_index(call.message.chat)



# Handles renaming of transction type
@bot.callback_query_handler(func=lambda call: call.data == 'Rename Transaction Type')
def rename_transaction_type(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction types
    cursor.execute('SELECT id, type FROM transaction_types WHERE store_id = ?', (call.message.chat.id,))
    types = cursor.fetchall()

    if len(types) == 0:
        bot.send_message(call.message.chat.id, 'Cannot rename Issue and Loan transaction types.')
        return

    # Create markup
    markup = {}
    for type in types:
        markup[type[1]] = {'callback_data': f'(rename_type) {type[0]}'}

    bot.send_message(call.message.chat.id, 'Select transction type to rename.', reply_markup=quick_markup(markup, row_width=1))

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(rename_type)')
def get_new_name(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction type id and name
    id = int(call.data.split()[1])
    cursor.execute('SELECT type FROM transaction_types WHERE id = ?', (id,))
    type = cursor.fetchone()[0]

    # Query for new name
    msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message the new name of '{type}' transaction type", parse_mode='HTML')
    bot.register_next_step_handler(msg, rename_transaction_type_db, id, type)

def rename_transaction_type_db(message, id ,type):

    # Valdiate new name
    new_name = message.text
    if not new_name:
        bot.reply_to(message, 'Invalid type name.')
        return

    cursor.execute('SELECT * FROM transaction_types WHERE store_id = ? AND type = ?', (message.chat.id, new_name))
    if len(cursor.fetchall()) > 0:
        bot.reply_to(message, f'{new_name} transaction type has already been added to store.')
        return

    # Update database
    cursor.execute('UPDATE transaction_types SET type = ? WHERE id = ?', (new_name, id))
    db.commit()

    bot.send_message(message.chat.id, f"'{type}' renamed to '{new_name}'.")
    send_index(message.chat)




# Opens a new transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(n_trans)')
def open_new_transaction(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get items in store
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE store_id = ?', (call.message.chat.id,))
    items = cursor.fetchall()

    # Ensure at least one item
    if len(items) == 0:
        bot.send_message(call.message.chat.id, 'There are no items in currently in this store. Add items to enable transactions.')
        return
    
    type_id=int(call.data.split()[1])

    # Add transaction to database
    cursor.execute('INSERT INTO transactions (store_id, operator, customer, type_id) VALUES (?, ?, ?, ?)', (call.message.chat.id, call.from_user.username, 'NIL', type_id,))
    db.commit()

    # Get transaction id
    id = cursor.lastrowid

    # Get name of transaction type
    cursor.execute('SELECT type FROM transaction_types WHERE id = ?', (type_id,))
    type = cursor.fetchone()[0]

    # Show transaction options
    bot.send_message(call.message.chat.id, f"New transaction of type '{type}' opened, select one of the options to continue.", reply_markup=transaction_markup(id))

    



# Shows items to add to transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(select_add_items)')
def show_add_items(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get current transaction data
    id = int(call.data.split()[1])
    cursor.execute('SELECT type FROM transactions JOIN transaction_types ON transactions.type_id = transaction_types.id WHERE transactions.id = ?', (id,))
    type = cursor.fetchone()[0]
    cursor.execute('SELECT stock_id, change FROM (transactions JOIN transaction_items ON transactions.id = transaction_items.transaction_id) JOIN stocks ON transaction_items.stock_id = stocks.id WHERE transactions.id = ?', (id,))
    rows = cursor.fetchall()

    items = {}
    for row in rows:
        items[row[0]] = row[1]
    
    # Get items in store
    cursor.execute('SELECT id, ItemName, Quantity FROM stocks WHERE store_id = ?', (call.message.chat.id,))
    rows = cursor.fetchall()

    # Show items not in transaction
    markup = {}
    for item in rows:
        if item[0] not in items:
            markup[f'{item[1]} (Current Qty: {item[2]})'] = {'callback_data': f'(add_item) {id} {item[0]}'}
    
    # If every items in store have been added to transactions
    if not markup:
        bot.send_message(call.message.chat.id, "Every item in this store has already been added to transaction." + transaction_info(id, db), reply_markup=transaction_markup(id))
        return

    # If no items in transaction
    if not items:
        bot.send_message(call.message.chat.id, f"Select an item to add to '{type}' transaction.\nNo items currently in transaction.", reply_markup=quick_markup(markup, row_width=1))
        return

    # Query for item to be added
    bot.send_message(call.message.chat.id, f"Select an item to add to '{type}' transaction." + transaction_info(id,db), reply_markup=quick_markup(markup, row_width=1))




# Adds item to transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(add_item)')
def query_change_transaction(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction id and stock id from call
    trans_id = int(call.data.split()[1])
    stock_id = int(call.data.split()[2])

    # Get transaction type
    cursor.execute('SELECT type FROM transactions JOIN transaction_types ON transactions.type_id = transaction_types.id WHERE transactions.id = ?', (trans_id,))
    type = cursor.fetchone()[0]

    # Get item data
    cursor.execute('SELECT ItemName FROM stocks WHERE id = ?', (stock_id,))
    item = cursor.fetchone()[0]

    # Query for increase or decrease
    bot.send_message(call.message.chat.id, f"Is quantity of '{item}' increased or decreased in '{type}' transaction?", reply_markup=quick_markup({ 'Increase': {'callback_data': f'(increase_item) {trans_id} {stock_id}'},
                                                                                                                                                    'Decrease': {'callback_data': f'(decrease_item) {trans_id} {stock_id}'}
                                                                                                                                               }, row_width=1))


@bot.callback_query_handler(func=lambda call:call.data.split()[0] in ['(increase_item)', '(decrease_item)'])
def query_quantity_transactions(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction id and stock id from call
    trans_id = int(call.data.split()[1])
    stock_id = int(call.data.split()[2])

    # Get transaction type
    cursor.execute('SELECT type FROM transactions JOIN transaction_types ON transactions.type_id = transaction_types.id WHERE transactions.id = ?', (trans_id,))
    type = cursor.fetchone()[0]

    # Get item data
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE id = ?', (stock_id,))
    row = cursor.fetchone()
    item = row[0]
    qty = row[1]

    # Query for quantity
    if call.data.split()[0] == '(increase_item)':
        msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message quantity of {item} increased in '{type}' transaction.", parse_mode='HTML')
        bot.register_next_step_handler(msg, add_new_qty, trans_id, stock_id, item, qty, True)
        return
    msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message quantity of {item} decreased in '{type}' transaction.", parse_mode='HTML')
    bot.register_next_step_handler(msg, add_new_qty, trans_id, stock_id, item, qty, False)



def add_new_qty(message, trans_id, stock_id, item, qty, increase):
    # Validate quantity
    try:
        change = int(message.text)
        if change <= 0:
            bot.reply_to(message, 'Invalid Quantity. Quantity must be a positive number.')
            bot.send_message(message.chat.id, 'Error adding item to transaction, choose an option to continue.' + transaction_info(trans_id,db), reply_markup=transaction_markup(trans_id))
            return
        if not increase and (qty - change < 0) :
            bot.reply_to(message, f"Insufficient '{item}' in store. Current quantity: {qty}")
            bot.send_message(message.chat.id, 'Error adding item to transaction, choose an option to continue.' + transaction_info(trans_id,db), reply_markup=transaction_markup(trans_id))
            return
    except:
        bot.reply_to(message, 'Invalid Quantity. Quantity must be a number.')
        bot.send_message(message.chat.id, 'Error adding item to transaction, choose an option to continue.' + transaction_info(trans_id,db), reply_markup=transaction_markup(trans_id))
        return

    # Update database
    if increase:
        cursor.execute('INSERT INTO transaction_items (transaction_id, stock_id, old_qty, change) VALUES (? ,? ,? ,?)', (trans_id, stock_id, qty, change))
        db.commit()
        bot.send_message(message.chat.id, f"x{change} '{item}' has been added to transaction." + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id))
        return
    
    cursor.execute('INSERT INTO transaction_items (transaction_id, stock_id, old_qty, change) VALUES (? ,? ,? ,?)', (trans_id, stock_id, qty, -change))
    db.commit()
    bot.send_message(message.chat.id, f"x{change} '{item}' has been added to transaction." + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id))
    return




# Shows items to remove from transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(select_remove_items)')
def show_remove_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction id
    trans_id = int(call.data.split()[1])

    # Get items in transaction
    cursor.execute('SELECT stock_id, ItemName, change FROM transaction_items JOIN stocks ON transaction_items.stock_id = stocks.id WHERE transaction_id = ?', (trans_id,))
    items = cursor.fetchall()

    # Validate data
    if not items:
        bot.send_message(call.message.chat.id, 'There are no items in this transaction to remove.' + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id))
        return
    
    # Create markup
    markup = {}
    for item in items:
        markup[f'{item[1]}'] = {'callback_data': f'(remove_item) {trans_id} {item[0]}'}

    bot.send_message(call.message.chat.id, 'Select item to remove from transaction.'+ transaction_info(trans_id, db), reply_markup=quick_markup(markup, row_width=1))

    

# Removes item from transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(remove_item)')
def remove_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction id and stock id
    trans_id = int(call.data.split()[1])
    stock_id = int(call.data.split()[2])

    # Get item name
    cursor.execute('SELECT ItemName FROM stocks WHERE id = ?', (stock_id,))
    item = cursor.fetchone()[0]

    # Update database
    cursor.execute('DELETE FROM transaction_items WHERE transaction_id = ? AND stock_id = ?', (trans_id, stock_id))
    db.commit()

    bot.send_message(call.message.chat.id, f"'{item}' has been removed from transaction." + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id))

















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