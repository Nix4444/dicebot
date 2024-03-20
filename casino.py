from telegram import InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from deposit_module.balance_dbhandler import balanceManager
from deposit_module.order_databasehandler import orderManager
from deposit_module.job_dbhandler import JobManager
from ongoing_gamesdbhandler import OngoingGame
from dice_dbhandler import DiceManager
import string,random,json

balancedb = balanceManager('database.sqlite3')
orderdb = orderManager('database.sqlite3')
jobsdb = JobManager('database.sqlite3')
ongoing = OngoingGame('database.sqlite3')
dicedata = DiceManager('database.sqlite3')
GET_BET_AMOUNT = 0
GET_USER_DICE_ONE,GET_USER_DICE_TWO,GET_USER_DICE_THREE = range(3)

def generate_random_id(length=20):
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
    try:
        context.user_data['bet_amt']
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
                print("gameid",gameid)
                ongoing.add_game(gameid,userid,username,bet_amt)
                dicedata.add_ids(gameid,userid,username,bet_amt)
                keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_1")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(f"<b>♠️ Starting Round 1...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                context.user_data.clear()

    except KeyError:
        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(f"<b>Bet Error, please start the game again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)


def abortgame(update:Update,context:CallbackContext):
    query = update.callback_query
    query.answer()
    keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(f"<b>Aborted the game ✅</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)

'''def botroll1(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
    userid = update.effective_user.id
    # Simulate retrieving game ID and recording bot's dice roll
    #gameid = ongoing.get_gameid_from_userid(userid)
    message = context.bot.send_dice(chat_id=userid, emoji='🎲')
    dice_value = message.dice.value
    dicedata.add_round(gameid,'bot','1',dice_value)
    print(f"Game ID: {gameid}, Bot Rolled: {dice_value}")# Replace with your actual data handling
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
    context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>g</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
    return GET_USER_DICE_ONE

def user_roll1(update: Update, context: CallbackContext):
    print("here")
    user_first_roll = update.message.text
    userid = update.effective_user.id
    context.bot.send_message(chat_id=userid, text=f"{user_first_roll}",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    return ConversationHandler.END
    '''
'''if user_first_roll.dice:
        dice_emoji = user_first_roll.dice.emoji
        value = user_first_roll.dice.value
        
        # Add your logic here for what to do with the user's dice roll
        
        context.bot.send_message(chat_id=userid, text=f"You rolled {dice_emoji} with a value of {value}.",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
        
        # Move to the next part of the conversation or end it
        return ConversationHandler.END  # Assuming this is the end of this conversation part
    else:
        context.bot.send_message(chat_id=userid, text=f"Invalid, roll a dice", parse_mode="HTML")
        return GET_USER_DICE_ONE
'''



'''
keyboard = [
                    [KeyboardButton("/yes"), KeyboardButton("/exit")]
                ]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
'''
