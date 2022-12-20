# CS50 STOREBOT PROJECT

This project is a telegram bot that is able to keep track of item stocks and transactions as well as connect users to stores for making item request. This bot can be used in any situation where stock taking and transaction tracking is relevant such as at warehouses, retail stores or even keeping track of items in your own storage room at home.

The bot is split into two main parts, one for when used in a group chat and another for when used in a private chat. When used in a group chat, the bot is able to stock take and track transactions while when used is a private chat, the bot is able to send request for items to stores and get you in touch with store operators.

Technologies used:
- Python
- SQLite

Libaries used:
- pyTelegramBotAPI
- sqlite3
- Various libaries for storing and manipulating date data.


## Video Demo: https://youtu.be/JYc51R3CC2A


## Bot Features

To start the bot and access its features, use the /start command. (Ensure that you have a telegram user name before using the bot.)

Once the /start command is run, the bot will reply with an 'inline keyboard', which are options to click on, which will allow you to access the bot.


#### **Group Chat Features**

The following features are available when the bot is started in a group chat.

- **Store Creation**

    - To access the other features and start tracking items, item transactions and getting item request, you must first create a store.

    - To create store:

        1. Add bot into a group chat
        2. Run /create_store command (Ensure that you are an administrator for the group chat)
        3. Follow the instructions given by the bot

    - Once store has been created, you can start tracking items and transactions for your store, as well as getting item request from other telegram users by sharing your store name.

- **Managing Items**

    - The 'Manage Items' option allows you to do three things:

        1. Add items and their minimum quantities, to your store.

            - To add items to your store press the add item option and follow instructions given by the bot.
            - The bot also gives you an option to add the minimum requirement of the item you are adding in your store.
            - Should you add a minimum requirement to an item, you will be notified whenever its quantity falls below its minimum requirement.

        2. Rename items currently in your store

            - To rename an item in your store press the rename item option, select an item to rename and follow the instructions given by the bot.
            - Note that renaming an item in your store changes the name of that item in all past transactions as well.

        3. Remove items from your store.

            - To remove an item from your store press the remove item option and select an item to remove.
            - Note that once an item has been removed from your store its stock will no longer be tracked and will be deleted from your current stock, but any past transactions involving that item will not be deleted.

- **Viewing/Checking Stock**

    - The 'View Current Stock' option allows you to view the quantities of items in your stock and check if any items are below their minimum requirement.

    - To view the full stock of items in your store, select the 'View Full Stock' option.

    - To view the stock of a specific item in your store, select the name of the item which you want to view.

    - To check if any items in your store is below minimum requirement, select the 'Check Minimum Requirement' option. This option shows you which items (if any) in your store are currently below minimum requirement and the respective quantities to 'top-up'.


- **Adding Transactions**

    - The 'New Transaction' option allows you to add new item transactions to your store.

    - To start a new transaction, select one of the transaction types shown. By default your store will only have two transaction types, 'Issue' and 'Loan', to add new transaction types, select the 'Add New Transaction Type' option.

    - You are able to add, rename and remove, as many transaction types from your store.

    - Once you have selected a transaction type, a new transaction is started and the bot will reply with the following options for you to edit your transaction:

        1. The 'Select Items' option prompts you for an item to add to your transaction. When selected, the option will first prompt you for an item, followed by if the item's quantity is increased or decreased for the transaction, and lastly the quantity of item involved in the transaction. After which the item will be added to your transaction.

        2. The 'Remove Items' option will prompt you for an item to remove from your transaction.

        3. The 'Add/Change Customer' option adds or changes the name of the customer for your transaction, if applicable.

        4. The 'Remove Customer' option removes the current customer for your transaction.

        5. The 'Confirm Transaction' option will confirm the transaction, after which the transaction is recorded and item quantities in your stock ajusted accordingly.

        6. The 'Cancel Transaction' option will cancel the transaction.

    - Note that one store can have only one ongoing transaction at all times, and thus a new transaction can only be started when the current transaction has been confirmed or cancelled.
        

- **Viewing Transaction History**

    - The 'View Transaction History' option allows you to view all transactions (For all items or one specific item) in a day, or month.

    - When this option is selected the bot will prompt you for a day or month.

    - Once you have inputed a day or month, you will then be able to choose to view all items or one specific item for transaction history viewing during that day/month.

    - Once you have selected an item, the bot will then show you all transactions involving that item during the day/month, by sending one text message containing transaction information per transaction. (This process could take a long time depending on how many transactions there are.)


#### **Private Chat Features**

The following features are available when the bot is started in a private chat with the bot.

- **Send item request to stores**

    - The 'Request Items' options allows you to send item request to stores.

    - When selected the bot will first prompt you for the name of the store you would like to request items from.

    - If you replied the bot with a valid store name, a new request is started and the bot will reply with the following options to edit your request:

        1. The 'Select Items' option will prompt you to select an item from the store which you would like to add to the request. Once you have selected an item it will prompt you for the quantity of that item you would like to request, after which the item and its requested quantity is added to the request.

        2. The 'Remove Items' option will prompt you for an item to remove from your request

        3. The 'Change/Remove Remarks' option will allow you to add, change or remove any additonal remarks for your request.

        4. The 'Confirm Request' option will confirm the request, after which the store will be notified of your request, and the bot will give you the contact number of the store, allowing you to get in touch with the store.

        5. The 'Cancel Request' option will cancel the current request

    - Note that any user may only have one current request at all times, thus to start a new request one must first confirm or cancel the current request.
         
- **Get store contact information**

    - The 'Contact Store' option will prompt you for the name of the store you would like to contact.

    - If you replied the bot with a valid store name, the bot will reply you with the contact number of the store.


## **Files**

- **bot.py**

    - Imports:

        - Imports `os` from the [python standard library](https://docs.python.org/3/library/)

        - Imports `load_dotenv` function the [python-dotenv library](https://pypi.org/project/python-dotenv/)
        
        - Imports `telebot` class from the [pyTelegramBotAPI library](https://pypi.org/project/pyTelegramBotAPI/)

        - Imports `sqlite3`, `datetime`, `calendar` and `time` from the [python standard library](https://docs.python.org/3/library/)

        - Imports `relativedelta` class from the [python-dateutil library](https://dateutil.readthedocs.io/en/latest/)

        - Imports `functions.py`

    - Functions/class instances:

        - Loads `API_KEY` from environmental variables using functions from `os` and `python-dotenv` library.

        - Creates instance of `telebot` class from `pyTelegramBotAPI` for establishing connection to the telegram API, using `API_KEY`.

        - Connects to local database (`stores.db`) using the Connection class from sqlite3 library.

        - `@bot.message_handler` and `@bot.callback_query_handler` is used throughout the file to execute the function below the decorator, when commands are sent to the bot or when the 'CallbackQuery' type is sent to the bot from an 'inline keyboard'.

        - `bot.register_next_step_handler(msg, func)` is used throughout the file to register a callback function, *func*, that is executed when a reply is sent to a message sent by the bot, *msg*.

        - Most functions interact with the database (`stores.db`) by first creating an instance of the `Cursor` class from `sqlite3` library, and using it to execute SQLite statements as well as fetch or edit data.

        - The `datetime` class from `datetime` library along with the `calendar` library and `relativedelta` class from `python-dateutil` library, is used throughout the file when manipulating data related to calendar dates for transactions.

        - Multiple functions imported from `functions.py` are used throughout the file, mainly to create text replies and 'inline keyboard' markups which the bot sends out to users.


- **stores.db**

    - This file is the database for this project, it uses multiple tables to store all stores, item stocks, transactions and request.

    - `stores` table stores the store id, store name and contact number of every store. Every store's id is equal to the chat id of the chat it was created in given by the Telegram API. The id column, which stores store id, is the primary key of this table.

    - `stocks` table stores the item id, store id, item name, quantity, minimum requirement and deletion status of every item in the database. The id column, which stores item id, is the primary key of this table.

    - `transaction_types` table stores the transaction type id, store id , name and deletion status of every transaction type in the database. The id column, which stores the transaction type id, is the primary key of this table. Notice that transaction type id from 1 to 4 have no store id, this is because these types are default types for all stores.

    - `transactions` table stores the transaction id, store id, user who created the transaction, customer, type id, datetime and confirmation status for all transactions in the database. The id column, which stores transaction id, is the primary key for this table.

    - `transaction_items` table stores the transaction id, item id, old item quantity and change in item quantity for every item involved in transactions in the database. This table does not have a primary key and is used to allow multiple items to be added to the same transaction.

    - `request` table stores the request id, request user, id of the store requested, and any remarks for request made to stores from private chats with the bot. The id column, which stores request id, is the primary key of this table. Entries to this table are deleted once the request has been made, as there is no need to keep them once the stores have been notified of the request.

    - `request_items` table stores the request id, item id and quantity requested for every item involved in ongoing request. This table does not have a primary key and is used to allow multiple items to be added to the same request.


#### **How To Run The Bot**

1. Ensure you have the latest version of `python` installed

2. Ensure you have the following python libraries installed using pip:

    1. [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/)
    2. [python-dateutil](https://dateutil.readthedocs.io/en/latest/)
    3. [python-dotenv](https://pypi.org/project/python-dotenv/)

3. Clone this repository using `git clone git@github.com:mattisongjj/project.git` at the command line

4. Generate an authentication token for a bot on telegram by following this [guide](https://core.telegram.org/bots/features#botfather)

5. Set `API_KEY` variable to the authentication token generated from step 4.

4. Run the bot by running the command `python bot.py`

5. Open [Telegram](https://telegram.org/) and search for the bot.

6. Start using the bot by starting it in a private chat or group chat!