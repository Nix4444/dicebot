from telegram import InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from deposit_module.balance_dbhandler import balanceManager
from deposit_module.order_databasehandler import orderManager
from deposit_module.create_order import create_order
import json
balancedb = balanceManager('../database.sqlite3')
orderdb = orderManager('../database.sqlite3')
with open('config.json', 'r') as file:
        data = json.load(file)
SELLIX_API = data['SELLIX_API']

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
    query.edit_message_text(amount_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

def handle_deposit(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = update.effective_user.id
    username = update.effective_user.username
    query.edit_message_text('<b>Generating invoice...</b>',parse_mode=ParseMode.HTML)
    currency = query.data.split('_')[0]
    amount = int(query.data.split('_')[-1])
    if currency == 'btc':
        coin = "BITCOIN"
    elif currency == 'ltc':
        coin = "LITECOIN"
    elif currency == 'eth':
        coin = "ETHEREUM"
    address, amount, uniqid, protocol, usdvalue = create_order(SELLIX_API,coin,amount) #response from api
    msg=f"To complete your purchase with {coin}\n\nPlease send Exactly <code>{amount}</code> {currency.upper()}\n\nTo Address: <code>{address}</code>\n\nYour Order ID is: <code>{uniqid}</code>\n\nWe are checking for payment status, please wait for 2 Confirmations.\n\n"
    keyboard = [[InlineKeyboardButton("❌Cancel Invoice", callback_data=f"cncl_{uniqid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    orderdb.insert_order(user_id=user_id, username=username, uniqid=uniqid, status='PENDING', crypto=coin, usdvalue=usdvalue, hash='None', amount=amount, address=address)

def cancelconfirm(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    uniqid = query.data.split('_')[-1]
    msg = f"<b>Are you sure you want to cancel order:</b> <code>{uniqid}</code>"
    keyboard = [[InlineKeyboardButton("✅Yes", callback_data=f"cncl_y_{uniqid}"),InlineKeyboardButton("❌No", callback_data=f"cncl_n_{uniqid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

def cancelconfirm_yes(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    uniqid = query.data.split('_')[-1]
    query.edit_message_text("cancelled",parse_mode=ParseMode.HTML)

def cancelconfirm_no(update:Update,context:CallbackContext):
    query = update.callback_query
    query.answer()
    uniqid = query.data.split('_')[-1]
    order = orderManager.get_order_by_uniqid(uniqid)
    coin = order[0]
    amount = order[1]
    address = order[2]
    if coin == "BITCOIN":
        currency = "btc"
    elif coin == 'LITECOIN':
        currency = "ltc"
    elif coin == 'ETHEREUM':
        currency = "eth"

    msg=f"To complete your purchase with {coin}\n\nPlease send Exactly <code>{amount}</code> {currency.upper()}\n\nTo Addres: <code>{address}</code>\n\nYour Order ID is: <code>{uniqid}</code>\n\nWe are checking for payment status, please wait for 2 Confirmations.\n\n"
    keyboard = [[InlineKeyboardButton("❌Cancel Invoice", callback_data=f"cncl_{uniqid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)