from telegram import InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from balance_dbhandler import balanceManager
from deposit_module.create_order import create_order
balancedb = balanceManager('../database.sqlite3')

def choose_crypto(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    coin_msg = "<b>🏦Select the crypto to pay with</b>"
    keyboard = [
        [
            InlineKeyboardButton("Bitcoin", callback_data='btc')
        ],
        [
            InlineKeyboardButton("Litecoin", callback_data='ltc')
        ],
        [
            InlineKeyboardButton("Ethereum", callback_data='eth')
        ],
        [
            InlineKeyboardButton("◀️Back", callback_data='mainmenu'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(coin_msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def handle_btc(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    amount_msg = f"💰Select the amount to deposit"
    keyboard = [
        [
            InlineKeyboardButton("$10", callback_data='btc_deposit_10'),
            InlineKeyboardButton("$20", callback_data='btc_deposit_20')

        ],
        [
            InlineKeyboardButton("$50", callback_data='btc_deposit_50'),
            InlineKeyboardButton("$100", callback_data='btc_deposit_100')
        ],
        [
            InlineKeyboardButton("◀️Back", callback_data='deposit'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print(query)
    query.edit_message_text(amount_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

def handle_ltc(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    amount_msg = f"💰Select the amount to deposit"
    keyboard = [
            [
                InlineKeyboardButton("$10", callback_data='ltc_deposit_10'),
                InlineKeyboardButton("$20", callback_data='ltc_deposit_20')

            ],
            [
                InlineKeyboardButton("$50", callback_data='ltc_deposit_50'),
                InlineKeyboardButton("$100", callback_data='ltc_deposit_100')
            ],
            [
                InlineKeyboardButton("◀️Back", callback_data='deposit'),
            ]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print(query)
    query.edit_message_text(amount_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
def handle_eth(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    amount_msg = f"💰Select the amount to deposit"
    keyboard = [
                [
                    InlineKeyboardButton("$10", callback_data='eth_deposit_10'),
                    InlineKeyboardButton("$20", callback_data='eth_deposit_20')

                ],
                [
                    InlineKeyboardButton("$50", callback_data='eth_deposit_50'),
                    InlineKeyboardButton("$100", callback_data='eth_deposit_100')
                ],
                [
                    InlineKeyboardButton("◀️Back", callback_data='deposit'),
                ]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print(query)
    query.edit_message_text(amount_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

def handle_deposit(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    amount = query.data.split("_")[1]  # Extracting the amount from callback data
    username = update.effective_user.username
    userid = update.effective_user.id
