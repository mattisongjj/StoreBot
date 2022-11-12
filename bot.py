import telebot
from telebot.util import quick_markup
from telebot import types
import sqlite3
from sqlite3 import Error

# Set API key
API_KEY = '5691173475:AAGF7nfwSMKzd4UyPpveJ2OYuu6PGSTJzLs'
bot = telebot.TeleBot(API_KEY, parse_mode=None)

# Connect to database
try:
    db = sqlite3.connect('stores.db', check_same_thread=False)
except Error as e:
    print(f"Error '{e}' occured when establishing connection to database")
cursor = db.cursor()


# Handle /start and /help commands
@bot.message_handler(commands=['start', 'help'])
def index(message):
# Start bot

    # Bot was started in a group chat
    if message.chat.type == 'group':

        # Check for existing store
        cursor.execute("SELECT * FROM stores WHERE id = ?", (message.chat.id,))
        rows = cursor.fetchall()
        # Store does not exist
        if len(rows) != 1:
            bot.send_message(message.chat.id, 'This group currently does not have a store. Enter /create_store to initialize store.')
        # Store exist
        else:
            msg = bot.send_message(message.chat.id, 'Choose an option', reply_markup= quick_markup({
                'View Current Stock': {'callback_data': 'View Current Stock'},
                'Increase Stock': {'callback_data': 'Increase Stock'},
                'Decrease Stock': {'callback_data': 'Decrease Stock'},
                'Add New Item': {'callback_data': 'Add New Item'},
                'Add Transaction': {'callback_data': 'Add Transaction'},
                'View Transaction History': {'callback_data': 'View Transaction History'}
            }, row_width=1))


    # Bot was started in a private chat
    elif message.chat.type == 'private':

        # Ask for store name
        bot.send_message(message.chat.id, 'Enter a store name')
        # Show options









# Handles adding of stock
@bot.callback_query_handler(func=lambda call: call.data == 'Add New Item')
def options(call):
    msg = bot.send_message(call.message.chat.id, 'Name of new item?\n(Reply to this message)')
    bot.register_next_step_handler(msg, get_total)

item = ''
def get_total(message):
    # Ensure message is text
    if not message.text:
        bot.reply_to(message, 'Invalid item name.')
    # Check database if item already exist
    cursor.execute('SELECT * FROM stocks WHERE store_id = ? AND ItemName = ?', (message.chat.id, message.text))
    if len(cursor.fetchall()) != 0:
        bot.reply_to(message, 'Item already exist in store.')
    # Remember item name
    global item 
    item = message.text
    # Get quantity
    msg = bot.reply_to(message,'Quantity of item?', reply_markup=types.ForceReply(True, 'Quantity of item'))
    bot.register_next_step_handler(msg, add_item)

def add_item(message):
    # Validate quantity
    try:
        int(message.text)
    except:
        bot.send_message(message.chat.id, 'Invalid Quantity')

    # Add item to database
    global item
    cursor.execute('INSERT INTO stocks (store_id, ItemName, Quantity) VALUES (?, ?, ?)', (message.chat.id, item, int(message.text)))
    db.commit()
    bot.send_message(message.chat.id, f'x{message.text} {item} has been created and added to stock.')















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
    user = bot.get_chat_member(message.chat.id, message.from_user.id)
    if user.status in ['creator', 'administrator']:

        # Prompt user for store name
        msg = bot.reply_to(message,'What would you like to name your store?', reply_markup=types.ForceReply(True, 'Store Name'))
        bot.register_next_step_handler(msg, created_store)
    else:
        bot.reply_to(message, 'You must be owner or administrator of this group to run this command')

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