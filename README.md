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

## Video Demo: 

## Bot Features

To start the bot and access its features, use the /start command. (Ensure that you have a telegram user name before using the bot.)

Once the /start command is run, the bot will reply with an 'inline keyboard', which are options to click on, which will allow you to access the bot.

#### **Group Chat Features**

- **Store Creation**

    - To start tracking items, item transactions and getting item request, you must first create a store.

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

    - Note that one store can have only one ongoing transaction at all times, and thus a new transaction can only be started when all transactions have been confirmed or cancelled.
        

- **Viewing Transaction History**

    - The 'View Transaction History' option allows you to view all transactions (For all items or one specific item) in a day, or month.

    - When this option is selected the bot will prompt you for a day or month.

    - Once you have inputed a day or month, you will then be able to choose to view all items or one specific item for transaction history viewing during that day/month.

    - Once you have selected an item, the bot will then show you all transactions involving that item during the day/month, by sending one text message containing transaction information per transaction. (This process could take a long time depending on how many transactions there are.)

#### **Private Chat Features**

- Send item request to stores
- Get store contact information

## **Files**

- bot.py
- function.py
- stores.db

## **How To Run The Bot**

1. Ensure you have the latest version of python installed
2. Ensure you have the following libraries installed:


