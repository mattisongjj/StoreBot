import os
from dotenv import load_dotenv
import telebot
from telebot.util import quick_markup
from telebot import types
import sqlite3
from sqlite3 import Error
import datetime
from dateutil.relativedelta import relativedelta
from calendar import month_name
from functions import transaction_info, transaction_markup, isadmin, send_index, private_index, request_markup, request_info
from time import sleep


# Set API key
load_dotenv()
API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY, parse_mode=None)

# Connect to database
try:
    db = sqlite3.connect('stores.db', check_same_thread=False)
except Error as e:
    print(f"Error '{e}' occured when establishing connection to database")

    
# Handles /start command
@bot.message_handler(commands=['start'])
def index(message):
# Start bot
    cursor = db.cursor()

    # Bot was started in a group chat
    if message.chat.type == 'group':

        # Check for existing store
        cursor.execute("SELECT * FROM stores WHERE id = ?", (message.chat.id,))
        rows = cursor.fetchall()
        if len(rows) != 1:
            bot.send_message(message.chat.id, 'This group currently does not have a store. Enter /create_store to initialize store.')
            return
        # Show Group Chat Options
        else:
            send_index(bot, message.chat)


    # Bot was started in a private chat
    elif message.chat.type == 'private':

        # Show Private Chat Options
        private_index(bot, message.chat)


# Handles /help command
@bot.message_handler(commands=['help'])
def help_message(message):

    # Send information about the bot
    if message.chat.type == 'group':
        bot.send_message(message.chat.id, 'To start the bot use the /start command.\nIf you have yet to create a store in this chat by running the /create_store command, please do so before starting the bot.')
        return
    
    else:
        bot.send_message(message.chat.id, 'To start the bot use the /start command.')
        



# Handles viewing of stock/checking of minimum requirement
@bot.callback_query_handler(func=lambda call: call.data == 'View Current Stock')
def view_stock(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Query database for items
    cursor.execute('SELECT ItemName, id FROM stocks WHERE store_id = ? AND is_deleted = FALSE ORDER BY ItemName ASC', (call.message.chat.id,))
    items = cursor.fetchall()
    if len(items) == 0:
        bot.send_message(call.message.chat.id, 'Store does not have any items.')
        send_index(bot, call.message.chat)
        return
    # Display options
    options = {'Back': {'callback_data': '(back_index)'}, 'View Full Stock': {'callback_data': 'View Full Stock'}, 'Check Minimum Requirement': {'callback_data': 'Check Minimum Requirement'}}
    for item in items:
        options[item[0]] = {'callback_data': f'(view) {item[1]}'}
    bot.send_message(call.message.chat.id, 'What would you like to view?', reply_markup=quick_markup(options, row_width=1))

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(view)')
def view_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get stock id
    stock_id = int(call.data.split()[1])

    # Query database
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE id = ? AND is_deleted = FALSE', (stock_id,))
    item = cursor.fetchone()
    bot.send_message(call.message.chat.id, f'Quantity of {item[0]} in store: {item[1]}')
    send_index(bot, call.message.chat)

@bot.callback_query_handler(func=lambda call: call.data == 'View Full Stock')
def full_stock(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Query database for items
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE store_id = ? AND is_deleted = FALSE ORDER BY ItemName ASC', (call.message.chat.id,))
    items = cursor.fetchall()
    reply = '<b>Total Stock</b>\n\n'
    for item in items:
        reply = reply + f'{item[0]} x{item[1]}\n'
    bot.send_message(call.message.chat.id, reply, parse_mode='HTML')
    send_index(bot, call.message.chat)
    

@bot.callback_query_handler(func=lambda call: call.data == 'Check Minimum Requirement')
def check_minimum_requirement(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Query for items below minimum requirement
    cursor.execute('SELECT ItemName, Quantity, Min_req FROM stocks WHERE store_id = ? AND is_deleted = FALSE AND Quantity < Min_req', (call.message.chat.id,))
    items = cursor.fetchall()
    if not items:
        bot.send_message(call.message.chat.id, 'No items in store are below the required amount.')
        send_index(bot, call.message.chat)
        return

    # Create reply
    reply = '<b>Items below minimum requirement</b>\n\n'

    for item in items:
        reply = reply + f'<u><b>{item[0]}</b></u>\n(Current Qty: {item[1]}, Required Quantity: {item[2]}, Deficit: {item[2] - item[1]})\n'
    
    bot.send_message(call.message.chat.id, reply, parse_mode='HTML')
    send_index(bot, call.message.chat)



# Shows options to manange items in store
@bot.callback_query_handler(func=lambda call: call.data == 'Manage Items')
def add_remove_rename_options(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Ensure user is admin
    if not isadmin(bot, call.message.chat, call.from_user):
        send_index(bot, call.message.chat)
        return

    # Create markup
    markup = quick_markup({'Back': {'callback_data': '(back_index)'}, 'Add New Item': {'callback_data': 'Add New Item'}, 'Rename Item': {'callback_data': 'Rename Item'}, 'Remove Item': {'callback_data': 'Remove Item'}}, row_width=1)

    bot.send_message(call.message.chat.id, 'Select an option.', reply_markup=markup)





# Handles creation of new item
@bot.callback_query_handler(func=lambda call: call.data == 'Add New Item')
def new_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Ensure user is admin
    if not isadmin(bot, call.message.chat, call.from_user):
        send_index(bot, call.message.chat)
        return
    msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this message name of new item.', reply_markup=types.ForceReply(True, 'Name of new item'),parse_mode='HTML')
    bot.register_next_step_handler(msg, get_total)

def get_total(message):
    cursor = db.cursor()

    # Ensure message is text
    item = message.text
    if not item:
        bot.reply_to(message, 'Invalid item name.')
    # Check database if item already exist in store
    cursor.execute('SELECT * FROM stocks WHERE store_id = ? AND ItemName = ? AND is_deleted = FALSE', (message.chat.id, item))
    if len(cursor.fetchall()) != 0:
        bot.reply_to(message, 'Item already exist in store.')
    # Get quantity
    msg = bot.reply_to(message, f'<b>Reply</b> to this message quantity of {item} added to store.', reply_markup=types.ForceReply(True, 'Quantity'), parse_mode='HTML')
    bot.register_next_step_handler(msg, get_minimum, item)

def get_minimum(message, item):
    # Validate quantity
    try:
        qty = int(message.text)
        if qty <= 0:
            bot.reply_to(message, 'Invalid Quantity')
            send_index(bot, message.chat)
            return
    except:
        bot.reply_to(message, 'Invalid Quantity')
        send_index(bot, message.chat)
        return

    msg = bot.reply_to(message, f"<b>Reply</b> to this message the minimum quantity of '{item}' required in store.\n(Reply '0' if item does not have a mimimum requirement)", reply_markup=types.ForceReply(True, 'Minimum Quantity'), parse_mode='HTML')
    bot.register_next_step_handler(msg, add_item, item, qty)

def add_item(message, item, qty):
    cursor = db.cursor()

    # Ensure user has username
    if not message.from_user.username:
        bot.send_message(message.chat.id, 'Please add a telegram username to your telegram account use the bot as intended.')
        send_index(bot, message.chat)
        return

    # Validate minimum
    try:
        min = int(message.text)
        if min < 0:
            bot.reply_to(message, 'Invalid Quantity')
            send_index(bot, message.chat)
            return
    except:
        bot.reply_to(message, 'Invalid quantity')
        send_index(bot, message.chat)
        return

    # Check is item has been deleted before
    cursor.execute('SELECT id FROM stocks WHERE store_id = ? AND ItemName = ? AND is_deleted = TRUE', (message.chat.id, item))
    try:
        stock_id = cursor.fetchone()[0]
        cursor.execute('UPDATE stocks SET quantity = ?, Min_req = ?, is_deleted = FALSE WHERE id = ?', (qty, min, stock_id))
        db.commit()
    except:
        cursor.execute('INSERT INTO stocks (store_id, ItemName, Quantity, Min_req) VALUES (?, ?, ?, ?)', (message.chat.id, item, qty, min))
        db.commit()
        stock_id = cursor.lastrowid

    # Update transactions
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    cursor.execute('INSERT INTO transactions (store_id, operator, type_id, datetime, confirmed) VALUES (?, ?, ?, ?, TRUE)', (message.chat.id, message.from_user.username, 3, time))
    db.commit()
    trans_id = cursor.lastrowid
    cursor.execute('INSERT INTO transaction_items (transaction_id, stock_id, old_qty, change) VALUES (?, ?, 0, ?)', (trans_id, stock_id, qty))

    bot.send_message(message.chat.id, f'x{qty} {item} has been added to store.\n(Minimum requirement: {min})')
    bot.send_message(message.chat.id, '<b>New Transaction Added</b>' + transaction_info(trans_id, db), parse_mode='HTML')
    send_index(bot, message.chat)




    
# Handles renaming of item
@bot.callback_query_handler(func=lambda call: call.data == 'Rename Item')
def rename_item_query(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Ensure user is admin
    if not isadmin(bot, call.message.chat, call.from_user):
        send_index(bot, call.message.chat)
        return

    # Get current items in store
    cursor.execute('SELECT ItemName, id FROM stocks WHERE store_id = ? AND is_deleted = FALSE', (call.message.chat.id,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        bot.send_message(call.message.chat.id, 'There is currently no items in store to rename.')
        send_index(bot, call.message.chat)
        return

    # Create markup
    markup = {'Back': {'callback_data': 'Manage Items'}}
    for item in rows:
        markup[item[0]] = {'callback_data': f'(rename_item) {item[1]}'}

    # Query for item to be renamed
    bot.send_message(call.message.chat.id, 'Choose item to be renamed.', reply_markup=quick_markup(markup, row_width=1))

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(rename_item)')
def rename_item_query(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get item information
    stock_id = int(call.data.split()[1])
    cursor.execute('SELECT ItemName FROM stocks WHERE id = ?', (stock_id,))
    item = cursor.fetchone()[0]

    # Query for new name
    msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message new name of '{item}'.", reply_markup=types.ForceReply(True, 'New Name'), parse_mode='HTML')
    bot.register_next_step_handler(msg, rename_item_db, stock_id, item)

def rename_item_db(message, stock_id, item):
    cursor = db.cursor()

    # Validate new name
    new_name = message.text
    if not new_name:
        bot.reply_to(message, 'Invalid item name')
        return
    cursor.execute('SELECT * FROM stocks WHERE ItemName = ? AND store_id = ? AND is_deleted = FALSE', (new_name, message.chat.id))
    if len(cursor.fetchall()) > 0:
        bot.reply_to(message, 'This item is already in store')
        send_index(bot, message.chat)
        return

    # Update database
    cursor.execute('UPDATE stocks SET ItemName = ? WHERE id = ?', (new_name, stock_id))
    db.commit()

    bot.send_message(message.chat.id, f"'{item}' renamed to '{new_name}'.")
    send_index(bot, message.chat)



# Handles removing of items
@bot.callback_query_handler(func=lambda call: call.data == 'Remove Item')
def remove_item_query(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Ensure user is admin
    if not isadmin(bot, call.message.chat, call.from_user):
        send_index(bot, call.message.chat)
        return
    
    # Get items in store
    cursor.execute('SELECT ItemName, id, Quantity FROM stocks WHERE store_id = ? AND is_deleted = FALSE', (call.message.chat.id,))
    rows = cursor.fetchall()
    if len(rows) == 0:
        bot.send_message(call.message.chat.id, 'There is currently no items in store to remove.')
        send_index(bot, call.message.chat)
        return

    # Create markup
    markup = {'Back': {'callback_data': 'Manage Items'}}
    for item in rows:
        markup[f'{item[0]} ({item[2]})'] = {'callback_data': f'(remove_item) {item[1]}'}
    
    # Query for item to be removed
    bot.send_message(call.message.chat.id, f"Select an item to remove from store.", reply_markup=quick_markup(markup, row_width=1))

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(remove_item)')
def remove_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Ensure user has username
    if not call.from_user.username:
        bot.send_message(call.message.chat.id, 'Please add a telegram username to your telegram account use the bot as intended.')
        send_index(bot, call.message.chat)
        return

    # Get stock id
    stock_id = int(call.data.split()[1])

    # Get item name and quantity
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE id = ?', (stock_id,))
    row = cursor.fetchone()
    item = row[0]
    quantity = row[1]

    # Remove item from store
    cursor.execute('UPDATE stocks SET is_deleted = TRUE WHERE id = ?', (stock_id,))
    db.commit()

    # Update transactions
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    cursor.execute('INSERT INTO transactions (store_id, operator, type_id, datetime, confirmed) VALUES (?, ?, ?, ?, TRUE)', (call.message.chat.id, call.from_user.username, 4, time))
    db.commit()
    trans_id = cursor.lastrowid
    cursor.execute('INSERT INTO transaction_items (transaction_id, stock_id, old_qty, change) VALUES (?, ?, ?, ?)', (trans_id, stock_id, quantity, -quantity))
    db.commit()


    bot.send_message(call.message.chat.id, f"'{item}' has been removed from store.")
    bot.send_message(call.message.chat.id, '<b>New Transaction Added</b>' + transaction_info(trans_id, db), parse_mode='HTML')
    send_index(bot, call.message.chat)













# Handles quantity adjustment/new transactions
@bot.callback_query_handler(func=lambda call: call.data == 'Adjust Qty')
def choose_type(call):
    cursor = db.cursor()

    # Add default types
    types = {
        'Back': {'callback_data': '(back_index)'},
        'Add New Transaction Type': {'callback_data': 'Add New Transaction Type'},
        'Remove Transaction Type': {'callback_data': 'Remove Transaction Type'},
        'Rename Transaction Type': {'callback_data': 'Rename Transaction Type'},
        'Issue': {'callback_data': '(n_trans) 1'},
        'Loan': {'callback_data': '(n_trans) 2'}
        }
    
    # Get additional transaction types from store
    cursor.execute('SELECT type, id FROM transaction_types WHERE store_id = ? AND is_deleted = FALSE', (call.message.chat.id,))
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
    bot.delete_message(call.message.chat.id, call.message.id)
    # Ensure user is admin
    if not isadmin(bot, call.message.chat, call.from_user):
        send_index(bot, call.message.chat)
        return
    # Get type name
    msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this message name of new transaction type', reply_markup=types.ForceReply(True, 'Name of new transaction type'),parse_mode='HTML')
    bot.register_next_step_handler(msg, add_type)

def add_type(message):
    type = message.text
    cursor = db.cursor()

    # Validate type
    cursor.execute('SELECT * FROM transaction_types WHERE store_id = ? AND type = ? AND is_deleted = FALSE', (message.chat.id, type))
    if len(cursor.fetchall()) != 0 or not type:
        bot.reply_to(message, 'Invalid type name.')
        return
    # Check if transaction type has been deleted before
    cursor.execute('SELECT id FROM transaction_types WHERE store_id = ? AND type = ? AND is_deleted = TRUE', (message.chat.id, type))
    try:
        deleted_id = cursor.fetchone()[0]
        cursor.execute('UPDATE transaction_types SET is_deleted = FALSE WHERE id = ?', (deleted_id,))
        db.commit()
    except:
        # Add type to database
        cursor.execute('INSERT INTO transaction_types (store_id, type) VALUES (?, ?)', (message.chat.id, type))
        db.commit()
    bot.reply_to(message, 'New type successfully added.')
    send_index(bot, message.chat)





# Handles removal of transaction type
@bot.callback_query_handler(func=lambda call: call.data == 'Remove Transaction Type')
def remove_type(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Ensure user is admin
    if not isadmin(bot, call.message.chat, call.from_user):
        send_index(bot, call.message.chat)
        return

    # Get transaction types
    cursor.execute('SELECT type, id FROM transaction_types WHERE store_id = ? AND is_deleted = FALSE', (call.message.chat.id,))
    types = cursor.fetchall()

    # Ensure that created types exist
    if len(types) == 0:
        bot.send_message(call.message.chat.id, "There are currently no transaction types to be removed.\n<b>Note</b>: 'Issue' and 'Loan' cannot be removed.", parse_mode='HTML')
        send_index(bot, call.message.chat)
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
    cursor = db.cursor()

    id = int(call.data.split()[1])

    # Get type name
    cursor.execute('SELECT type FROM transaction_types WHERE id = ?', (id,))
    type = cursor.fetchone()[0]

    # Update database
    cursor.execute('UPDATE transaction_types SET is_deleted = TRUE WHERE id = ?', (id,))
    db.commit()
    bot.send_message(call.message.chat.id, f"Transaction type '{type}' removed.")
    send_index(bot, call.message.chat)



# Handles renaming of transction type
@bot.callback_query_handler(func=lambda call: call.data == 'Rename Transaction Type')
def rename_transaction_type(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get transaction types
    cursor.execute('SELECT id, type FROM transaction_types WHERE store_id = ? AND is_deleted = FALSE', (call.message.chat.id,))
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
    cursor = db.cursor()

    # Get transaction type id and name
    id = int(call.data.split()[1])
    cursor.execute('SELECT type FROM transaction_types WHERE id = ?', (id,))
    type = cursor.fetchone()[0]

    # Query for new name
    msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message the new name of '{type}' transaction type", reply_markup=types.ForceReply(True, 'New Name'), parse_mode='HTML')
    bot.register_next_step_handler(msg, rename_transaction_type_db, id, type)

def rename_transaction_type_db(message, id ,type):
    cursor = db.cursor()

    # Valdiate new name
    new_name = message.text
    if not new_name:
        bot.reply_to(message, 'Invalid type name.')
        return

    cursor.execute('SELECT * FROM transaction_types WHERE store_id = ? AND type = ? AND is_deleted = FALSE', (message.chat.id, new_name))
    if len(cursor.fetchall()) > 0:
        bot.reply_to(message, f'{new_name} transaction type has already been added to store.')
        send_index(bot, message.chat)
        return

    # Update database
    cursor.execute('UPDATE transaction_types SET type = ? WHERE id = ?', (new_name, id))
    db.commit()

    bot.send_message(message.chat.id, f"'{type}' renamed to '{new_name}'.")
    send_index(bot, message.chat)




# Opens a new transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(n_trans)')
def open_new_transaction(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Ensure user has username
    if not call.from_user.username:
        bot.send_message(call.message.chat.id, 'Please add a telegram username to your telegram account use the bot as intended.')
        send_index(bot, call.message.chat)
        return

    # Check for existing transaction
    cursor.execute('SELECT id FROM transactions WHERE store_id = ? AND confirmed = FALSE', (call.message.chat.id,))
    existing_id = cursor.fetchone()
    if existing_id:
        bot.send_message(call.message.chat.id, '<b>Unconfirmed transaction found</b>\n\nConfirm or cancel transaction to start a new transaction.' + transaction_info(existing_id[0], db), reply_markup=transaction_markup(existing_id[0]), parse_mode='HTML')
        return
    
    # Get items in store
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE store_id = ? AND is_deleted = FALSE', (call.message.chat.id,))
    items = cursor.fetchall()

    # Ensure at least one item
    if len(items) == 0:
        bot.send_message(call.message.chat.id, 'There are no items in currently in this store. Add items to enable transactions.')
        return
    
    type_id=int(call.data.split()[1])

    # Add transaction to database
    cursor.execute('INSERT INTO transactions (store_id, operator, type_id) VALUES (?, ?, ?)', (call.message.chat.id, call.from_user.username, type_id,))
    db.commit()

    # Get transaction id
    trans_id = cursor.lastrowid

    # Get name of transaction type
    cursor.execute('SELECT type FROM transaction_types WHERE id = ?', (type_id,))
    type = cursor.fetchone()[0]

    # Show transaction options
    bot.send_message(call.message.chat.id, f"New transaction of type '{type}' opened. Choose an option to continue" + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')

    



# Shows items to add to transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(select_add_items)')
def show_add_items(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

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
    cursor.execute('SELECT id, ItemName, Quantity FROM stocks WHERE store_id = ? AND is_deleted = FALSE ORDER BY ItemName ASC', (call.message.chat.id,))
    rows = cursor.fetchall()

    # Show items not in transaction
    markup = {}
    for item in rows:
        if item[0] not in items:
            markup[f'{item[1]} (Current Qty: {item[2]})'] = {'callback_data': f'(add_item) {id} {item[0]}'}
    
    # If every items in store have been added to transactions
    if not markup:
        bot.send_message(call.message.chat.id, "Every item in this store has already been added to transaction." + transaction_info(id, db), reply_markup=transaction_markup(id), parse_mode='HTML')
        return

    # Add back option
    markup['Back'] = {'callback_data': f'(back_trans) {id}'}

    # Query for item to be added
    bot.send_message(call.message.chat.id, f"Select an item to add to '{type}' transaction." + transaction_info(id,db), reply_markup=quick_markup(markup, row_width=1), parse_mode='HTML')




# Adds item to transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(add_item)')
def query_change_transaction(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get transaction id and stock id from call
    trans_id = int(call.data.split()[1])
    stock_id = int(call.data.split()[2])

    # Get transaction type
    cursor.execute('SELECT type FROM transactions JOIN transaction_types ON transactions.type_id = transaction_types.id WHERE transactions.id = ?', (trans_id,))
    type = cursor.fetchone()[0]

    # Get item data
    cursor.execute('SELECT ItemName FROM stocks WHERE id = ?', (stock_id,))
    item = cursor.fetchone()[0]

    # Create markup
    markup = quick_markup({ 'Increase': {'callback_data': f'(increase_item) {trans_id} {stock_id}'}, 'Decrease': {'callback_data': f'(decrease_item) {trans_id} {stock_id}'}}, row_width=1)
    # Query for increase or decrease
    bot.send_message(call.message.chat.id, f"Is quantity of '{item}' in stock increased or decreased in '{type}' transaction?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call:call.data.split()[0] in ['(increase_item)', '(decrease_item)'])
def query_quantity_transactions(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

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
        msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message quantity of {item} increased in '{type}' transaction.", reply_markup=types.ForceReply(True, 'Quantity Increased'), parse_mode='HTML')
        bot.register_next_step_handler(msg, add_new_qty, trans_id, stock_id, item, qty, True)
        return
    msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message quantity of {item} decreased in '{type}' transaction.", reply_markup=types.ForceReply(True, 'Quantity Decreased'), parse_mode='HTML')
    bot.register_next_step_handler(msg, add_new_qty, trans_id, stock_id, item, qty, False)



def add_new_qty(message, trans_id, stock_id, item, qty, increase):
    cursor = db.cursor()

    # Validate quantity
    try:
        change = int(message.text)
        if change <= 0:
            bot.reply_to(message, 'Invalid Quantity. Quantity must be a positive number.')
            bot.send_message(message.chat.id, 'Error adding item to transaction, choose an option to continue.' + transaction_info(trans_id,db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
            return
        if not increase and (qty - change < 0) :
            bot.reply_to(message, f"Insufficient '{item}' in store. Current quantity: {qty}")
            bot.send_message(message.chat.id, 'Error adding item to transaction, choose an option to continue.' + transaction_info(trans_id,db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
            return
    except:
        bot.reply_to(message, 'Invalid Quantity. Quantity must be a number.')
        bot.send_message(message.chat.id, 'Error adding item to transaction, choose an option to continue.' + transaction_info(trans_id,db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
        return

    # Update database
    if increase:
        cursor.execute('INSERT INTO transaction_items (transaction_id, stock_id, old_qty, change) VALUES (? ,? ,? ,?)', (trans_id, stock_id, qty, change))
        db.commit()
        bot.send_message(message.chat.id, f"x{change} '{item}' has been added to transaction." + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
        return
    
    cursor.execute('INSERT INTO transaction_items (transaction_id, stock_id, old_qty, change) VALUES (? ,? ,? ,?)', (trans_id, stock_id, qty, -change))
    db.commit()
    bot.send_message(message.chat.id, f"x{change} '{item}' has been added to transaction." + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
    return




# Shows items to remove from transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(select_remove_items)')
def show_remove_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get transaction id
    trans_id = int(call.data.split()[1])

    # Get items in transaction
    cursor.execute('SELECT stock_id, ItemName, change FROM transaction_items JOIN stocks ON transaction_items.stock_id = stocks.id WHERE transaction_id = ? ORDER BY ItemName ASC', (trans_id,))
    items = cursor.fetchall()

    # Validate data
    if not items:
        bot.send_message(call.message.chat.id, 'There are no items in this transaction to remove.' + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
        return
    
    # Create markup
    markup = {}
    for item in items:
        markup[f'{item[1]}'] = {'callback_data': f'(remove_item_trans) {trans_id} {item[0]}'}
    
    # Add back option
    markup['Back'] = {'callback_data': f'(back_trans) {trans_id}'}

    bot.send_message(call.message.chat.id, 'Select item to remove from transaction.'+ transaction_info(trans_id, db), reply_markup=quick_markup(markup, row_width=1), parse_mode='HTML')

    

# Removes item from transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(remove_item_trans)')
def remove_item(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get transaction id and stock id
    trans_id = int(call.data.split()[1])
    stock_id = int(call.data.split()[2])

    # Get item name
    cursor.execute('SELECT ItemName FROM stocks WHERE id = ?', (stock_id,))
    item = cursor.fetchone()[0]

    # Update database
    cursor.execute('DELETE FROM transaction_items WHERE transaction_id = ? AND stock_id = ?', (trans_id, stock_id))
    db.commit()

    bot.send_message(call.message.chat.id, f"'{item}' has been removed from transaction." + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')



# Handles adding of customer to transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(add_customer)')
def query_customer(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction id
    trans_id = int(call.data.split()[1])

    # Query for customer name
    msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message name of customer.", reply_markup=types.ForceReply(True, 'Customer Name'), parse_mode='HTML')
    bot.register_next_step_handler(msg, add_customer, trans_id)

def add_customer(message, trans_id):
    cursor = db.cursor()

    # Validate customer name
    customer = message.text
    if not customer:
        bot.reply_to(message, 'Invalid Customer Name.')
        bot.send_message(message.chat.id, 'Error adding customer to transaction, choose an option to continue.' + transaction_info(trans_id,db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
        return

    # Update database
    cursor.execute('UPDATE transactions SET customer = ? WHERE id = ?', (customer, trans_id))
    db.commit()
    bot.send_message(message.chat.id, f"'{customer}' has been set as customer for transaction." + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')



# Handles removal of customer from transaction
@bot.callback_query_handler(func= lambda call: call.data.split()[0] == '(remove_customer)')
def remove_customer(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get transaction id
    trans_id = int(call.data.split()[1])

    # Check for existing customer
    cursor.execute('SELECT customer FROM transactions WHERE id = ?', (trans_id,))
    customer = cursor.fetchone()[0]
    if customer == 'NIL':
        bot.send_message(call.message.chat.id, 'No customer in current transaction to remove.' + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
        return

    # Remove customer
    cursor.execute('UPDATE transactions SET customer = ? WHERE id = ?', ('NIL', trans_id))
    db.commit()

    bot.send_message(call.message.chat.id, f"'{customer}' has been removed as customer for transaction." + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')



# Handles confirming of transaction
@bot.callback_query_handler(func=lambda call:call.data.split()[0] == '(confirm)')
def confirm_transaction_info(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get transaction id
    trans_id = int(call.data.split()[1])

    # Validate transaction
    cursor.execute('SELECT stock_id FROM transaction_items WHERE transaction_id = ?', (trans_id,))
    if len(cursor.fetchall()) == 0:
        bot.send_message(call.message.chat.id, 'Must have at least one item in transaction to confirm transaction.' + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')
        return
    cursor.execute('SELECT * FROM transactions WHERE id = ? AND confirmed = TRUE', (trans_id,))
    if cursor.fetchone():
        bot.send_message(call.message.chat.id, 'This transaction has already been confirmed.')
        send_index(bot, call.message.chat)
        return
    
    # Check for customer
    cursor.execute('SELECT customer FROM transactions WHERE id = ?', (trans_id,))
    customer = cursor.fetchone()[0]

    # Create markup
    markup = quick_markup({'Confirm': {'callback_data': f'(confirm_transaction) {trans_id}'},
                            'Back': {'callback_data': f'(back_trans) {trans_id}'},}
                            ,row_width=1)
    if customer != 'NIL':
        bot.send_message(call.message.chat.id, 'Confirm the following transaction?' + transaction_info(trans_id, db), reply_markup=markup, parse_mode='HTML')
        return
    bot.send_message(call.message.chat.id, 'Confirm the following transaction?\n(<b>NOTE</b>: No customer has been added)' + transaction_info(trans_id, db), reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(confirm_transaction)')
def confirm_transaction(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get transaction id
    trans_id = int(call.data.split()[1])
    
    # Validate transaction
    cursor.execute('SELECT * FROM transactions WHERE id = ? AND confirmed = TRUE', (trans_id,))
    if cursor.fetchone():
        bot.send_message(call.message.chat.id, 'This transaction has already been confirmed.')
        send_index(bot, call.message.chat)
        return

    # Get item changes
    cursor.execute('SELECT stock_id, old_qty, change, ItemName, Min_req FROM transaction_items JOIN stocks ON transaction_items.stock_id = stocks.id WHERE transaction_id = ?', (trans_id,))
    changes = cursor.fetchall()

    # Update item quantity, saving items that go below minimum requirement
    below_minreq = []
    for change in changes:
        new_qty = change[1] + change[2]
        if new_qty < change[4]:
            below_minreq.append((change[3], new_qty, change[4]))
        cursor.execute('UPDATE stocks SET quantity = ? WHERE id = ?', (new_qty, change[0]))
        db.commit()


    # Confirm transaction
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    cursor.execute('UPDATE transactions SET datetime = ?, confirmed = TRUE WHERE id = ?', (time, trans_id))
    db.commit()
    bot.send_message(call.message.chat.id, '<b>New transaction added.</b>' + transaction_info(trans_id, db), parse_mode='HTML')

    # Notify user of items belows minimum requirement
    if below_minreq:
        reply = '<b>NOTE: New items from transaction below minimum requirement</b>\n\n'
        for item in below_minreq:
            reply = reply + f'<b>{item[0]}</b> (Current Qty: {item[1]}, Required Quantity: {item[2]}, Deficit: {item[2] - item[1]})\n'
        bot.send_message(call.message.chat.id, reply, parse_mode='HTML')
        send_index(bot, call.message.chat)
        return

    send_index(bot, call.message.chat)




# Handles cancellation of transaction
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(cancel)')
def cancel_transaction_info(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction id
    trans_id = int(call.data.split()[1])

    # Create markup
    markup = quick_markup({'Cancel': {'callback_data': f'(cancel_transaction) {trans_id}'},
                            'Back': {'callback_data': f'(back_trans) {trans_id}'}},
                            row_width=1)
    bot.send_message(call.message.chat.id, 'Cancel the following transaction?' + transaction_info(trans_id, db), reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(cancel_transaction)')
def cancel_transaction(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get transaction id
    trans_id = int(call.data.split()[1])

    # Save transaction information
    info = transaction_info(trans_id, db)

    # Update database
    cursor.execute('DELETE FROM transactions WHERE id = ?', (trans_id,))
    cursor.execute('DELETE FROM transaction_items WHERE transaction_id = ?', (trans_id,))
    db.commit()

    bot.send_message(call.message.chat.id, '<b>Transaction Cancelled.</b>' + info, parse_mode='HTML')
    send_index(bot, call.message.chat)




# Handles back button for transactions
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(back_trans)')
def back_trans(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get transaction id
    trans_id = int(call.data.split()[1])

    bot.send_message(call.message.chat.id, 'Choose an option to continue.' + transaction_info(trans_id, db), reply_markup=transaction_markup(trans_id), parse_mode='HTML')








# Handles viewing of transaction history
@bot.callback_query_handler(func=lambda call: call.data == 'View Transaction History')
def query_time_period(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Create markup
    markup = quick_markup(
        {'Back': {'callback_data': '(back_index)'},
        'Day': {'callback_data': '(hist_time) day'},
        'Month': {'callback_data': '(hist_time) month'},
        }, row_width=1
    )

    bot.send_message(call.message.chat.id, 'Select a time period for transaction history viewing', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(hist_time)')
def query_time_period2(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get time period
    time_period = call.data.split()[1]

    if time_period == 'day':
        msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this message the date for transaction history viewing in the format (DD/MM/YYYY).\n(<b>For example</b>: 21/11/2002)', parse_mode='HTML')
        bot.register_next_step_handler(msg, query_history_item, time_period)
    elif time_period == 'month':
        msg = bot.send_message(call.message.chat.id, "<b>Reply</b> to this message the month and year for transaction history viewing in the format (MM/YYYY).\n(<b>For example</b>: '06/2021' for June 2021)", parse_mode='HTML')
        bot.register_next_step_handler(msg, query_history_item, time_period)


def query_history_item(message, time_period):
    cursor = db.cursor()

    # Validate time period
    message_data = message.text
    if not message_data:
        bot.reply_to(message, 'Invalid time period.')
        send_index(bot, message.chat)
        return
    # Validate day
    if time_period == 'day':
        try:
            ddmmyyyy = list(map(int, message_data.split('/')))
            date = datetime.datetime(year=ddmmyyyy[2], month=ddmmyyyy[1], day=ddmmyyyy[0]).strftime('%d/%m/%Y')
        except:
            bot.reply_to(message, 'Invalid date, ensure to reply a valid date in the format (DD/MM/YYYY).')
            send_index(bot, message.chat)
            return
        # Get items in store
        cursor.execute('SELECT id, ItemName FROM stocks WHERE store_id = ?', (message.chat.id,))
        items = cursor.fetchall()
        if not items:
            bot.send_message(message.chat.id, 'No items in store, add items to store to view transaction history.')
            send_index(bot, message.chat)
            return
        # Create markup
        markup = {'Back': {'callback_data': 'View Transaction History'}, 'All Items': {'callback_data': f'(hist_item_day) all {date}'}}
        for item in items:
            markup[item[1]] = {'callback_data': f'(hist_item_day) {item[0]} {date}'}
        bot.send_message(message.chat.id, f'Select an item for transactions on {date}', reply_markup=quick_markup(markup, row_width=1))
    # Validate month
    elif time_period == 'month':
        try:
            mmyyyy = list(map(int, message_data.split('/')))
            month = datetime.datetime(year=mmyyyy[1], month=mmyyyy[0], day=1).strftime('%d/%m/%Y')
        except:
            bot.reply_to(message, 'Invalid month ensure to reply a number')
            send_index(bot, message.chat)
            return
        # Get items in store
        cursor.execute('SELECT id, ItemName FROM stocks WHERE store_id = ?', (message.chat.id,))
        items = cursor.fetchall()
        if not items:
            bot.send_message(message.chat.id, 'No items in store, add items to store to view transaction history.')
            send_index(bot, message.chat)
            return
        # Create markup
        markup = {'Back': {'callback_data': 'View Transaction History'}, 'All Items': {'callback_data': f'(hist_item_month) all {month}'}}
        for item in items:
            markup[item[1]] = {'callback_data': f'(hist_item_month) {item[0]} {month}'}
        bot.send_message(message.chat.id, f'Select an item for transactions during {month_name[mmyyyy[0]]} {mmyyyy[1]}', reply_markup=quick_markup(markup, row_width=1))



@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(hist_item_day)')
def history_day(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get stock id, ItemName and date
    date = datetime.datetime.strptime(call.data.split()[2], '%d/%m/%Y')
    try:
        stock_id = int(call.data.split()[1])
        cursor.execute('SELECT ItemName FROM stocks WHERE id = ?', (stock_id,))
        item = cursor.fetchone()[0]
    except:
    # If User wants to view every item

        # Get transactions 
        cursor.execute('SELECT id, datetime FROM transactions WHERE datetime < ? AND datetime > ? AND store_id = ?', (date + datetime.timedelta(days=1), date - datetime.timedelta(days=1), call.message.chat.id))
        transactions = cursor.fetchall()
        if not transactions:
            bot.send_message(call.message.chat.id, f'No transactions occured on {call.data.split()[2]}')
            send_index(bot, call.message.chat)
            return
        
        # Send transaction history
        bot.send_message(call.message.chat.id, f'<u>Transaction History Report on {call.data.split()[2]}</u>', parse_mode='HTML')
        for transaction in transactions:
            bot.send_message(call.message.chat.id, f'<b>Date</b>: {transaction[1].split()[0]}\n<b>Time</b>: {transaction[1].split()[1]}' + transaction_info(transaction[0], db), parse_mode='HTML')
            sleep(2.5)
        send_index(bot, call.message.chat)
        return
    
    # Get transactions 
    cursor.execute('SELECT id, datetime FROM transactions JOIN transaction_items ON transactions.id = transaction_items.transaction_id WHERE stock_id = ? AND datetime < ? AND datetime > ?', (stock_id, date + datetime.timedelta(days=1), date - datetime.timedelta(days=1)))
    transactions = cursor.fetchall()
    if not transactions:
        bot.send_message(call.message.chat.id, f"No transactions involving '{item}' on {call.data.split()[2]}")
        send_index(bot, call.message.chat)
        return
    
    # Send transaction history
    bot.send_message(call.message.chat.id, f"<u>Transaction History Report on {call.data.split()[2]} involving '{item}'</u>", parse_mode='HTML')
    for transaction in transactions:
        bot.send_message(call.message.chat.id, f'<b>Date</b>: {transaction[1].split()[0]}\n<b>Time</b>: {transaction[1].split()[1]}' + transaction_info(transaction[0], db), parse_mode='HTML')
        sleep(2.5)
    send_index(bot, call.message.chat)



@bot.callback_query_handler(func=lambda call : call.data.split()[0] == '(hist_item_month)')
def history_month(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get stock id, ItemName and date
    date = datetime.datetime.strptime(call.data.split()[2], '%d/%m/%Y')
    try:
        stock_id = int(call.data.split()[1])
        cursor.execute('SELECT ItemName FROM stocks WHERE id = ?', (stock_id,))
        item = cursor.fetchone()[0]
    except:
        # User wants to view all items

        # Get transactions
        cursor.execute('SELECT id, datetime FROM transactions WHERE datetime < ? AND datetime > ? AND store_id = ?', (date + relativedelta(months=+1), date + relativedelta(months=-1), call.message.chat.id))
        transactions = cursor.fetchall()
        if not transactions:
            bot.send_message(call.message.chat.id, f'No transactions occured during {month_name[date.month]} {date.year}.')
            send_index(bot, call.message.chat.id)
            return
        
        # Send transaction history
        bot.send_message(call.message.chat.id, f'<u>Transaction History Report for {month_name[date.month]} {date.year}</u>', parse_mode='HTML')
        for transaction in transactions:
            bot.send_message(call.message.chat.id, f'<b>Date</b>: {transaction[1].split()[0]}\n<b>Time</b>: {transaction[1].split()[1]}' + transaction_info(transaction[0], db), parse_mode='HTML')
            sleep(2.5)
        send_index(bot, call.message.chat)
        return

    # Get transactions 
    cursor.execute('SELECT id, datetime FROM transactions JOIN transaction_items ON transactions.id = transaction_items.transaction_id WHERE stock_id = ? AND datetime < ? AND datetime > ?', (stock_id, date + relativedelta(months=+1), date + relativedelta(months=-1)))
    transactions = cursor.fetchall()
    if not transactions:
        bot.send_message(call.message.chat.id, f"No transactions involving '{item}' during {month_name[date.month]} {date.year}.")
        send_index(bot, call.message.chat)
        return
    
    # Send transaction history
    bot.send_message(call.message.chat.id, f"<u>Transaction History Report for {month_name[date.month]} {date.year} involving '{item}'</u>", parse_mode='HTML')
    for transaction in transactions:
        bot.send_message(call.message.chat.id, f'<b>Date</b>: {transaction[1].split()[0]}\n<b>Time</b>: {transaction[1].split()[1]}' + transaction_info(transaction[0], db), parse_mode='HTML')
        sleep(2.5)
    send_index(bot, call.message.chat)









# Handles editing of store details
@bot.callback_query_handler(func=lambda call : call.data == 'Edit Store Details')
def edit_store_details(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Ensure user is administrator
    if not isadmin(bot, call.message.chat, call.from_user):
        send_index(bot, call.message.chat)
        return

    # Get current store details
    cursor.execute('SELECT StoreName, contact FROM stores WHERE id = ?', (call.message.chat.id,))
    details = cursor.fetchone()

    # Create markup
    markup = quick_markup({'Back': {'callback_data': '(back_index)'},'Change Store Contact Number': {'callback_data': '(contact)'}, 'Change Store Name': {'callback_data': '(change_name)'}}, row_width=1)

    bot.send_message(call.message.chat.id, f'<b>Current Store Details</b>\n\n<b>Store Name</b>: {details[0]}\n<b>Contact Number</b>: {details[1]}', reply_markup=markup, parse_mode='HTML')
    

# Handles changing of store contact number
@bot.callback_query_handler(func= lambda call: call.data == '(contact)')
def change_contact(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Query for new contact number
    msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this message the new contact number for this store.', parse_mode='HTML')
    bot.register_next_step_handler(msg, update_contact)

def update_contact(message):
    cursor = db.cursor()

    # Get current contact number
    cursor.execute('SELECT contact FROM stores WHERE id = ?', (message.chat.id,))
    contact = cursor.fetchone()[0]


    # Validate contact
    if not message.text:
        bot.reply_to(message, 'Invalid contact number.')
        send_index(bot, message.chat)
    try:
        new_contact = int(message.text)
        if new_contact <= 0:
            bot.reply_to(message, 'Invalid contact number, number must be a positive integer.')
            send_index(bot, message.chat)
            return
    except:
        bot.reply_to(message, 'Invalid contact number, number must be an integer.')
        send_index(bot, message.chat)
        return
    if new_contact == contact:
        bot.reply_to(message, 'New contact number must be different from current contact number.')
        send_index(bot, message.chat)
        return
    
    # Update contact
    cursor.execute('UPDATE stores SET contact = ? WHERE id = ?', (new_contact, message.chat.id))
    db.commit()
    bot.send_message(message.chat.id, f"Store contact number has been changed from '{contact}' to '{new_contact}'.")
    send_index(bot, message.chat)


# Handles changing of store name
@bot.callback_query_handler(func=lambda call: call.data == '(change_name)')
def query_newname(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    
    # Query for new store name
    msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this message the new store name.', parse_mode='HTML')
    bot.register_next_step_handler(msg, update_storename)

def update_storename(message):
    cursor = db.cursor()

    # Get current store name
    cursor.execute('SELECT StoreName FROM stores WHERE id = ?', (message.chat.id,))
    name = cursor.fetchone()[0]

    # Validate store name
    if not message.text:
        bot.reply_to(message, 'Invalid store name.')
        send_index(bot, message.chat)
        return
    new_name = message.text
    if new_name == name:
        bot.reply_to(message, 'Invalid name, new name must be different from current name.')
        send_index(bot, message.chat)
        return
    
    # Update store name
    cursor.execute('UPDATE stores SET StoreName = ? WHERE id = ?', (new_name, message.chat.id))
    db.commit()
    bot.send_message(message.chat.id, f"Store name has been changed from '{name}' to '{new_name}'.")
    send_index(bot, message.chat)








# Handles contact store option from private chats
@bot.callback_query_handler(func=lambda call: call.data == 'Contact Store')
def contact_query_storename(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Query for store name
    msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this messsage the name of the store you would like to contact.', parse_mode='HTML')
    bot.register_next_step_handler(msg, contact_store)

def contact_store(message):

    # Validate store name
    name = message.text
    if not name:
        bot.reply_to(message, 'Invalid store name.')
        private_index(bot, message.chat)
        return
    
    # Check Database for Store
    cursor = db.cursor()
    cursor.execute('SELECT id FROM stores WHERE StoreName = ?', (name,))
    try:
        store_id = cursor.fetchone()[0]
    except:
        bot.reply_to(message, f"Sorry the store '{name}' does not exist. Try another name.")
        private_index(bot, message.chat)
        return

    # Get contact number
    cursor.execute('SELECT contact FROM stores WHERE id = ?', (store_id,))
    contact = cursor.fetchone()[0]

    bot.send_message(message.chat.id, f"<b>Contact Number for '{name}'</b>: {contact}", parse_mode='HTML')
    private_index(bot, message.chat)















# Handles item requests from private chats
@bot.callback_query_handler(func=lambda call: call.data == '(Request)')
def request_query_storename(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Ensure user has username
    if not call.from_user.username:
        bot.send_message(call.message.chat.id, 'Please add a telegram username to your telegram account use the bot as intended.')
        private_index(bot, call.message.chat)
        return
    
    # Check for active request
    cursor.execute('SELECT id FROM request WHERE user = ?', (call.from_user.username,))
    try:
        request_id = cursor.fetchone()[0]
        bot.send_message(call.message.chat.id, '<b>Uncompleted Request Found</b>\nComplete or cancel request before starting a new one.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
    except:
        # Query for store name
        msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this messsage the name of the store you would like to request from.', parse_mode='HTML')
        bot.register_next_step_handler(msg, request_query_items)

def request_query_items(message):

    # Ensure user has username
    if not message.from_user.username:
        bot.send_message(message.chat.id, 'Please add a telegram username to your telegram account use the bot as intended.')
        send_index(bot, message.chat)
        return

    # Validate store name
    name = message.text
    if not name:
        bot.reply_to(message, 'Invalid store name.')
        private_index(bot, message.chat)
        return
    
    # Check Database for Store
    cursor = db.cursor()
    cursor.execute('SELECT id FROM stores WHERE StoreName = ?', (name,))
    try:
        store_id = cursor.fetchone()[0]
    except:
        bot.reply_to(message, f"Sorry the store '{name}' does not exist. Try another name.")
        private_index(bot, message.chat)
        return
    
    # Ensure store has at least one item
    cursor.execute('SELECT id FROM stocks WHERE store_id = ?', (store_id,))
    items = cursor.fetchall()
    if not items:
        bot.reply_to(message, 'This store currently does not have any items in store. Unable to request from this store.')
        private_index(bot, message.chat)
        return
    
    # Start new request
    cursor.execute('INSERT INTO request (user, store_id) VALUES (?, ?)', (message.from_user.username, store_id))
    db.commit()
    request_id = cursor.lastrowid

    # Send markup
    bot.send_message(message.chat.id, '<b>New Request Started</b>' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')


# Handles adding of items into request
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(select_items_req)')
def select_items_req(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get request id and store id
    request_id = int(call.data.split()[1])
    cursor.execute('SELECT store_id FROM request WHERE id = ?', (request_id,))
    store_id = cursor.fetchone()[0]

    # Get current items in request
    cursor.execute('SELECT stock_id FROM request_items WHERE request_id = ?', (request_id,))
    rows = cursor.fetchall()
    request_stock_ids = [i[0] for i in rows]

    # Get items in store
    cursor.execute('SELECT id, ItemName, Quantity FROM stocks WHERE store_id = ? AND is_deleted = FALSE ORDER BY ItemName ASC', (store_id,))
    rows = cursor.fetchall()
    store_items = {}
    for item in rows:
        store_items[item[0]] = [item[1], item[2]]

    # Create markup excluding items already in request
    markup = {'Back': {'callback_data': f'(back_req) {request_id}'}}
    for item in store_items:
        if item not in request_stock_ids:
            markup[f'{store_items[item][0]} (Quantity: {store_items[item][1]})'] = {'callback_data': f'(add_item_req) {item} {request_id}'}

    # Query for item to add to request
    bot.send_message(call.message.chat.id, 'Select an item to add to request.', reply_markup=quick_markup(markup, row_width=1))


@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(add_item_req)')
def get_itemqty_req(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get request id and stock id
    stock_id = int(call.data.split()[1])
    request_id = int(call.data.split()[2])

    # Get item name and quantity
    cursor.execute('SELECT ItemName, Quantity FROM stocks WHERE id = ?', (stock_id,))
    item = cursor.fetchone()

    # Query for quantity
    msg = bot.send_message(call.message.chat.id, f"<b>Reply</b> to this message quantity of {item[0]} you would like to request.\n<b>Max Quantity</b>: {item[1]}", parse_mode='HTML')
    bot.register_next_step_handler(msg, add_item_request, request_id, stock_id, item[0], item[1])

def add_item_request(message, request_id, stock_id, itemname, max_quantity):
    cursor = db.cursor()

    # Validate Quantity
    try:
        quantity = int(message.text)
        if quantity <= 0:
            bot.reply_to(message, 'Invalid quantity, quantity must be a positive number.')
            bot.send_message(message.chat.id, 'Select an option to continue.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
            return
        if quantity > max_quantity:
            bot.reply_to(message, f"Invalid quantity, this store only has x{max_quantity} '{itemname}'.")
            bot.send_message(message.chat.id, 'Select an option to continue.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
            return
    except:
        bot.reply_to(message, 'Invalid quantity.')
        bot.send_message(message.chat.id, 'Select an option to continue.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
        return

    # Update Database
    cursor.execute('INSERT INTO request_items (request_id, stock_id, quantity) VALUES (?, ?, ?)', (request_id, stock_id, quantity))
    db.commit()
    bot.send_message(message.chat.id, f"x{quantity} {itemname} has been added to request" + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')





# Handles removing items from request
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(select_remove_req)')
def get_itemremove_req(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get request id
    request_id = int(call.data.split()[1])

    # Get items in request
    cursor.execute('SELECT  stock_id, request_items.quantity, ItemName FROM request_items JOIN stocks ON request_items.stock_id = stocks.id WHERE request_id = ? ORDER BY ItemName ASC', (request_id,))
    items = cursor.fetchall()
    if not items:
        bot.send_message(call.message.chat.id, 'No items in request to remove.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
        return
    
    # Create markup
    markup = {'Back': {'callback_data': '(back_req)'}}
    for item in items:
        markup[f'{item[2]} ({item[1]})'] = {'callback_data': f'(remove_req) {item[0]} {request_id}'}
    
    # Query for item to be removed
    bot.send_message(call.message.chat.id, 'Select an item to remove from request.' + request_info(request_id, db), reply_markup=quick_markup(markup, row_width=1), parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(remove_req)')
def remove_item_req(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get request id and stock id
    stock_id = int(call.data.split()[1])
    request_id = int(call.data.split()[2])

    # Get item name and quantity
    cursor.execute('SELECT ItemName, request_items.quantity FROM request_items JOIN stocks ON request_items.stock_id = stocks.id WHERE request_id = ? AND stock_id = ?', (request_id, stock_id))
    item = cursor.fetchone()

    # Update database
    cursor.execute('DELETE FROM request_items WHERE request_id = ? AND stock_id = ?', (request_id, stock_id))
    db.commit()

    bot.send_message(call.message.chat.id, f"x{item[1]} {item[0]} has been removed from request." + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')






# Handles request confirmation
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(confirm_req)')
def confirm_show_request_info(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get request id
    request_id = int(call.data.split()[1])

    # Ensure at least one item in request
    cursor.execute('SELECT * FROM request_items WHERE request_id = ?', (request_id,))
    if len(cursor.fetchall()) <= 0:
        bot.send_message(call.message.chat.id, 'Cannot submit empty request' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
        return

    # Create markup
    markup = quick_markup({'Confirm': {'callback_data': f'(confirmed_req) {request_id}'}, 'Back': {'callback_data': f'(back_req) {request_id}'}}, row_width=1)

    # Show request information
    bot.send_message(call.message.chat.id, 'Confirm request?' + request_info(request_id, db), reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(confirmed_req)')
def confirm_request(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get request id
    request_id = int(call.data.split()[1])

    # Get items in request
    cursor.execute('SELECT ItemName, request_items.quantity FROM request_items JOIN stocks ON request_items.stock_id = stocks.id WHERE request_id = ?', (request_id,))
    items = cursor.fetchall()

    # Get store name and contact
    cursor.execute('SELECT user, contact, store_id, remarks FROM request JOIN stores ON request.store_id = stores.id WHERE request.id = ?', (request_id,))
    store = cursor.fetchone()

    # Create store chat reply
    store_reply = f'<b>New Request</b>\nFrom: @{store[0]}\n\n<u>Items</u>\n'
    for item in items:
        store_reply += f'x{item[1]} <b>{item[0]}</b>\n'
    store_reply += '\n<u>Remarks</u>\n'
    if store[3]:
        store_reply += store[3]
    else:
        store_reply += 'No remarks.'
    
    # Create private chat reply
    private_reply = f'<b>Request Made</b>\nContact {store[1]} for more information.' + request_info(request_id, db)

    # Update store chat
    bot.send_message(store[2], store_reply, parse_mode='HTML')

    # Update private chat
    bot.send_message(call.message.chat.id, private_reply, parse_mode='HTML')

    # Remove request from database
    cursor.execute('DELETE FROM request WHERE id = ?', (request_id,))
    db.commit()
    cursor.execute('DELETE FROM request_items WHERE request_id = ?', (request_id,))
    db.commit()

    private_index(bot, call.message.chat)




# Handles cancellation of request
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(cancel_req)')
def cancel_show_request_info(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get request id
    request_id = int(call.data.split()[1])

    # Create markup
    markup = quick_markup({'Cancel': {'callback_data': f'(cancelled_req) {request_id}'}, 'Back': {'callback_data': f'(back_req) {request_id}'}}, row_width=1)

    # Show request information
    bot.send_message(call.message.chat.id, 'Cancel this request?' + request_info(request_id, db), reply_markup=markup, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(cancelled_req)')
def cancel_request(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get request id
    request_id = int(call.data.split()[1])

    # Create reply
    reply = 'The following request has been cancelled.' + request_info(request_id, db)

    # Remove request from database
    cursor.execute('DELETE FROM request WHERE id = ?', (request_id,))
    db.commit()
    cursor.execute('DELETE FROM request_items WHERE request_id = ?', (request_id,))
    db.commit()

    # Send reply
    bot.send_message(call.message.chat.id, reply, parse_mode='HTML')
    private_index(bot, call.message.chat)
    


# Shows options to add or remove remarks to request in private chats
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(add_remove_req)')
def query_addremove_req(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get request id
    request_id = int(call.data.split()[1])

    # Create markup
    markup = quick_markup({'Back': {'callback_data': f'(back_req) {request_id}'},'Change Remarks': {'callback_data': f'(add_remarks_req) {request_id}'}, 'Remove Remarks': {'callback_data': f'(remove_remarks_req) {request_id}'}}, row_width=1)

    # Show options
    bot.send_message(call.message.chat.id, 'Would you like to add or remove remarks to request?', reply_markup=markup)






# Handles adding remarks to request in private chats
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(add_remarks_req)')
def req_query_for_remarks(call):
    bot.delete_message(call.message.chat.id, call.message.id)

    # Get request id
    request_id = int(call.data.split()[1])

    # Query for remarks
    msg = bot.send_message(call.message.chat.id, '<b>Reply</b> to this message remarks for remarks', parse_mode='HTML')
    bot.register_next_step_handler(msg, req_add_remarks, request_id)

def req_add_remarks(message, request_id):
    cursor = db.cursor()

    # Validate remarks
    remarks = message.text
    if not remarks:
        bot.reply_to(message, 'Invalid remarks.')
        bot.send_message(message.chat.id, 'Select an option.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
        return
    
    # Update datebase
    cursor.execute('UPDATE request SET remarks = ? WHERE id = ?', (remarks, request_id))
    db.commit()
    bot.send_message(message.chat.id, 'Remarks added to request.')
    bot.send_message(message.chat.id, 'Select an option.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
    return


# Handles removal of remarks from request in private chats
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(remove_remarks_req)')
def remove_remarks_req(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    cursor = db.cursor()

    # Get request id
    request_id = int(call.data.split()[1])

    # Check for remarks
    cursor.execute('SELECT remarks FROM request WHERE id = ?', (request_id,))
    if not cursor.fetchone()[0]:
        bot.send_message(call.message.chat.id, 'No remarks to remove.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')
        return
    
    # Remove remarks
    cursor.execute('UPDATE request SET remarks = NULL WHERE id = ?', (request_id,))
    db.commit()
    bot.send_message(call.message.chat.id, 'Remarks removed.' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')






# Handles back button for index
@bot.callback_query_handler(func=lambda call: call.data == '(back_index)')
def back_index(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    send_index(bot, call.message.chat)

# Handles back button for index for private chats
@bot.callback_query_handler(func=lambda call: call.data == '(back_private)')
def back_private(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    private_index(bot, call.message.chat)

# Handles back button for request
@bot.callback_query_handler(func=lambda call: call.data.split()[0] == '(back_req)')
def back_req(call):
    bot.delete_message(call.message.chat.id, call.message.id)
    request_id = int(call.data.split()[1])
    bot.send_message(call.message.chat.id, 'Choose an option to continue' + request_info(request_id, db), reply_markup=request_markup(request_id), parse_mode='HTML')

# Closes bot
@bot.callback_query_handler(func=lambda call: call.data == 'Exit')
def exit(call):
    bot.delete_message(call.message.chat.id, call.message.id)






# Handle /create_store command
@bot.message_handler(commands=['create_store'])
def query_storename(message):
    cursor = db.cursor()

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
    if not (bot, message.chat, message.from_user):
        return
    
    # Prompt user for store name
    msg = bot.reply_to(message, '<b>Reply</b> to this message name of your store.\n(Your store name is used for other users to find your store)', reply_markup=types.ForceReply(True, 'Name of Store'), parse_mode='HTML')
    bot.register_next_step_handler(msg, query_storecontact)

def query_storecontact(message):
    cursor = db.cursor()

    # Ensure store name is a string
    if not message.text:
        bot.reply_to(message, 'Invalid store name, enter /create_store to try again.')
        
    # Check if store name already exist
    cursor.execute('SELECT * FROM stores WHERE StoreName = ?', (message.text,))
    rows = cursor.fetchall()
    if len(rows) != 0:
        bot.send_message(message.chat.id, 'Store name has already been taken. Enter /create_store to try again')
        return

    # Query for contact number
    name = message.text
    msg = bot.reply_to(message, '<b>Reply</b> to this message the contact number for this store.', reply_markup=types.ForceReply(True, 'Contact Number'), parse_mode='HTML')
    bot.register_next_step_handler(msg, create_store, name)

def create_store(message, name):
    cursor = db.cursor()

    # Validate contact
    if not message.text:
        bot.reply_to(message, 'Invalid contact number, enter /create_store to try again.')
        return
    try:
        contact = int(message.text)
        if contact <= 0:
            bot.reply_to(message, 'Invalid contact number, number must be a positive integer, enter /create_store to try again.')
            return
    except:
        bot.reply_to(message, 'Invalid contact number, number must be an integer, enter /create_store to try again.')
        return
    
    # Initialise store
    cursor.execute('INSERT INTO stores (id, StoreName, contact) VALUES (?, ?, ?)', (message.chat.id, name, contact))
    db.commit()
    bot.send_message(message.chat.id, f'<b>Store successfully created</b>\n\n<b>Store Name</b>: {name}\n<b>Contact Number</b>: {contact}', parse_mode='HTML')
    send_index(bot, message.chat)

# Enable saving next step handlers
bot.enable_save_next_step_handlers(delay=2)

# Load next step handlers
bot.load_next_step_handlers

# Constantly check for new messages
bot.infinity_polling()
