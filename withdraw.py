from telegram import Game, InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from telegram.message import Message
from deposit_module.balance_dbhandler import balanceManager
from deposit_module.order_databasehandler import orderManager
from deposit_module.job_dbhandler import JobManager
from ongoing_gamesdbhandler import OngoingGame
from dice_dbhandler import DiceManager
from withdrawalstate_dbhandler import WithdrawalState
from transact_ltc import create_broadcast, usd_to_ltc_to_litoshis
from transact_eth import send_eth
from web3 import Web3
from withdrawaldata_dbhandler import WithdrawalData
import requests
balancedb = balanceManager('database.sqlite3')
orderdb = orderManager('database.sqlite3')
jobsdb = JobManager('database.sqlite3')
ongoing = OngoingGame('database.sqlite3')
dicedata = DiceManager('database.sqlite3')
iswithdrawing = WithdrawalState('database.sqlite3')
withdrawaldb = WithdrawalData('database.sqlite3')

GET_WITHDRAW_AMOUNT_BTC = 0
GET_BTC_ADDRESS = 1
GET_WITHDRAW_AMOUNT_LTC = 2
GET_LTC_ADDRESS = 3
GET_WITHDRAW_AMOUNT_ETH = 4
GET_ETH_ADDRESS = 5

def cancel_withdrawal(update:Update,context:CallbackContext):
    query = update.callback_query
    query.answer()
    userid = update.effective_user.id
    msg =f"Withdrawal Cancelled❌"
    keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    iswithdrawing.remove_record(userid)
    query.edit_message_text(text=msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    return ConversationHandler.END
def abort_withdrawal(update:Update,context:CallbackContext):
    query = update.callback_query
    query.answer()
    userid = update.effective_user.id
    msg =f"Withdrawal Aborted❌"
    keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    iswithdrawing.remove_record(userid)
    query.edit_message_text(text=msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    return ConversationHandler.END

def show_coins(update:Update,context:CallbackContext):
    userid = update.effective_user.id
    username = update.effective_user.username
    query = update.callback_query
    query.answer()
    iswithdrawing.add_record(userid,username)
    msg = f"<b>Select a coin to process withdrawal💳</b>"
    keyboard = [[InlineKeyboardButton("Litecoin",callback_data='withdraw_ltc')],[InlineKeyboardButton("Ethereum",callback_data='withdraw_eth')],[InlineKeyboardButton("◀️Back", callback_data='mainmenu_withdraw')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)

'''def withdraw_btc(update:Update, context:CallbackContext):

    userid = update.effective_user.id
    current_balance = balancedb.get_balance(userid)
    if jobsdb.check_user_exists(userid):
        query = update.callback_query
        query.answer()
        msg = f"<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>"
        keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)

        return ConversationHandler.END
    elif ongoing.check_user_exists(userid):
        query = update.callback_query
        query.answer()
        msg = f"<b>⚠ You have game unfinished, Finish it first before withdrawing money.</b>"
        keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)
        return ConversationHandler.END
    else:
            query = update.callback_query
            query.answer()
            msg = f"<b>Enter the amount that you want to withdraw in USD\n\nCurrent Balance: <code>${current_balance[2]}</code></b>"
            keyboard = [[InlineKeyboardButton("❌ Cancel",callback_data='cancel_withdrawal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            message_id = query.message.message_id
            context.user_data['withdraw_message_id'] = message_id
            return GET_WITHDRAW_AMOUNT_BTC

def get_amount_btc(update:Update, context:CallbackContext):
    amt_withdraw = update.message.text
    userid = update.effective_user.id
    message_id = context.user_data['withdraw_message_id']
    current_balance = balancedb.get_balance(userid)
    try:
        amt_withdraw = int(amt_withdraw)
        if jobsdb.check_user_exists(userid):
            msg = f"<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>"
            keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        elif ongoing.check_user_exists(userid):
            msg = f"<b>⚠ You have game unfinished, Finish it first before withdrawing money.</b>"
            keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        else:
            if amt_withdraw >= 5:
                if amt_withdraw <= current_balance[2]:
                    keyboard = [[InlineKeyboardButton("❌ Cancel",callback_data='cancel_withdrawal')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.user_data['amt_withdraw'] = amt_withdraw
                    context.bot.edit_message_text(chat_id=userid,message_id=message_id,text=f"<b>⚠ In Process...</b>",parse_mode=ParseMode.HTML)
                    text = f"<b>Enter your Bitcoin Address\n\n⚠ No refunds will be provided if you make a mistake.</b>"
                    update.message.reply_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return GET_BTC_ADDRESS
                else:
                    keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    update.message.reply_text(f"<b>Not Enough Balance to withdraw!</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>❌Insufficient Balance</b>",parse_mode=ParseMode.HTML)
                    iswithdrawing.remove_record(userid)
                    return ConversationHandler.END
            else:
                raise ValueError
    except ValueError:
            context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>Invalid Amount ❌\n\nMinimum Amount: <code>$5</code></b>",parse_mode=ParseMode.HTML)
            keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("<b>Invalid response. Please enter a valid positive number to withdraw.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END

def get_address_btc(update:Update,context:CallbackContext):
    userid = update.effective_user.id
    btc_address = update.message.text
    try:
        context.user_data['amt_withdraw']
        amt_withdraw = context.user_data['amt_withdraw']
        if jobsdb.check_user_exists(userid):
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        else:
            if ongoing.check_user_exists(userid):
                keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text("<b>⚠ You already have an ongoing game, Finish it before withdrawing money.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                iswithdrawing.remove_record(userid)
                return ConversationHandler.END
            else:
                text = f"<b>⚙ Review your withdrawal details\n\nAmount: <code>${amt_withdraw}</code>\nBTC Address: <code>{btc_address}</code></b>"
                keyboard = [[InlineKeyboardButton("✅ Process Withdrawal",callback_data='process_btc'),InlineKeyboardButton("❌Abort",callback_data='abort_withdrawal')]]
                reply_markup=InlineKeyboardMarkup(keyboard)
                update.message.reply_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                context.user_data['btc_address'] = btc_address
                return ConversationHandler.END
    except KeyError:
        keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f"<b>Unknown Error, please try withdrawing again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)
        return ConversationHandler.END



def process_btc(update:Update,context:CallbackContext):
    userid = update.effective_user.id
    query = update.callback_query
    query.answer()
    try:
        amt_withdraw = context.user_data['amt_withdraw']
        btc_address = context.user_data['btc_address']
        if jobsdb.check_user_exists(userid):
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text("<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)

        else:
            if ongoing.check_user_exists(userid):
                keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text("<b>⚠ You already have an ongoing game, Finish it before withdrawing money.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                iswithdrawing.remove_record(userid)

            else:
                keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')],[InlineKeyboardButton("💲Deposit",callback_data='deposit')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = f"Processing <code>${amt_withdraw}</code> to BTC Address: <code>{btc_address}</code>"
                curr_bal = balancedb.get_balance(userid)
                if amt_withdraw <= curr_bal[2]:
                    transact_btc(update,context,amount=amt_withdraw,addy=btc_address)
                    balancedb.deduct_from_balance(userid,amt_withdraw)
                    query.edit_message_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    iswithdrawing.remove_record(userid)
                else:
                    keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')],[InlineKeyboardButton("💲Deposit",callback_data='deposit')]]
                    query.edit_message_text(f"<b>Insufficient Balance!</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    except KeyError:
        keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(f"<b>Unknown Error, please try withdrawing again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)




def transact_btc(update:Update,context:CallbackContext,amount,addy):
    query = update.callback_query
    query.answer()
    print("processing: ",amount, addy)'''



def withdraw_ltc(update:Update, context:CallbackContext):

    userid = update.effective_user.id
    current_balance = balancedb.get_balance(userid)
    if jobsdb.check_user_exists(userid):
        query = update.callback_query
        query.answer()
        msg = f"<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>"
        keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)

        return ConversationHandler.END
    elif ongoing.check_user_exists(userid):
        query = update.callback_query
        query.answer()
        msg = f"<b>⚠ You have game unfinished, Finish it first before withdrawing money.</b>"
        keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)
        return ConversationHandler.END
    else:
            query = update.callback_query
            query.answer()
            msg = f"<b>Enter the amount that you want to withdraw in USD\n\nCurrent Balance: <code>${current_balance[2]}</code></b>"
            keyboard = [[InlineKeyboardButton("❌ Cancel",callback_data='cancel_withdrawal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            message_id = query.message.message_id
            context.user_data['withdraw_message_id'] = message_id
            return GET_WITHDRAW_AMOUNT_LTC

def get_amount_ltc(update:Update, context:CallbackContext):
    amt_withdraw = update.message.text
    userid = update.effective_user.id
    message_id = context.user_data['withdraw_message_id']
    current_balance = balancedb.get_balance(userid)
    try:
        amt_withdraw = int(amt_withdraw)
        if jobsdb.check_user_exists(userid):
            msg = f"<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>"
            keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        elif ongoing.check_user_exists(userid):
            msg = f"<b>⚠ You have game unfinished, Finish it first before withdrawing money.</b>"
            keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        else:
            if amt_withdraw >= 5:
                if amt_withdraw <= current_balance[2]:
                    keyboard = [[InlineKeyboardButton("❌ Cancel",callback_data='cancel_withdrawal')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.user_data['amt_withdraw'] = amt_withdraw
                    context.bot.edit_message_text(chat_id=userid,message_id=message_id,text=f"<b>⚠ In Process...</b>",parse_mode=ParseMode.HTML)
                    text = f"<b>Enter your Litecoin Address\n\n⚠ No refunds will be provided if you make a mistake.</b>"
                    update.message.reply_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return GET_LTC_ADDRESS
                else:
                    keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    update.message.reply_text(f"<b>Not Enough Balance to withdraw!</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>❌Insufficient Balance</b>",parse_mode=ParseMode.HTML)
                    iswithdrawing.remove_record(userid)
                    return ConversationHandler.END
            else:
                raise ValueError
    except ValueError:
            context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>Invalid Amount ❌\n\nMinimum Amount: <code>$5</code></b>",parse_mode=ParseMode.HTML)
            keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("<b>Invalid response. Please enter a valid positive number to withdraw.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END

def get_address_ltc(update:Update,context:CallbackContext):
    userid = update.effective_user.id
    ltc_address = update.message.text
    try:
        context.user_data['amt_withdraw']
        amt_withdraw = context.user_data['amt_withdraw']
        if jobsdb.check_user_exists(userid):
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        else:
            if ongoing.check_user_exists(userid):
                keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text("<b>⚠ You already have an ongoing game, Finish it before withdrawing money.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                iswithdrawing.remove_record(userid)
                return ConversationHandler.END
            else:
                text = f"<b>⚙ Review your withdrawal details\n\nAmount: <code>${amt_withdraw}</code>\nLTC Address: <code>{ltc_address}</code></b>"
                keyboard = [[InlineKeyboardButton("✅ Process Withdrawal",callback_data='process_ltc'),InlineKeyboardButton("❌Abort",callback_data='abort_withdrawal')]]
                reply_markup=InlineKeyboardMarkup(keyboard)
                update.message.reply_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                context.user_data['ltc_address'] = ltc_address
                return ConversationHandler.END
    except KeyError:
        keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f"<b>Unknown Error, please try withdrawing again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)
        return ConversationHandler.END



def process_ltc(update:Update,context:CallbackContext):
    userid = update.effective_user.id
    query = update.callback_query
    query.answer()
    try:
        amt_withdraw = context.user_data['amt_withdraw']
        ltc_address = context.user_data['ltc_address']
        if jobsdb.check_user_exists(userid):
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text("<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)

        else:
            if ongoing.check_user_exists(userid):
                keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text("<b>⚠ You already have an ongoing game, Finish it before withdrawing money.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                iswithdrawing.remove_record(userid)

            else:
                keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')],[InlineKeyboardButton("💲Deposit",callback_data='deposit')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = f"Processing <code>${amt_withdraw}</code> to LTC Address: <code>{ltc_address}</code>"
                curr_bal = balancedb.get_balance(userid)
                if amt_withdraw <= curr_bal[2]:
                    query.edit_message_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    balancedb.deduct_from_balance(userid,amt_withdraw)
                    transact_ltc(update,context,amount=amt_withdraw,addy=ltc_address)

                    iswithdrawing.remove_record(userid)
                else:
                    keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')],[InlineKeyboardButton("💲Deposit",callback_data='deposit')]]
                    query.edit_message_text(f"<b>Insufficient Balance!</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    except KeyError:
        keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(f"<b>Unknown Error, please try withdrawing again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)

def send_failed_transaction_notification(userid, username, addy, amount,coin):
    webhook_url = "https://discord.com/api/webhooks/1221894122848125129/7aSXxgI58XCdtdxMoeCCDCGZJmKofZrd6m_bBdbXvlXHM6OCuLUJvSIJlaQKqtcK84cb"  # Replace with your actual webhook URL
    content = {
        "content": "@everyone 🚨",  # Adding an emoji to grab attention
        "embeds": [{
            "title": "Withdrawal Failed!",
            "description": "A Withdrawal failed and needs immediate attention. Please check the details below.",
            "fields": [
                {"name": "User ID 🔢", "value": str(userid)},
                {"name": "Username 🧑", "value": username},
                {"name": "Address 🏠", "value": addy},
                {"name": "Amount 💰", "value": f"{amount}"},
                {"name": "Coin 🪙", "value": coin}
            ],
            "color": 0xFF0000
        }]
    }
    response = requests.post(webhook_url, json=content)



def transact_ltc(update:Update,context:CallbackContext,amount,addy):
    query = update.callback_query
    query.answer()
    value = usd_to_ltc_to_litoshis(amount)
    hash = create_broadcast(addy,value)
    userid = update.effective_user.id
    username = update.effective_user.username
    if hash:
        context.bot.send_message(
                        chat_id=userid,
                        text=f"<b>Successfully Processed ✅\n\nTransaction hash: <code>{hash}</code></b>",
                        parse_mode=ParseMode.HTML
                    )
        withdrawaldb.insert_withdrawal(userid,username,amount,coin="LTC",address=addy,hash_value=hash)
        iswithdrawing.remove_record(userid)
    else:
        context.bot.send_message(
                        chat_id=userid,
                        text=f"<b>Error Processing Litecoin ❌ Contact Support</b>",
                        parse_mode=ParseMode.HTML
                    )
        balancedb.add_to_balance(userid,amount)
        send_failed_transaction_notification(userid, username, addy, amount,coin="LTC")
        iswithdrawing.remove_record(userid)


def withdraw_eth(update:Update, context:CallbackContext):

    userid = update.effective_user.id
    current_balance = balancedb.get_balance(userid)
    if jobsdb.check_user_exists(userid):
        query = update.callback_query
        query.answer()
        msg = f"<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>"
        keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)

        return ConversationHandler.END
    elif ongoing.check_user_exists(userid):
        query = update.callback_query
        query.answer()
        msg = f"<b>⚠ You have game unfinished, Finish it first before withdrawing money.</b>"
        keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)
        return ConversationHandler.END
    else:
            query = update.callback_query
            query.answer()
            msg = f"<b>Enter the amount that you want to withdraw in USD\n\nCurrent Balance: <code>${current_balance[2]}</code>\nMinimum Amount: <code>$5</code></b>"
            keyboard = [[InlineKeyboardButton("❌ Cancel",callback_data='cancel_withdrawal')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            message_id = query.message.message_id
            context.user_data['withdraw_message_id'] = message_id
            return GET_WITHDRAW_AMOUNT_ETH

def get_amount_eth(update:Update, context:CallbackContext):
    amt_withdraw = update.message.text
    userid = update.effective_user.id
    message_id = context.user_data['withdraw_message_id']
    current_balance = balancedb.get_balance(userid)
    try:
        amt_withdraw = int(amt_withdraw)
        if jobsdb.check_user_exists(userid):
            msg = f"<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>"
            keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        elif ongoing.check_user_exists(userid):
            msg = f"<b>⚠ You have game unfinished, Finish it first before withdrawing money.</b>"
            keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        else:
            if amt_withdraw >= 5:

                if amt_withdraw <= current_balance[2]:
                    keyboard = [[InlineKeyboardButton("❌ Cancel",callback_data='cancel_withdrawal')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.user_data['amt_withdraw'] = amt_withdraw
                    context.bot.edit_message_text(chat_id=userid,message_id=message_id,text=f"<b>⚠ In Process...</b>",parse_mode=ParseMode.HTML)
                    text = f"<b>Enter your Ethereum ERC-20 Address\n\n⚠ No refunds will be provided if you make a mistake.</b>"
                    update.message.reply_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return GET_ETH_ADDRESS

                else:
                    keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    update.message.reply_text(f"<b>Not Enough Balance to withdraw!</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>❌Insufficient Balance</b>",parse_mode=ParseMode.HTML)
                    iswithdrawing.remove_record(userid)
                    return ConversationHandler.END
            else:
                raise ValueError
    except ValueError:
            context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>Invalid Amount ❌\n\nMinimum Amount: <code>$5</code></b>",parse_mode=ParseMode.HTML)
            keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("<b>Invalid response. Please enter a valid positive number to withdraw.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END

def get_address_eth(update:Update,context:CallbackContext):
    userid = update.effective_user.id
    eth_address = update.message.text
    try:
        context.user_data['amt_withdraw']
        amt_withdraw = context.user_data['amt_withdraw']
        if jobsdb.check_user_exists(userid):
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)
            return ConversationHandler.END
        else:
            if ongoing.check_user_exists(userid):
                keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text("<b>⚠ You already have an ongoing game, Finish it before withdrawing money.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                iswithdrawing.remove_record(userid)
                return ConversationHandler.END
            else:
                text = f"<b>⚙ Review your withdrawal details\n\nAmount: <code>${amt_withdraw}</code>\nETH Withdrawal Fee: <code>$2</code>\nETH Address: <code>{eth_address}</code></b>"
                keyboard = [[InlineKeyboardButton("✅ Process Withdrawal",callback_data='process_eth'),InlineKeyboardButton("❌Abort",callback_data='abort_withdrawal')]]
                reply_markup=InlineKeyboardMarkup(keyboard)
                update.message.reply_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                context.user_data['eth_address'] = eth_address
                return ConversationHandler.END
    except KeyError:
        keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f"<b>Unknown Error, please try withdrawing again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)
        return ConversationHandler.END



def process_eth(update:Update,context:CallbackContext):
    userid = update.effective_user.id
    query = update.callback_query
    query.answer()
    try:
        amt_withdraw = context.user_data['amt_withdraw']
        eth_address = context.user_data['eth_address']
        if jobsdb.check_user_exists(userid):
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text("<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before withdrawing or cancel the invoice.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            iswithdrawing.remove_record(userid)

        else:
            if ongoing.check_user_exists(userid):
                keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text("<b>⚠ You already have an ongoing game, Finish it before withdrawing money.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                iswithdrawing.remove_record(userid)

            else:
                keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')],[InlineKeyboardButton("💲Deposit",callback_data='deposit')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                text = f"Processing <code>${amt_withdraw}</code> to ETH Address: <code>{eth_address}</code>"
                curr_bal = balancedb.get_balance(userid)
                if amt_withdraw <= curr_bal[2]:
                    query.edit_message_text(text,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    balancedb.deduct_from_balance(userid,amt_withdraw)
                    transact_eth(update,context,amount=amt_withdraw,addy=eth_address)

                    iswithdrawing.remove_record(userid)
                else:
                    keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')],[InlineKeyboardButton("💲Deposit",callback_data='deposit')]]
                    query.edit_message_text(f"<b>Insufficient Balance!</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    except KeyError:
        keyboard = [[InlineKeyboardButton("💵Withdraw", callback_data='withdraw'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(f"<b>Unknown Error, please try withdrawing again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        iswithdrawing.remove_record(userid)




def transact_eth(update: Update, context: CallbackContext, amount, addy):
    query = update.callback_query
    query.answer()
    userid = update.effective_user.id
    username = update.effective_user.username
    tx_hash = send_eth(addy, amount)
    if tx_hash:
        context.bot.sendMessage(chat_id=userid, text=f"Transaction hash✅: <code>{tx_hash.hex()}</code>",parse_mode=ParseMode.HTML)
        w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/229a95048da349249136c1d9b4af80c8'))
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        withdrawaldb.insert_withdrawal(userid,username,amount,coin="ETH",address=addy,hash_value=tx_hash.hex())
        iswithdrawing.remove_record(userid)
        if tx_receipt.status == 1:
            context.bot.sendMessage(chat_id=userid, text=f"<b>Transaction <code>{tx_hash.hex()}</code> succeeded.</b>",parse_mode=ParseMode.HTML)
        elif tx_receipt.status == 0:
            context.bot.sendMessage(chat_id=userid, text="<b>Transaction <code>{tx_hash.hex()}</code> failed.</b>",parse_mode=ParseMode.HTML)
    else:
        context.bot.sendMessage(chat_id=userid,text=f"<b>Transaction failed ❌ Contact Support</b>",parse_mode=ParseMode.HTML)
        balancedb.add_to_balance(userid,amount)
        send_failed_transaction_notification(userid, username, addy, amount,coin="ETH")
        iswithdrawing.remove_record(userid)
