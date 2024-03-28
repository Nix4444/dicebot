from telegram import Game, InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler
from telegram.message import Message
from deposit_module.balance_dbhandler import balanceManager
from deposit_module.order_databasehandler import orderManager
from deposit_module.job_dbhandler import JobManager
from ongoing_gamesdbhandler import OngoingGame
from dice_dbhandler import DiceManager
import string,random,json
import time
from withdrawalstate_dbhandler import WithdrawalState
balancedb = balanceManager('database.sqlite3')
orderdb = orderManager('database.sqlite3')
jobsdb = JobManager('database.sqlite3')
ongoing = OngoingGame('database.sqlite3')
dicedata = DiceManager('database.sqlite3')
iswithdrawing = WithdrawalState('database.sqlite3')

GET_BET_AMOUNT = 0
GET_USER_DICE_ONE = 1
GET_USER_DICE_TWO = 2
GET_USER_DICE_THREE = 3
GET_USER_DICE_FOUR = 4
GET_USER_DICE_FIVE = 5
ROUND_ONE_TIED = 6
ROUND_TWO_TIED = 7
ROUND_THREE_TIED = 8
ROUND_FOUR_TIED = 9
ROUND_FIVE_TIED = 10

def generate_random_id(length=20):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

def is_message_forwarded(update, message: Message) -> bool:
    """Check if the specified message is forwarded.

    Args:
        update: The Telegram update object, used for context (optional in this version).
        message: The message object to check if it's forwarded.

    Returns:
        bool: True if the message is forwarded, False otherwise.
    """
    return bool(message.forward_date)

def choose_bet(update: Update, context: CallbackContext):
    userid = update.effective_user.id
    username = update.effective_user.username
    query = update.callback_query
    query.answer()
    if ongoing.check_user_exists(userid):
                    keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    query.edit_message_text("<b>⚠ You already have an ongoing game, Finish it before starting another one.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)

    if iswithdrawing.user_exists(userid):
         keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
         reply_markup = InlineKeyboardMarkup(keyboard)
         msg = f"<b>Please Cancel the ongoing withdrawal before starting a new game!</b>"
         query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
         return ConversationHandler.END
    else:
        current_balance = balancedb.get_balance(userid)
        msg = f"<b>Please enter the amount in USD to bet 🎲\nMinimum Bet: <code>$3</code>\nCurrent Balance: <code>${current_balance[2]}</code></b>"
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
    username = update.effective_user.username
    try:
        bet_amount = int(bet_amount)

        if iswithdrawing.user_exists(userid):
            keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            msg = f"<b>Please Cancel or Complete the ongoing withdrawal before starting a new game!</b>"
            update.message.reply_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        elif bet_amount > 0:
                if bet_amount <= userbal[2]:
                    if bet_amount >= 3:
                        gameid = generate_random_id()
                        ongoing.add_game(gameid,userid,username,bet_amount)
                        keyboard = [[InlineKeyboardButton("✅Start",callback_data='startgame'),InlineKeyboardButton("❌Abort",callback_data='abortgame')]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        update.message.reply_text(f"<b>You have bet <code>${bet_amount}</code>\nYour Current Balance: <code>${userbal[2]}</code>\nYour Current Balance will be deducted upon proceeding.\n\nRules⚠\n1.First one to win three rounds, wins the money.\n2. If both dice get the same number, the round will be played again.\n3. Game will end and your bet will not be refunded if you try to forward anything to the bot.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                        context.bot.edit_message_text(chat_id=userid,message_id=message_id,text=f"<b>Bet Amount: <code>${bet_amount}</code>✅</b>",parse_mode=ParseMode.HTML)
                        context.user_data['bet_amt'] = bet_amount
                        return ConversationHandler.END
                    else:
                        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')],[InlineKeyboardButton("💲Deposit",callback_data='deposit')]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        update.message.reply_text(f"<b>Minimum Bet: <code>$3</code></b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                        context.bot.edit_message_text(chat_id=userid,message_id=message_id,text=f"<b>You need to bet equal to or more than <code>$3</code> ❌</b>",parse_mode=ParseMode.HTML)
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

        if iswithdrawing.user_exists(userid):
            keyboard = [[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            msg = f"<b>Please Cancel or Complete the ongoing withdrawal before starting a new game!</b>"
            query.edit_message_text(msg,reply_markup=reply_markup,parse_mode=ParseMode.HTML)
            gameid = ongoing.get_gameid_from_userid(userid)
            ongoing.remove_game(gameid)
        else:
            context.user_data['bet_amt']
            bet_amt = context.user_data['bet_amt']
            if jobsdb.check_user_exists(userid):
                keyboard =[[InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text("<b>⚠ You have a pending invoice to be paid.\nPlease wait for it to confirm before playing or cancel the invoice.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                gameid = ongoing.get_gameid_from_userid(userid)
                ongoing.remove_game(gameid)

            else:
                    balancedb.deduct_from_balance(userid,bet_amt)
                    gameid = ongoing.get_gameid_from_userid(userid)
                    dicedata.add_ids(gameid,userid,username,bet_amt)
                    keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_1")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    query.edit_message_text(f"<b>🎲 Starting Round 1...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)

    except KeyError:
        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(f"<b>Bet Error, please start the game again.</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
        ongoing.remove_game(gameid)


def abortgame(update:Update,context:CallbackContext):
    query = update.callback_query
    query.answer()
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(f"<b>Aborted the game ✅</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    ongoing.remove_game(gameid)


def botroll1(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    message = context.bot.send_dice(chat_id=userid, emoji='🎲')
    dice_value = message.dice.value
    dicedata.add_round(gameid,'bot','1',dice_value)
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
    time.sleep(3.5)
    context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
    return GET_USER_DICE_ONE

def user_roll1(update: Update, context: CallbackContext):
    usermsg = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if is_message_forwarded(update,usermsg):
        keyboard = [
                    [InlineKeyboardButton("🎲 Play Dice", callback_data='dice'), InlineKeyboardButton("💻 Main Menu", callback_data='mainmenu2')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)


        context.bot.send_message(
                    chat_id=userid,
                    text="<b>Game ended.\n\nYou Lost because you tried to cheat.</b>",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.HTML
                )
        context.bot.send_message(
                    chat_id=userid,
                    text="<b>What would you like to do next?</b>",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
        dicedata.add_winner(gameid,'ATTEMPTED_CHEAT')
        ongoing.remove_game(gameid)
        return ConversationHandler.END
    else:
        if usermsg.dice:
            first_bot_roll_value = dicedata.get_round_value(gameid,'bot','1')
            value = usermsg.dice.value
            time.sleep(3.5)
            context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
            if value == first_bot_roll_value:
                keyboard = [[InlineKeyboardButton("🎲 Play Round 1 Again",callback_data="reroundone")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(chat_id=userid,text=f"<b><u>Round 1 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{first_bot_roll_value}</code>\n\nRound 1 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)

                return ROUND_ONE_TIED
            else:
                dicedata.add_round(gameid,'user','1',value)
                if value > first_bot_roll_value:
                    context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 1 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{first_bot_roll_value}</code>\nYou Won Round 1.\n\n<u>Scores💯</u>
                        \nYour Score: <code>1</code>\nBot Score: <code>0</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                    dicedata.enter_user_score(gameid,1)
                    dicedata.enter_bot_score(gameid,0)
                    keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_2")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 2...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return ConversationHandler.END

                elif first_bot_roll_value > value:
                    context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 1 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{first_bot_roll_value}</code>\nYou Lost Round 1\n\n<u>Scores💯</u>
                    \nYour Score: <code>0</code>\nBot Score: <code>1</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                    dicedata.enter_user_score(gameid,0)
                    dicedata.enter_bot_score(gameid,1)
                    keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_2")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 2...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return ConversationHandler.END
                else:
                    context.bot.send_message(chat_id=userid, text=f"<b>Invalid response, roll a dice</b>", parse_mode="HTML")
                    return GET_USER_DICE_ONE
def botroll2(update: Update, context: CallbackContext) -> int:
            query = update.callback_query
            query.answer()
            query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
            userid = update.effective_user.id
            gameid = ongoing.get_gameid_from_userid(userid)
            message = context.bot.send_dice(chat_id=userid, emoji='🎲')
            dice_value = message.dice.value
            dicedata.add_round(gameid,'bot','2',dice_value)
            reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
            time.sleep(3.5)
            context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
            return GET_USER_DICE_TWO

def user_roll2(update: Update, context: CallbackContext):
    usermsg2 = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if is_message_forwarded(update,usermsg2):
        keyboard = [
                    [InlineKeyboardButton("🎲 Play Dice", callback_data='dice'), InlineKeyboardButton("💻 Main Menu", callback_data='mainmenu2')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)


        context.bot.send_message(
                    chat_id=userid,
                    text="<b>Game ended.\n\nYou Lost because you tried to cheat.</b>",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.HTML
                )
        context.bot.send_message(
                    chat_id=userid,
                    text="<b>What would you like to do next?</b>",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
        dicedata.add_winner(gameid,'ATTEMPTED_CHEAT')
        ongoing.remove_game(gameid)
        return ConversationHandler.END
    else:
        if usermsg2.dice:
                second_bot_roll_value = dicedata.get_round_value(gameid,'bot','2')
                value = usermsg2.dice.value
                time.sleep(3.5)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                if value == second_bot_roll_value:
                    keyboard = [[InlineKeyboardButton("🎲 Play Round 2 Again",callback_data="reroundtwo")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.bot.send_message(chat_id=userid,text=f"<b><u>Round 2 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{second_bot_roll_value}</code>\n\nRound 2 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return ROUND_TWO_TIED
                else:
                    dicedata.add_round(gameid,'user','2',value)
                    curr_bot_score, curr_user_score = dicedata.get_scores(gameid)
                    if value > second_bot_roll_value:
                        new_user_score = curr_user_score + 1
                        context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 2 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{second_bot_roll_value}</code>\nYou Won Round 2.\n\n<u>Scores💯</u>
                            \nYour Score: <code>{new_user_score}</code>\nBot Score: <code>{curr_bot_score}</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                        dicedata.enter_user_score(gameid,new_user_score)
                        #dicedata.enter_bot_score(gameid,)
                        keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_3")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 3...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                        return ConversationHandler.END

                    elif second_bot_roll_value > value:
                        new_bot_score = curr_bot_score + 1
                        context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 2 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{second_bot_roll_value}</code>\nYou Lost Round 2.\n\n<u>Scores💯</u>
                            \nYour Score: <code>{curr_user_score}</code>\nBot Score: <code>{new_bot_score}</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                        #dicedata.enter_user_score(gameid,0)
                        dicedata.enter_bot_score(gameid,new_bot_score)
                        keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_3")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 3...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                        return ConversationHandler.END
        else:
                context.bot.send_message(chat_id=userid, text=f"<b>Invalid response, roll a dice</b>", parse_mode="HTML")
                return GET_USER_DICE_TWO

def botroll3(update: Update, context: CallbackContext) -> int:
            query = update.callback_query
            query.answer()
            query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
            userid = update.effective_user.id
            gameid = ongoing.get_gameid_from_userid(userid)
            message = context.bot.send_dice(chat_id=userid, emoji='🎲')
            dice_value = message.dice.value
            dicedata.add_round(gameid,'bot','3',dice_value)
            reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
            time.sleep(3.5)
            context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
            return GET_USER_DICE_THREE

def user_roll3(update: Update, context: CallbackContext):
    usermsg3 = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if is_message_forwarded(update,usermsg3):
        keyboard = [
                    [InlineKeyboardButton("🎲 Play Dice", callback_data='dice'), InlineKeyboardButton("💻 Main Menu", callback_data='mainmenu2')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)


        context.bot.send_message(
                    chat_id=userid,
                    text="<b>Game ended.\n\nYou Lost because you tried to cheat.</b>",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.HTML
                )
        context.bot.send_message(
                    chat_id=userid,
                    text="<b>What would you like to do next?</b>",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
        dicedata.add_winner(gameid,'ATTEMPTED_CHEAT')
        ongoing.remove_game(gameid)
        return ConversationHandler.END
    else:
        if usermsg3.dice:
                third_bot_roll_value = dicedata.get_round_value(gameid,'bot','3')
                value = usermsg3.dice.value
                time.sleep(3.5)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                if value == third_bot_roll_value:
                    keyboard = [[InlineKeyboardButton("🎲 Play Round 3 Again",callback_data="reroundthree")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.bot.send_message(chat_id=userid,text=f"<b><u>Round 3 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{third_bot_roll_value}</code>\n\nRound 3 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return ROUND_THREE_TIED
                else:
                    dicedata.add_round(gameid,'user','3',value)
                    curr_bot_score, curr_user_score = dicedata.get_scores(gameid)
                    if value > third_bot_roll_value:
                        new_user_score = curr_user_score + 1
                        context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 3 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{third_bot_roll_value}</code>\nYou Won Round 3.\n\n<u>Scores💯</u>
                            \nYour Score: <code>{new_user_score}</code>\nBot Score: <code>{curr_bot_score}</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                        dicedata.enter_user_score(gameid,new_user_score)
                        if new_user_score == 3:
                            bet_amt = dicedata.get_bet(gameid)
                            bet_amt = int(bet_amt[0])
                            credit = bet_amt + bet_amt
                            curr_balance = balancedb.get_balance(userid)
                            curr_balance = curr_balance[2]
                            balancedb.add_to_balance(userid,credit)
                            dicedata.add_winner(gameid,'USER')
                            keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu2')]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f'''<b>You won this match!🤑\n\nWinnings: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance + credit}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            ongoing.remove_game(gameid)
                            return ConversationHandler.END
                        else:
                            keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_4")]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 4...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            return ConversationHandler.END

                    elif third_bot_roll_value > value:
                        new_bot_score = curr_bot_score + 1
                        context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 3 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{third_bot_roll_value}</code>\nYou Lost Round 3.\n\n<u>Scores💯</u>
                            \nYour Score: <code>{curr_user_score}</code>\nBot Score: <code>{new_bot_score}</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                        dicedata.enter_bot_score(gameid,new_bot_score)
                        if new_bot_score == 3:
                            bet_amt = dicedata.get_bet(gameid)
                            bet_amt = int(bet_amt[0])
                            curr_balance = balancedb.get_balance(userid)
                            dicedata.add_winner(gameid,'BOT')
                            keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu2')]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f'''<b>You Lost this match🎲\n\nBet Placed: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance[2]}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            ongoing.remove_game(gameid)

                            return ConversationHandler.END
                        else:
                            keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_4")]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 4...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            return ConversationHandler.END
        else:
                context.bot.send_message(chat_id=userid, text=f"<b>Invalid response, roll a dice</b>", parse_mode="HTML")
                return GET_USER_DICE_THREE

def botroll4(update: Update, context: CallbackContext) -> int:
            query = update.callback_query
            query.answer()
            query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
            userid = update.effective_user.id
            gameid = ongoing.get_gameid_from_userid(userid)
            message = context.bot.send_dice(chat_id=userid, emoji='🎲')
            dice_value = message.dice.value
            dicedata.add_round(gameid,'bot','4',dice_value)
            reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
            time.sleep(3.5)
            context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
            return GET_USER_DICE_FOUR

def user_roll4(update: Update, context: CallbackContext):
    usermsg4 = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if is_message_forwarded(update,usermsg4):
        keyboard = [
                    [InlineKeyboardButton("🎲 Play Dice", callback_data='dice'), InlineKeyboardButton("💻 Main Menu", callback_data='mainmenu2')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)


        context.bot.send_message(
                    chat_id=userid,
                    text="<b>Game ended.\n\nYou Lost because you tried to cheat.</b>",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.HTML
                )
        context.bot.send_message(
                    chat_id=userid,
                    text="<b>What would you like to do next?</b>",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
        dicedata.add_winner(gameid,'ATTEMPTED_CHEAT')
        ongoing.remove_game(gameid)
        return ConversationHandler.END
    else:
        if usermsg4.dice:
                four_bot_roll_value = dicedata.get_round_value(gameid,'bot','4')
                value = usermsg4.dice.value
                time.sleep(3.5)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                if value == four_bot_roll_value:
                    keyboard = [[InlineKeyboardButton("🎲 Play Round 4 Again",callback_data="reroundfour")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.bot.send_message(chat_id=userid,text=f"<b><u>Round 4 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{four_bot_roll_value}</code>\n\nRound 4 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return ROUND_FOUR_TIED
                else:
                    dicedata.add_round(gameid,'user','4',value)
                    curr_bot_score, curr_user_score = dicedata.get_scores(gameid)
                    if value > four_bot_roll_value:
                        new_user_score = curr_user_score + 1
                        context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 4 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{four_bot_roll_value}</code>\nYou Won Round 4.\n\n<u>Scores💯</u>
                            \nYour Score: <code>{new_user_score}</code>\nBot Score: <code>{curr_bot_score}</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                        dicedata.enter_user_score(gameid,new_user_score)
                        if new_user_score == 3:
                            bet_amt = dicedata.get_bet(gameid)
                            bet_amt = int(bet_amt[0])
                            credit = bet_amt + bet_amt
                            curr_balance = balancedb.get_balance(userid)
                            curr_balance = curr_balance[2]
                            balancedb.add_to_balance(userid,credit)
                            dicedata.add_winner(gameid,'USER')
                            keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu2')]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f'''<b>You won this match!🤑\n\nWinnings: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance + credit}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            ongoing.remove_game(gameid)

                            return ConversationHandler.END
                        else:
                            keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_5")]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 5...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            return ConversationHandler.END

                    elif four_bot_roll_value > value:
                        new_bot_score = curr_bot_score + 1
                        context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 4 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{four_bot_roll_value}</code>\nYou Lost Round 4.\n\n<u>Scores💯</u>
                            \nYour Score: <code>{curr_user_score}</code>\nBot Score: <code>{new_bot_score}</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                        dicedata.enter_bot_score(gameid,new_bot_score)
                        if new_bot_score == 3:
                            bet_amt = dicedata.get_bet(gameid)
                            bet_amt = int(bet_amt[0])
                            curr_balance = balancedb.get_balance(userid)
                            dicedata.add_winner(gameid,'BOT')
                            keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu2')]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f'''<b>You Lost this match🎲\n\nBet Placed: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance[2]}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            ongoing.remove_game(gameid)

                            return ConversationHandler.END
                        else:
                            keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_5")]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 5...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            return ConversationHandler.END
        else:
                context.bot.send_message(chat_id=userid, text=f"<b>Invalid response, roll a dice</b>", parse_mode="HTML")
                return GET_USER_DICE_FOUR

def botroll5(update: Update, context: CallbackContext) -> int:
            query = update.callback_query
            query.answer()
            query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
            userid = update.effective_user.id
            gameid = ongoing.get_gameid_from_userid(userid)
            message = context.bot.send_dice(chat_id=userid, emoji='🎲')
            dice_value = message.dice.value
            dicedata.add_round(gameid,'bot','5',dice_value)
            reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
            time.sleep(3.5)
            context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
            return GET_USER_DICE_FIVE

def user_roll5(update: Update, context: CallbackContext):
    usermsg5 = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if is_message_forwarded(update,usermsg5):
        keyboard = [
                    [InlineKeyboardButton("🎲 Play Dice", callback_data='dice'), InlineKeyboardButton("💻 Main Menu", callback_data='mainmenu2')]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)


        context.bot.send_message(
                    chat_id=userid,
                    text="<b>Game ended.\n\nYou Lost because you tried to cheat.</b>",
                    reply_markup=ReplyKeyboardRemove(),
                    parse_mode=ParseMode.HTML
                )
        context.bot.send_message(
                    chat_id=userid,
                    text="<b>What would you like to do next?</b>",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
        dicedata.add_winner(gameid,'ATTEMPTED_CHEAT')
        ongoing.remove_game(gameid)
        return ConversationHandler.END
    else:
        if usermsg5.dice:
                five_bot_roll_value = dicedata.get_round_value(gameid,'bot','5')
                value = usermsg5.dice.value
                time.sleep(3.5)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                if value == five_bot_roll_value:
                    keyboard = [[InlineKeyboardButton("🎲 Play Round 5 Again",callback_data="reroundfive")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    context.bot.send_message(chat_id=userid,text=f"<b><u>Round 5 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{five_bot_roll_value}</code>\n\nRound 5 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                    return ROUND_FIVE_TIED
                else:
                    dicedata.add_round(gameid,'user','5',value)
                    curr_bot_score, curr_user_score = dicedata.get_scores(gameid)
                    if value > five_bot_roll_value:
                        new_user_score = curr_user_score + 1
                        context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 5 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{five_bot_roll_value}</code>\nYou Won Round 5.\n\n<u>Scores💯</u>
                            \nYour Score: <code>{new_user_score}</code>\nBot Score: <code>{curr_bot_score}</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                        dicedata.enter_user_score(gameid,new_user_score)
                        if new_user_score == 3:
                            bet_amt = dicedata.get_bet(gameid)
                            bet_amt = int(bet_amt[0])
                            credit = bet_amt + bet_amt
                            curr_balance = balancedb.get_balance(userid)
                            curr_balance = curr_balance[2]
                            balancedb.add_to_balance(userid,credit)
                            dicedata.add_winner(gameid,'USER')
                            keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu2')]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f'''<b>You won this match!🤑\n\nWinnings: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance + credit}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            ongoing.remove_game(gameid)

                            return ConversationHandler.END
                        else:
                            keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="askdjnaj")]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 5...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            return ConversationHandler.END

                    elif five_bot_roll_value > value:
                        new_bot_score = curr_bot_score + 1
                        context.bot.send_message(chat_id=userid,text=f'''<b><u>Round 5 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{five_bot_roll_value}</code>\nYou Lost Round 5.\n\n<u>Scores💯</u>
                            \nYour Score: <code>{curr_user_score}</code>\nBot Score: <code>{new_bot_score}</code></b>''',reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                        dicedata.enter_bot_score(gameid,new_bot_score)
                        if new_bot_score == 3:
                            bet_amt = dicedata.get_bet(gameid)
                            bet_amt = int(bet_amt[0])
                            curr_balance = balancedb.get_balance(userid)
                            dicedata.add_winner(gameid,'BOT')
                            keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu2')]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f'''<b>You Lost this match🎲\n\nBet Placed: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance[2]}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            ongoing.remove_game(gameid)
                            return ConversationHandler.END
                        else:
                            keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="fkasfkja")]]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            context.bot.send_message(chat_id=userid,text=f"<b>🎲 Starting Round 5...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
                            return ConversationHandler.END
        else:
                context.bot.send_message(chat_id=userid, text=f"<b>Invalid response, roll a dice</b>", parse_mode="HTML")
                return GET_USER_DICE_FIVE

def reround_one(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    message = context.bot.send_dice(chat_id=userid, emoji='🎲')
    dice_value = message.dice.value
    dicedata.add_round(gameid,'bot','1',dice_value)
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
    time.sleep(3.5)
    context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
    return GET_USER_DICE_ONE

def reround_two(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    message = context.bot.send_dice(chat_id=userid, emoji='🎲')
    dice_value = message.dice.value
    dicedata.add_round(gameid,'bot','2',dice_value)
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
    time.sleep(3.5)
    context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
    return GET_USER_DICE_TWO

def reround_three(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    message = context.bot.send_dice(chat_id=userid, emoji='🎲')
    dice_value = message.dice.value
    dicedata.add_round(gameid,'bot','3',dice_value)
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
    time.sleep(3.5)
    context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
    return GET_USER_DICE_THREE

def reround_four(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    message = context.bot.send_dice(chat_id=userid, emoji='🎲')
    dice_value = message.dice.value
    dicedata.add_round(gameid,'bot','4',dice_value)
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
    time.sleep(3.5)
    context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
    return GET_USER_DICE_FOUR

def reround_five(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    message = context.bot.send_dice(chat_id=userid, emoji='🎲')
    dice_value = message.dice.value
    dicedata.add_round(gameid,'bot','5',dice_value)
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
    time.sleep(3.5)
    context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
    return GET_USER_DICE_FIVE
