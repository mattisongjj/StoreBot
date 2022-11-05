import telebot
import sqlite3
from sqlite3 import Error

# Set API key
API_KEY = '5691173475:AAGF7nfwSMKzd4UyPpveJ2OYuu6PGSTJzLs'
bot = telebot.TeleBot(API_KEY, parse_mode=None)

# Connect to database
try:
    db = sqlite3.connect('/home/mattisong/githubrepos/project/stores.sqlite', check_same_thread=False)
except Error as e:
    print(f"Error '{e}' occured when establishing connection to database")
cursor = db.cursor()


@bot.message_handler(commands=['start', 'help'])
def index(message):
# Start bot

    # Bot was started in a group chat
    if message.chat.type == 'group':

        # Check for existing store
        cursor.execute("SELECT * FROM stores WHERE id = ?", [message.chat.id])
        rows = cursor.fetchall()
        print(rows)
        # Store does not exist
        if len(rows) != 1:
            bot.send_message(message.chat.id, 'This group currently does not have a store. Enter /create_store to initialize store.')
        # Store exist
        else:
            #todo
            bot.send_message(message.chat.id, 'Store options')

    # Bot was started in a private chat
    elif message.chat.type == 'private':

        # Ask for store name
        bot.send_message(message.chat.id, 'Enter a store name')
        # Show options









def created_store(message):
    # Ensure store name is a string
    if not message.text:
        bot.send_message(message.chat.id, 'Invalid store name')
        
    # Check if store name already exist
    cursor.execute('SELECT * FROM stores WHERE name = ?', [message.text])
    rows = cursor.fetchall()
    if len(rows) != 0:
        bot.send_message(message.chat.id, 'Store name has already been taken. Please choose another name.')
        return
            
    # Initialise store
    cursor.execute('INSERT INTO stores (name) VALUES (?)', [message.text]) 

@bot.message_handler(commands=['create_store'])
def create_store(message):
# Initialises store in a group chat

    # Ensure that message was sent in a group chat
    if message.chat.type != 'group':
        bot.send_message(message.chat.id, 'Can only create store in a group chat')
        return
    
    # Ensure User is creator or adminstrator of chat
    user = bot.get_chat_member(message.chat.id, message.from_user.id)
    if user.status in ['creator', 'administrator']:

        # Prompt user for store name
        reply= bot.reply_to(message,'What would you like to name your store?')
        ###
        bot.register_next_step_handler(reply, created_store)
        ###
    else:
        bot.reply_to(message, 'You must be owner or administrator of this group to run this command')






# Constantly check for new messages
bot.infinity_polling()