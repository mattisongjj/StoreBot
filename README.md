# STOREBOT PROJECT

This project is a telegram bot that is able to keep track of item stocks and transactions as well as connect users to stores for making item request. This bot can be used in any situation where stock taking and transaction tracking is relevant such as at warehouses, retail stores or even keeping track of items in your own storage room at home.

The bot is split into two main parts, one for when used in a group chat and another for when used in a private chat. When used in a group chat, the bot is able to stock take and track transactions while when used is a private chat, the bot is able to send request for items to stores and get you in touch with store operators.

Technologies used:
- Python
- SQLite

Libaries used:
- pyTelegramBotAPI
- sqlite3
- Various libaries for storing and manipulating date data.

## Video Demo: 

## Bot Features

To start the bot and access its features, either use the /start command or /help command.

#### Group Chat Features

- Store creation

    - To start tracking items, item transactions and getting item request, you must first create a store.
    - To create store:
        1. Add bot into a group chat
        2. Run /create_store command (Ensure that you are an administrator for the group chat)
        3. Follow the instructions given by the bot
    - Once store has been created, you can start tracking items and transactions for your store, as well as getting item request from other telegram users by sharing your store name.

- Managing Items
    - 

- Checking stock
    -

- Adding new transactions and transaction types
    -

- Viewing transaction history
    -

#### Private Chat Features

- Send item request to stores
- Get store contact information

## Files:

- bot.py
- function.py
- stores.db

## How to run the bot

1. Clone this repository
2. Ensure you have the following libraries installed:


