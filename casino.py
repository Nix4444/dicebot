from telegram import InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from deposit_module.balance_dbhandler import balanceManager
from deposit_module.order_databasehandler import orderManager
from deposit_module.job_dbhandler import JobManager
from ongoing_gamesdbhandler import OngoingGame
from dice_dbhandler import DiceManager
import string,random

balancedb = balanceManager('database.sqlite3')
orderdb = orderManager('database.sqlite3')
jobsdb = JobManager('database.sqlite3')
ongoing = OngoingGame('database.sqlite3')
dicedata = DiceManager('database.sqlite3')
GET_BET_AMOUNT = 0

def generate_random_id(length=12):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

def choose_bet(update: Update, context: CallbackContext):
    userid = update.effective_user.id
    username = update.effective_user.username
    query = update.callback_query
    query.answer()
    msg = "<b>Please enter the amount to bet 🎲</b>"
    keyboard = [[InlineKeyboardButton("❌Cancel",callback_data='cancel_conv')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    message_id = query.message.message_id
    context.user_data['bet_message_id'] = message_id
    return GET_BET_AMOUNT

def get_bet_amount(update: Update, context: CallbackContext):
    bet_amount = update.message.text
    userid = update.effective_user.id
    message_id = context.user_data['bet_message_id']
    userbal = balancedb.get_balance(userid)
    try:
        bet_amount = int(bet_amount)
        if bet_amount > 0:
            if bet_amount <= userbal[2]:
                keyboard = [[InlineKeyboardButton("✅Start",callback_data='startgame'),InlineKeyboardButton("❌Abort",callback_data='abortgame')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(f"<b>You have bet <code>${bet_amount}</code>\nYour Current Balance: <code>${userbal[2]}</code>\nYour Current Balance will be deducted upon proceeding.\n\nRules⚠\n1.First one to win three rounds, wins the money.\n2. If both dice get the same number, the round will be played again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>Bet Selected ✅</b>",parse_mode=ParseMode.HTML)
                context.user_data.clear()
                context.user_data['bet_amt'] = bet_amount
                return ConversationHandler.END
            else:
                
                keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')],[InlineKeyboardButton("💲Deposit",callback_data='deposit')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(f"<b>Please add more Balance to play.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>❌Insufficient Balance</b>",parse_mode=ParseMode.HTML)
                return ConversationHandler.END
        else:
            raise ValueError
    except ValueError:
        context.bot.edit_message_text(chat_id=userid,message_id=message_id,text="<b>Invalid Bet ❌</b>",parse_mode=ParseMode.HTML)
        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("<b>Invalid response. Please enter a valid positive number to bet.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        context.user_data.clear()
        return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text('<b>Game Cancelled.</b>',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    return ConversationHandler.END

def startgame(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    userid = update.effective_user.id
    username = update.effective_user.username
    bet_amt = context.user_data['bet_amt']
    context.user_data.clear()
    if jobsdb.check_user_exists(userid):
        keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before playing or cancel the order.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    else:
        if ongoing.check_user_exists(userid):
            keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text("<b>⚠ You already have an going game, Finish it before starting another one.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        else:
            gameid = generate_random_id()
            ongoing.add_game(gameid,userid,username,bet_amt)
            dicedata.add_ids(gameid,userid,username,bet_amt)
            query.edit_message_text(f"<b>Starting Round 1...🎲\n Goodluck!</b>")

            



def abortgame(update:Update,context:CallbackContext):
    print('aborted')


'''
keyboard = [
                    [KeyboardButton("/yes"), KeyboardButton("/exit")]
                ]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
'''