import datetime, time
from telegram import InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from deposit_module.balance_dbhandler import balanceManager
from deposit_module.order_databasehandler import orderManager
from deposit_module.create_order import create_order
import json
from deposit_module.delete_order import delete_sellix_order
from deposit_module.job_dbhandler import JobManager
from main import confirmation_update_job
from ongoing_gamesdbhandler import OngoingGame
from withdrawalstate_dbhandler import WithdrawalState
import qrcode,io,requests
balancedb = balanceManager('database.sqlite3')
orderdb = orderManager('database.sqlite3')
jobsdb = JobManager('database.sqlite3')
ongoing = OngoingGame('database.sqlite3')
iswithdrawing = WithdrawalState('database.sqlite3')
with open('config.json', 'r') as file:
        data = json.load(file)
SELLIX_API = data['SELLIX_API']
def generate_crypto_payment_qr(address, amount=None, label=None,box_size=5):
    # Construct the payment URI
    uri = f'bitcoin:{address}'
    if amount:
        uri += f'?amount={amount}'
    if label:
        uri += f'&label={label}'

    # Generate the QR code
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=box_size, border=4)
    qr.add_data(uri)
    qr.make(fit=True)

    qr_stream = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(qr_stream, format='PNG')
    qr_stream.seek(0)  # Move the cursor to the beginning of the stream
    return qr_stream.getvalue()

def choose_crypto(update: Update, context: CallbackContext):
    userid = update.effective_user.id
    query = update.callback_query
    query.answer()

    if ongoing.check_user_exists(userid):
        keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = f"<b>⚠ You have game unfinished, Finish it first before creating an invoice.</b>"
        query.edit_message_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    elif iswithdrawing.user_exists(userid):
         keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
         reply_markup = InlineKeyboardMarkup(keyboard)
         msg = f"<b>Please Cancel the ongoing withdrawal before depositing!</b>"
         query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    else:
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
    amount_msg = f"<b>💰Select the amount to deposit</b>"
    keyboard = [
                [
                    InlineKeyboardButton("$5", callback_data='btc_deposit_5'),
                    InlineKeyboardButton("$10", callback_data='btc_deposit_10'),
                    InlineKeyboardButton("$20", callback_data='btc_deposit_20')

                ],
                [
                    InlineKeyboardButton("$30", callback_data='btc_deposit_30'),
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
    amount_msg = f"<b>💰Select the amount to deposit</b>"
    keyboard = [
                [
                    InlineKeyboardButton("$5", callback_data='ltc_deposit_5'),
                    InlineKeyboardButton("$10", callback_data='ltc_deposit_10'),
                    InlineKeyboardButton("$20", callback_data='ltc_deposit_20')

                ],
                [
                    InlineKeyboardButton("$30", callback_data='ltc_deposit_30'),
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
    amount_msg = f"<b>💰Select the amount to deposit</b>"
    keyboard = [
                [
                    InlineKeyboardButton("$5", callback_data='eth_deposit_5'),
                    InlineKeyboardButton("$10", callback_data='eth_deposit_10'),
                    InlineKeyboardButton("$20", callback_data='eth_deposit_20')

                ],
                [
                    InlineKeyboardButton("$30", callback_data='eth_deposit_30'),
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
    msg=f"<b>To complete your purchase with {coin}\n\nPlease send Exactly <code>{amount}</code> {currency.upper()}\n\nTo Address: <code>{address}</code>\n\nYour Order ID is: <code>{uniqid}</code>\n\nWe are checking for payment status, please wait for 2 Confirmations.\n\n</b>"
    keyboard = [[InlineKeyboardButton("❌Cancel Invoice", callback_data=f"cncl_{uniqid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    img_data = generate_crypto_payment_qr(address,amount,label="coin")
    context.bot.send_photo(chat_id=user_id,photo=img_data)
    message_id = query.message.message_id
    orderdb.insert_order(user_id=user_id, username=username, uniqid=uniqid, status='PENDING', crypto=coin, usdvalue=usdvalue, hash='None', amount=amount, address=address)
    context.job_queue.run_repeating(confirmation_update_job, interval=10, first=0, context={'user_id': user_id, 'uniqid': uniqid, 'username': username, 'usdvalue':usdvalue,'message_id':message_id})
    jobsdb.add_job(user_id,uniqid,username,usdvalue,message_id)
    webhook_content = {
    "content": None,  # You can set this to a message if you want to send a text message along with the embed
    "embeds": [{
        "title": "New Order Created📥",
        "description": "A new deposit has been initiated. 🚀",
        "fields": [
            {"name": "Order ID 🆔", "value": uniqid},
            {"name": "User ID 🔢", "value": str(user_id)},
            {"name": "Username 🧑‍💼", "value": username},
            {"name": "Address 🏦", "value": address},
            {"name": "Amount 💰", "value": f"{amount} {coin}"},
            {"name": "USD Value 💵", "value": f"${usdvalue}"},
            {"name": "Currency 💱", "value": currency.upper()}
        ],
        "color": 5814783  # You can change this to any color you prefer
    }]
}
    webhook_url = "https://discord.com/api/webhooks/1221894219350806568/bUU2QDC5Au67sZb4AwCZZzrG5_VmklszZ-y0JfAuj6BRPmHg_aw1Bmcb8KPu6-Td5X1g"
    response = requests.post(webhook_url, json=webhook_content)

def handle_cancel_confirmation(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    uniqid = query.data.split('_')[-1]  # Extracting uniqid from the callback data
    # Confirmation message
    msg = f"<b>Are you sure you want to cancel the order: <code>{uniqid}</code></b>"
    # Yes and No buttons
    keyboard = [
        [InlineKeyboardButton("✅Yes", callback_data=f"confirm_cancel_{uniqid}"),
        InlineKeyboardButton("❌No", callback_data=f"decline_cancel_{uniqid}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def handle_decline_cancel(update: Update, context: CallbackContext):
    query = update.callback_query
    uniqid = query.data.split('_')[-1]
    order = orderdb.get_order_by_uniqid(uniqid)
    query.answer()
    coin = order[0]
    amount = order[1]
    address = order[2]
    msg = f"<b>To complete your purchase with {coin}\n\nPlease send Exactly <code>{amount}</code> {coin}\n\nTo Address: <code>{address}</code>\n\nYour Order ID is: <code>{uniqid}</code>\n\nWe are checking for payment status, please wait for 2 Confirmations.\n\n</b>"
    keyboard = [[InlineKeyboardButton("❌Cancel Invoice", callback_data=f"cncl_{uniqid}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.HTML)



def handle_confirm_cancel(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    uniqid = query.data.split('_')[-1]

    keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    status, err = delete_sellix_order(SELLIX_API, uniqid)
    if status:
        query.edit_message_text(f"<b>Order <code>{uniqid}</code> has been cancelled ✅</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        jobsdb.remove_job(uniqid)
    else:
        query.edit_message_text(f"<b>Order Cancellation failed, Error: {err}</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
