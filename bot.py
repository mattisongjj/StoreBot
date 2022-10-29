import telebot

# Set API key
API_KEY = '5691173475:AAGF7nfwSMKzd4UyPpveJ2OYuu6PGSTJzLs'
bot = telebot.TeleBot(API_KEY, parse_mode=None)

# Start bot
@bot.message_handler(commands=['start', 'help'])
def index(message):

    # Bot was started in a group chat
    if message.chat.type == 'group':

        # Check for existing store
        bot.send_message(message.chat.id, "Create store")
        # Show options

    # Bot was started in a private chat
    elif message.chat.type == 'private':
        # Ask for store name
        bot.send_message(message.chat.id, "Enter a store name")
        # Show options

    



# Constantly check for new messages
bot.infinity_polling()