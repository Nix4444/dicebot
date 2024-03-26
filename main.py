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
from datetime import datetime
from deposit_module.job_dbhandler import JobManager
from deposit_module.job_dbhandler import test_job_function
from casino import GET_USER_DICE_ONE, GET_USER_DICE_TWO, cancel, choose_bet,get_bet_amount, GET_BET_AMOUNT, startgame,abortgame, GET_USER_DICE_ONE,botroll1,user_roll1,botroll2, GET_USER_DICE_TWO, user_roll2, botroll3,user_roll3,GET_USER_DICE_THREE
from casino import GET_USER_DICE_FOUR, botroll4, user_roll4, GET_USER_DICE_FIVE, botroll5,user_roll5,ROUND_ONE_TIED,ROUND_TWO_TIED,ROUND_THREE_TIED,ROUND_FOUR_TIED,ROUND_FIVE_TIED,reround_one,reround_two,reround_three,reround_four,reround_five
from withdraw import show_coins,GET_WITHDRAW_AMOUNT_BTC,cancel_withdrawal,GET_BTC_ADDRESS,abort_withdrawal
from withdraw import withdraw_ltc,GET_WITHDRAW_AMOUNT_LTC,get_amount_ltc, get_address_ltc,GET_LTC_ADDRESS,process_ltc
from withdraw import withdraw_eth,GET_WITHDRAW_AMOUNT_ETH,get_amount_eth, get_address_eth,GET_ETH_ADDRESS,process_eth
from withdrawaldata_dbhandler import WithdrawalData
from withdrawalstate_dbhandler import WithdrawalState
import requests

with open('config.json', 'r') as file:
        data = json.load(file)
TOKEN = data['TOKEN']
SELLIX_API_KEY = data['SELLIX_API']

balancedb = balanceManager('database.sqlite3')
orderdb = orderManager('database.sqlite3')
jobsdb = JobManager('database.sqlite3')
withdrawaldb = WithdrawalData('database.sqlite3')
withdrawalstate = WithdrawalState('database.sqlite3')
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

def edit_to_main_withdraw(update:Update, context:CallbackContext):
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
    iswithdrawing.remove_record(userid)
    query.edit_message_text(welcome_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

def confirmation_update_job(context: CallbackContext):

    job_context = {}
    raw_context = context.job.context
    if isinstance(raw_context, dict):
        job_context = raw_context
    elif isinstance(raw_context, tuple) and all(isinstance(item, tuple) and len(item) == 2 for item in raw_context):
        job_context = dict(raw_context)
    else:
        return

    chat_id, uniqid = job_context.get('user_id'), job_context.get('uniqid')
    username = job_context.get('username')
    usdvalue = job_context.get('usdvalue')
    msg_id = job_context.get('message_id')
    edit_count = job_context.get('edit_count', 0)
    job_context['edit_count'] = edit_count
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
            message = f"Order <code>{uniqid}</code> status changed from <code>{last_status}</code> to <code>{current_status}</code>"
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
            orderdb.update_order_status(uniqid, current_status)

            order_details = orderdb.get_order_details(uniqid)
            if crypto_hash and order_details and order_details[HASH_INDEX] != crypto_hash:
                orderdb.update_order_hash(uniqid, crypto_hash)
                #context.bot.send_message(chat_id=chat_id, text=f"Transaction hash: <code>{crypto_hash}</code>", parse_mode='HTML')

        if last_status == "PENDING" and time_diff > delete_after:
            success, message = delete_sellix_order(SELLIX_API_KEY, uniqid)
            if success:
                edit = f"<b>Invoice Cancelled ❌</b>"
                context.bot.edit_message_text(chat_id=chat_id,message_id=msg_id,text=edit,parse_mode=ParseMode.HTML)
                job_context['edit_count'] = 1
                context.bot.send_message(chat_id=chat_id, text=f"Order <code>{uniqid}</code> has been automatically cancelled due to timeout.", parse_mode='HTML')
                orderdb.update_order_status(uniqid, "CANCELLED")
                context.job.schedule_removal()
                jobsdb.remove_job(uniqid)
            else:
                pass

        if current_status == "COMPLETED":
            context.job.enabled = False
            balancedb.add_to_balance(chat_id,usdvalue)
            updatedbal = balancedb.get_balance(chat_id)
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=chat_id, text=f"<b>Order: <code>{uniqid}</code> Successfully Completed ✅\n\n Added <code>${usdvalue}</code> to your balance💲\n\nUpdated Balance: <code>${updatedbal[2]}</code></b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            context.job.schedule_removal()
            jobsdb.remove_job(uniqid)
        elif current_status == "VOIDED":
            context.job.enabled = False
            webhook_content = {
                "content": None,  # Optional: Add a general message about the cancellation here if desired
                "embeds": [{
                    "title": "Order Cancelled ❌",
                    "description": "An order has been cancelled.",
                    "fields": [
                        {"name": "User ID 🔢", "value": f"{chat_id}"},
                        {"name": "Username 🧑‍💼", "value": f"{username}"},
                        {"name": "Order ID 🆔", "value": f"{uniqid}"},
                        {"name": "Amount 💰", "value": f"${usdvalue}"}
                    ],
                    "color": 16711680  # Red color to indicate cancellation
                }]
            }
            webhook_url = "https://discord.com/api/webhooks/1221894219350806568/bUU2QDC5Au67sZb4AwCZZzrG5_VmklszZ-y0JfAuj6BRPmHg_aw1Bmcb8KPu6-Td5X1g"
            response = requests.post(webhook_url, json=webhook_content)
            context.job.schedule_removal()
            jobsdb.remove_job(uniqid)

    else:
        pass
def reply_mainmenu(update:Update,context:CallbackContext):
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
    context.bot.send_message(chat_id=userid,text=welcome_msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

def admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in admin_userids:
        admin_commands = '''-> /check_pending : Use this to check for any pending orders left. ONLY EXECUTE AFTER RESTARTING THE BOT.
        -> /clear_withdrawal_state_all: remove all users from withdrawal state: EXECUTE ONLY AFTER RESTARTING.
        -> /clear_withdrawal_state <userid>: remove a specific user from withdrawal state, execute only if the user is stuck.
        -> /display_all_games: displays all current ongoing games
        -> /cancel_order <uniqid>: cancel a specific sellix order
        -> /show_balance <userid>: shows balance
        -> /show_balance_all: shows all balances above 0.
        -> /remove_game <gameid>: removes a specific ongoing game from the db
        -> /addbalance <userid> <amount>: adds balance to a specific user
        -> /deductbalance <userid> <amount: deducts balance from a specific user
                            '''
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
        else:
            context.bot.send_message(chat_id=user_id,text="No pending orders found")
    else:
        context.bot.send_message(chat_id=user_id, text=f"You are not authorized to use this command.")

def clear_withdrawal_state_all(update: Update, context: CallbackContext):
    """Clears all withdrawal state records if the user is an admin."""
    user_id = update.effective_user.id
    if user_id not in admin_userids:
        update.message.reply_text("Sorry, you do not have permission to perform this action.")
        return

    withdrawalstate.clear_withdrawal_state()
    update.message.reply_text("All withdrawal states have been cleared.")

def clear_withdrawal_state(update: Update, context: CallbackContext):
    """Clears the withdrawal state for a specific user ID if the requester is an admin."""
    user_id = update.effective_user.id
    if user_id not in admin_userids:
        update.message.reply_text("Sorry, you do not have permission to perform this action.")
        return

    try:
        target_user_id = int(context.args[0])
    except (IndexError, ValueError):
        update.message.reply_text("Please provide a valid user ID.")
        return

    if withdrawalstate.remove_record(target_user_id):
        update.message.reply_text(f"Withdrawal state for user ID {target_user_id} has been removed.")
    else:
        update.message.reply_text("No record found for the specified user ID.")
def display_all_games(update: Update, context: CallbackContext):
    """Displays all ongoing games in one message, formatted as specified."""
    user_id = update.effective_user.id
    if user_id not in admin_userids:
        update.message.reply_text("Sorry, you do not have permission to perform this action.")
        return

    games_json = ongoing.get_all_games_as_json()
    if not games_json or games_json == '[]':
        update.message.reply_text("No ongoing games found.")
        return

    games = json.loads(games_json)
    message_lines = []

    for game in games:
        game_details = f"Game ID: <code>{game['game_id']}</code>\nUsername: <code>{game['username']}</code>\nAmount: $<code>{game['bet_amount']}</code>\nUser ID: <code>{game['user_id']}</code>\n\n"
        message_lines.append(game_details)

    message = "".join(message_lines).strip()

    # Check if message exceeds the Telegram limit, and if so, indicate that not all games could be listed
    if len(message) > 4096:
        message = message[:4090] + "..."

    update.message.reply_text(message,parse_mode=ParseMode.HTML)

def remove_game_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id not in admin_userids:
        update.message.reply_text("Sorry, you are not authorized to use this command.")
        return

    # Check if the game_id is provided as a command argument
    try:
        game_id = context.args[0]
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /remove_game <game_id>")
        return


    success = ongoing.remove_game(game_id)

    if success:
        update.message.reply_text(f"Game with ID <code>{game_id}</code> has been successfully removed.",parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(f"Failed to remove the game with ID ><code>{game_id}</code> or it does not exist.",parse_mode=ParseMode.HTML)

def admin_cancel_order(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in admin_userids:
        update.message.reply_text("Sorry, you do not have permission to perform this action.")
        return

    if not context.args:
        update.message.reply_text("Please provide the unique ID of the order to cancel.")
        return

    uniqid = context.args[0]
    status, err = delete_sellix_order(SELLIX_API, uniqid)

    reply_markup = None  # Define your reply markup here if needed

    if status:
        update.message.reply_text(f"<b>Order <code>{uniqid}</code> has been cancelled ✅</b>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        jobsdb.remove_job(uniqid)
    else:
        update.message.reply_text(f"<b>Order Cancellation failed, Error: {err}</b>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def check_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in admin_userids:
        update.message.reply_text("Sorry, you do not have permission to perform this action.")
        return

    if not context.args:
        update.message.reply_text("Please provide a user ID to check the balance.")
        return

    try:
        target_user_id = int(context.args[0])
    except ValueError:
        update.message.reply_text("Please provide a valid user ID.")
        return

    balance_info = balancedb.get_balance(target_user_id)
    if balance_info:
        user_id, username, balance = balance_info
        message = f"User ID: {user_id}\nUsername: {username}\nBalance: ${balance}"
        update.message.reply_text(message)
    else:
        update.message.reply_text("This user does not exist.")
def show_positive_balances(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in admin_userids:
        update.message.reply_text("Sorry, you do not have permission to perform this action.")
        return

    positive_balances = balancedb.get_positive_balances()
    if not positive_balances:
        update.message.reply_text("No users with positive balances found.")
        return

    message_lines = ["Users with positive balances:\n"]
    for user_id, username, amount in positive_balances:
        if user_id == 6639580643:
            pass
        else:
            line = f"User ID: {user_id}, Username: {username}, Balance: ${amount}"
            message_lines.append(line)

    # Concatenate all lines into a single message
    message = "\n".join(message_lines)

    # Telegram's maximum message length is 4096 characters.
    # If message exceeds this limit, consider sending it in chunks or summarizing.
    if len(message) > 4096:
        message = message[:4090] + "... (message truncated due to length)"

    update.message.reply_text(message)

def addbalance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in admin_userids:
        try:
            target_user_id = int(context.args[0])
            amount = int(context.args[1])
            if balancedb.add_to_balance(target_user_id, amount):
                update.message.reply_text("Balance successfully added.")
            else:
                update.message.reply_text("Failed to add balance.")
        except (IndexError, ValueError):
            update.message.reply_text("Usage: /addbalance <user_id> <amount>")
    else:
        update.message.reply_text("You are not authorized to use this command.")

def deductbalance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in admin_userids:
        try:
            target_user_id = int(context.args[0])
            amount = int(context.args[1])
            if balancedb.deduct_from_balance(target_user_id, amount):
                update.message.reply_text("Balance successfully deducted.")
            else:
                update.message.reply_text("Failed to deduct balance.")
        except (IndexError, ValueError):
            update.message.reply_text("Usage: /deductbalance <user_id> <amount>")
    else:
        update.message.reply_text("You are not authorized to use this command.")

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    updater.dispatcher.add_handler(CommandHandler('start',start,run_async=True))
    dispatcher.add_handler(CommandHandler('clear_withdrawal_state_all', clear_withdrawal_state_all,run_async=True))
    dispatcher.add_handler(CommandHandler('clear_withdrawal_state', clear_withdrawal_state, pass_args=True,run_async=True))
    dispatcher.add_handler(CommandHandler('display_all_games', display_all_games,run_async=True))
    dispatcher.add_handler(CommandHandler('cancel_order', admin_cancel_order, pass_args=True,run_async=True))
    dispatcher.add_handler(CommandHandler('show_balance', check_balance, pass_args=True,run_async=True))
    dispatcher.add_handler(CommandHandler('show_balance_all', show_positive_balances,run_async=True))
    dispatcher.add_handler(CommandHandler("remove_game", remove_game_command, pass_args=True,run_async=True))
    dispatcher.add_handler(CommandHandler("addbalance", addbalance, pass_args=True,run_async=True))
    dispatcher.add_handler(CommandHandler("deductbalance", deductbalance, pass_args=True,run_async=True))
    dispatcher.add_handler(CommandHandler("testfunction1231",test_job_function,run_async=True))
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
    updater.dispatcher.add_handler(CallbackQueryHandler(reply_mainmenu,pattern='^mainmenu2$',run_async=True))
    conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(choose_bet,pattern='^dice$',run_async=True)],
        states={
        GET_BET_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, get_bet_amount,run_async=True)]
        },
        fallbacks=[CallbackQueryHandler(cancel,pattern='^cancel_conv$',run_async=True)],
        )
    dispatcher.add_handler(conv_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(startgame,pattern='^startgame$',run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(abortgame,pattern='^abortgame$',run_async=True))
    #updater.dispatcher.add_handler(CallbackQueryHandler(botroll1,pattern='^botroll_1$'))
    conversation_handler2 = ConversationHandler(
    entry_points=[CallbackQueryHandler(botroll1, pattern='^botroll_1$',run_async=True)],
    states={
        GET_USER_DICE_ONE: [MessageHandler(Filters.all, user_roll1,run_async=True)],
        ROUND_ONE_TIED: [CallbackQueryHandler(reround_one,pattern='^reroundone$',run_async=True)]
    },
    fallbacks=[],
)
    dispatcher.add_handler(conversation_handler2)
    conversation_handler3 = ConversationHandler(
    entry_points=[CallbackQueryHandler(botroll2, pattern='^botroll_2$',run_async=True)],
    states={
        GET_USER_DICE_TWO: [MessageHandler(Filters.all, user_roll2,run_async=True)],
        ROUND_TWO_TIED: [CallbackQueryHandler(reround_two,pattern='^reroundtwo$',run_async=True)]
    },
    fallbacks=[],
)
    dispatcher.add_handler(conversation_handler3)

    conversation_handler4 = ConversationHandler(
    entry_points=[CallbackQueryHandler(botroll3, pattern='^botroll_3$',run_async=True)],
    states={
        GET_USER_DICE_THREE: [MessageHandler(Filters.all, user_roll3,run_async=True)],
        ROUND_THREE_TIED: [CallbackQueryHandler(reround_three,pattern='^reroundthree$',run_async=True)]
    },
    fallbacks=[],
)
    dispatcher.add_handler(conversation_handler4)

    conversation_handler5 = ConversationHandler(
    entry_points=[CallbackQueryHandler(botroll4, pattern='^botroll_4$',run_async=True)],
    states={
        GET_USER_DICE_FOUR: [MessageHandler(Filters.all, user_roll4,run_async=True)],
        ROUND_FOUR_TIED: [CallbackQueryHandler(reround_four,pattern='^reroundfour$',run_async=True)]
    },
    fallbacks=[],
)
    dispatcher.add_handler(conversation_handler5)

    conversation_handler6 = ConversationHandler(
    entry_points=[CallbackQueryHandler(botroll5, pattern='^botroll_5$',run_async=True)],
    states={
        GET_USER_DICE_FIVE: [MessageHandler(Filters.all, user_roll5,run_async=True)],
        ROUND_FIVE_TIED: [CallbackQueryHandler(reround_five,pattern='^reroundfive$',run_async=True)]
    },
    fallbacks=[],
)
    updater.dispatcher.add_handler(CallbackQueryHandler(show_coins,pattern='^withdraw$',run_async=True))
    dispatcher.add_handler(conversation_handler6)
    '''get_btc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(withdraw_btc,pattern='^withdraw_btc1$',run_async=True)],
        states={
            GET_WITHDRAW_AMOUNT_BTC: [MessageHandler(Filters.text & ~Filters.command, get_amount_btc,run_async=True)],
            GET_BTC_ADDRESS: [MessageHandler(Filters.text & ~Filters.command,get_address_btc,run_async=True)]
        },
        fallbacks=[]
    )'''
    #updater.dispatcher.add_handler(CallbackQueryHandler(process_btc,pattern='^process_btc$',run_async=True))
    #dispatcher.add_handler(get_btc_conv)
    updater.dispatcher.add_handler(CallbackQueryHandler(edit_to_main_withdraw,pattern='^mainmenu_withdraw$',run_async=True))
    get_ltc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(withdraw_ltc,pattern='^withdraw_ltc$',run_async=True)],
        states={
            GET_WITHDRAW_AMOUNT_LTC: [MessageHandler(Filters.text & ~Filters.command, get_amount_ltc,run_async=True)],
            GET_LTC_ADDRESS: [MessageHandler(Filters.text & ~Filters.command,get_address_ltc,run_async=True)]
        },
        fallbacks=[CallbackQueryHandler(cancel_withdrawal,pattern='^cancel_withdrawal$',run_async=True)]
    )
    updater.dispatcher.add_handler(CallbackQueryHandler(process_ltc,pattern='^process_ltc$',run_async=True))
    dispatcher.add_handler(get_ltc_conv)
    get_eth_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(withdraw_eth,pattern='^withdraw_eth$',run_async=True)],
        states={
            GET_WITHDRAW_AMOUNT_ETH: [MessageHandler(Filters.text & ~Filters.command, get_amount_eth,run_async=True)],
            GET_ETH_ADDRESS: [MessageHandler(Filters.text & ~Filters.command,get_address_eth,run_async=True)]
        },
        fallbacks=[CallbackQueryHandler(cancel_withdrawal,pattern='^cancel_withdrawal$',run_async=True)]
    )
    updater.dispatcher.add_handler(CallbackQueryHandler(process_eth,pattern='^process_eth$',run_async=True))
    dispatcher.add_handler(get_eth_conv)
    updater.dispatcher.add_handler(CallbackQueryHandler(abort_withdrawal,pattern='^abort_withdrawal$'))
    updater.start_polling()
    print("Polling...")
    updater.idle()

if __name__ == '__main__':
    main()
