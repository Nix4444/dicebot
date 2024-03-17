import json
from telegram import InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from deposit_module.order_databasehandler import orderManager
from balance_dbhandler import balanceManager
from deposit_module.create_order import create_order
from deposit_module.conf_check import check_order_status
from deposit_module.delete_order import delete_sellix_order
from datetime import timedelta, datetime
from deposit_module.deposit_buttons import *
import logging
with open('config.json', 'r') as file:
        data = json.load(file)
TOKEN = data['TOKEN']
SELLIX_API_KEY = data['SELLIX_API']

orderdb = orderManager('database.sqlite3')
admin_userids = [5455454489]
UNIQID_INDEX = 0
USER_ID_INDEX = 1
USERNAME_INDEX = 2
STATUS_INDEX = 3
CRYPTO_INDEX = 4
AMOUNT_INDEX = 5
HASH_INDEX = 6
def start(update: Update, context: CallbackContext) -> None:
    username = update._effective_user.username
    userid = update.effective_user.id
    welcome_msg = f"<b>Welcome @{username} to [name placeholder] Bot!</b>"

    balancedb.add_entry(userid,username)
    keyboard = [
        [InlineKeyboardButton("💲Deposit", callback_data='deposit'),
        InlineKeyboardButton("💵Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("💸Balance", callback_data='balance')],
        [InlineKeyboardButton("🎲Play Dice", callback_data='dice')]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
def balance_button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    userid = update.effective_user.id
    user =  balancedb.get_balance(userid)
    balance_msg = f'''<b>📊Account Overview</b>\n\n👤Username: @{user[1]}\n\n🆔UserID: <code>{user[0]}</code>\n\n💸Balance: <code>${user[2]}</code>'''
    keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(balance_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

def edit_to_main(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    username = update.effective_user.username
    userid = update.effective_user.id
    welcome_msg = f"<b>Welcome @{username} to [name placeholder] Bot!</b>"

    balancedb.add_entry(userid,username)
    keyboard = [
        [InlineKeyboardButton("💲Deposit", callback_data='deposit'),
        InlineKeyboardButton("💵Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("💸Balance", callback_data='balance')],
        [InlineKeyboardButton("🎲Play Dice", callback_data='dice')]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(welcome_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

def confirmation_update_job(context: CallbackContext):

    job_context = {}
    raw_context = context.job.context
    if isinstance(raw_context, dict):
        job_context = raw_context
    elif isinstance(raw_context, tuple) and all(isinstance(item, tuple) and len(item) == 2 for item in raw_context):
        job_context = dict(raw_context)
    else:
        logging.error("Unexpected job context format. Ensure it's a dictionary or an iterable of key-value pairs.")
        return

    chat_id, uniqid = job_context.get('chat_id'), job_context.get('uniqid')
    username = job_context.get('username')
    amount = job_context.get('amount')

    if not chat_id or not uniqid:
        logging.error("Chat ID or Uniqid missing from the job context.")
        return

    now = datetime.now()

    first_check_time = job_context.get('first_check_time', now)
    job_context['first_check_time'] = first_check_time

    time_diff = now - first_check_time

    delete_after = timedelta(hours=2)

    current_status, crypto_hash = check_order_status(SELLIX_API_KEY, uniqid)

    if current_status:
        last_status = orderdb.get_order_status(uniqid)

        valid_transitions = [("PENDING", "WAITING_FOR_CONFIRMATIONS"),
                             ("PENDING", "COMPLETED"),
                             ("WAITING_FOR_CONFIRMATIONS", "COMPLETED")]

        if (last_status, current_status) in valid_transitions:
            message = f"Order <code>{uniqid}</code> status changed from <code>{last_status}</code> to <code>{current_status}</code>"
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
            logging.info(f"Order {uniqid} status changed from {last_status} to {current_status}")
            orderdb.update_order_status(uniqid, current_status)

            order_details = orderdb.get_order_details(uniqid)
            if crypto_hash and order_details and order_details[HASH_INDEX] != crypto_hash:
                orderdb.update_order_hash(uniqid, crypto_hash)
                #context.bot.send_message(chat_id=chat_id, text=f"Transaction hash: <code>{crypto_hash}</code>", parse_mode='HTML')

        if last_status == "PENDING" and time_diff > delete_after:
            success, message = delete_sellix_order(SELLIX_API_KEY, uniqid)
            if success:
                context.bot.send_message(chat_id=chat_id, text=f"Order <code>{uniqid}</code> has been automatically cancelled due to timeout.", parse_mode='HTML')
                orderdb.update_order_status(uniqid, "CANCELLED")
                logging.info(f"Order {uniqid} has been automatically cancelled due to timeout, Placed by: {chat_id}")
                context.job.schedule_removal()
            else:
                logging.error(f"Failed to automatically cancel order {uniqid}: {message}")

        if current_status == "COMPLETED":
            context.job.enabled = False
             # credit the amount to the user develop the logic and db for that
            if key:
                context.bot.send_message(chat_id=chat_id, text=f"Your key: <code>{key}</code>\nFor Plan: <b>{plan.upper()}</b>\nRedeem it by going into Licenses Section.", parse_mode='HTML')
                logging.info(f"Order {uniqid} is successfully completed, Plan: {plan}, Buyer: {chat_id}, Removing the Job")
                license_manager.mark_purchased(key)
            else:
                context.bot.send_message(chat_id=chat_id,text=f"Keys are out of stock for Plan: <b>{plan}</b>\nPlease Contact Support.",parse_mode='HTML')
                logging.info(f"Order {uniqid} is successfully completed, Key not delivered, reason: OUT OF STOCK. Plan: {plan},Buyer: {chat_id}")
            context.job.schedule_removal()
        elif current_status == "VOIDED":
            context.job.enabled = False
            logging.info(f"Order {uniqid} Was Cancelled, Buyer: {chat_id}, Removing the Job")
            context.job.schedule_removal()

    else:
        logging.error(f"No current status for order {uniqid}. It might be an API error or network issue.")




def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    updater.dispatcher.add_handler(CommandHandler('start',start))
    updater.dispatcher.add_handler(CallbackQueryHandler(balance_button,pattern='^balance$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(edit_to_main,pattern='^mainmenu$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(choose_crypto,pattern='^deposit$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_btc, pattern='^btc$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_ltc, pattern='^ltc$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_eth, pattern='^eth$'))
    #updater.dispatcher.add_handler(CallbackQueryHandler(,pattern='^$'))
    updater.start_polling()
    print("Polling...")
    updater.idle()

if __name__ == '__main__':
    main()
