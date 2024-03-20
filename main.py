import json
from telegram import InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,

)
from deposit_module.order_databasehandler import orderManager
from deposit_module.balance_dbhandler import balanceManager
from deposit_module.create_order import create_order
from deposit_module.conf_check import check_order_status
from deposit_module.delete_order import delete_sellix_order
from datetime import timedelta, datetime
from deposit_module.deposit_buttons import *
import logging
from datetime import datetime
from deposit_module.job_dbhandler import JobManager
from casino import cancel, choose_bet,get_bet_amount, GET_BET_AMOUNT, startgame,abortgame,botroll1
with open('config.json', 'r') as file:
        data = json.load(file)
TOKEN = data['TOKEN']
SELLIX_API_KEY = data['SELLIX_API']

balancedb = balanceManager('database.sqlite3')
orderdb = orderManager('database.sqlite3')
jobsdb = JobManager('database.sqlite3')
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

    chat_id, uniqid = job_context.get('user_id'), job_context.get('uniqid')
    username = job_context.get('username')
    usdvalue = job_context.get('usdvalue')
    msg_id = job_context.get('message_id')
    edit_count = job_context.get('edit_count', 0)
    job_context['edit_count'] = edit_count
    print(job_context)
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
            if job_context['edit_count'] == 0:
                edit = f"<b>Payment Detected ✅\n\nPlease wait for 2 confirmations.</b>"
                context.bot.edit_message_text(chat_id=chat_id,message_id=msg_id,text=edit,parse_mode=ParseMode.HTML)
                job_context['edit_count'] = 1
                print(f"edited {msg_id} once")
            message = f"Order <code>{uniqid}</code> status changed from <code>{last_status}</code> to <code>{current_status}</code>"
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
            logging.info(f"Order {uniqid} status changed from {last_status} to {current_status}")
            print(f"Order {uniqid} status changed from {last_status} to {current_status}")
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
                jobsdb.remove_job(uniqid)
            else:
                logging.error(f"Failed to automatically cancel order {uniqid}: {message}")

        if current_status == "COMPLETED":
            context.job.enabled = False
            balancedb.add_to_balance(chat_id,usdvalue)
            updatedbal = balancedb.get_balance(chat_id)
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=chat_id, text=f"<b>Order: <code>{uniqid}</code> Successfully Completed ✅\n\n Added <code>${usdvalue}</code> to your balance💲\n\nUpdated Balance: <code>${updatedbal[2]}</code></b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            logging.info(f"Added ${usdvalue} to user: {username} userid: {chat_id} updated balance: {updatedbal[2]}")
            print(f"Added ${usdvalue} to user: {username} userid: {chat_id} updated balance: {updatedbal[2]}")
            context.job.schedule_removal()
            jobsdb.remove_job(uniqid)
        elif current_status == "VOIDED":
            context.job.enabled = False
            logging.info(f"Order {uniqid} Was Cancelled, Buyer: {chat_id}, Removing the Job")
            print(f"Order {uniqid} Was Cancelled, Buyer: {chat_id}, Removing the Job")
            context.job.schedule_removal()
            jobsdb.remove_job(uniqid)

    else:
        logging.error(f"No current status for order {uniqid}. It might be an API error or network issue.")

def admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in admin_userids:
        admin_commands = '''-> /check_pending : Use this to check for any pending orders left. ONLY EXECUTE AFTER RESTARTING THE BOT.'''
        context.bot.send_message(chat_id=user_id, text=admin_commands)
    else:
        context.bot.send_message(chat_id=user_id, text=f"You are not authorized to use this command.")
def check_pending(update:Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in admin_userids:
        jobs_json = jobsdb.get_all_jobs_as_json()
        if jobs_json:
            jobs = json.loads(jobs_json)
            for job in jobs:
                job_context = {
                    'user_id': job['user_id'],
                    'uniqid': job['uniqid'],
                    'username': job['username'],
                    'usdvalue': job['usdvalue'],
                    'msg_id': job['msg_id']
                }
                context.job_queue.run_repeating(confirmation_update_job, interval=10, first=0, context=job_context)
                print("added",job_context)
        else:
            context.bot.send_message(chat_id=user_id,text="No pending orders found")
    else:
        context.bot.send_message(chat_id=user_id, text=f"You are not authorized to use this command.")


def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    updater.dispatcher.add_handler(CommandHandler('start',start,run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(balance_button,pattern='^balance$',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(edit_to_main,pattern='^mainmenu$',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(choose_crypto,pattern='^deposit$',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_btc, pattern='^btc$',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_ltc, pattern='^ltc$',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_eth, pattern='^eth$',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_deposit, pattern='^(btc|ltc|eth)_deposit_',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_cancel_confirmation,pattern='^cncl_',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_decline_cancel,pattern='^decline_cancel_',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(handle_confirm_cancel,pattern='^confirm_cancel_',run_async=True))
    updater.dispatcher.add_handler(CommandHandler('admin',admin,run_async=True))
    updater.dispatcher.add_handler(CommandHandler('check_pending',check_pending,run_async=True))
    conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(choose_bet,pattern='^dice$',run_async=True)],
        states={
        GET_BET_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, get_bet_amount,run_async=True)]
        },
        fallbacks=[CallbackQueryHandler(cancel,pattern='^cancel_conv$',run_async=True)],
        )
    dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(startgame,pattern='^startgame$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(abortgame,pattern='^abortgame$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(botroll1,pattern='^botroll1$'))
    updater.start_polling()
    print("Polling...")
    updater.idle()

if __name__ == '__main__':
    main()
