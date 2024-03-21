from telegram import Game, InlineKeyboardButton,InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ParseMode, KeyboardButton, ReplyKeyboardRemove
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
GET_USER_DICE_ONE = 1
GET_USER_DICE_TWO = 2
GET_USER_DICE_THREE = 3
GET_USER_DICE_FOUR = 4
GET_USER_DICE_FIVE = 5

def generate_random_id(length=20):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

def choose_bet(update: Update, context: CallbackContext):
    userid = update.effective_user.id
    username = update.effective_user.username
    query = update.callback_query
    query.answer()
    current_balance = balancedb.get_balance(userid)
    msg = f"<b>Please enter the amount in USD to bet 🎲\nCurrent Balance: <code>${current_balance[2]}</code></b>"
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
                balancedb.deduct_from_balance(userid,bet_amt)
                gameid = generate_random_id()
                print("gameid",gameid)
                ongoing.add_game(gameid,userid,username,bet_amt)
                dicedata.add_ids(gameid,userid,username,bet_amt)
                keyboard = [[InlineKeyboardButton("🤖Bot Roll",callback_data="botroll_1")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                query.edit_message_text(f"<b>🎲 Starting Round 1...\n\nPress the button to make the bot roll the dice🎲️</b>",reply_markup=reply_markup,parse_mode=ParseMode.HTML)
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



def botroll1(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text("<b>Bot is rolling...</b>", parse_mode="HTML")
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    message = context.bot.send_dice(chat_id=userid, emoji='🎲')
    dice_value = message.dice.value
    dicedata.add_round(gameid,'bot','1',dice_value)
    print(f"Game ID: {gameid}, Bot Rolled: {dice_value}")# Replace with your actual data handling
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("🎲")]], one_time_keyboard=True, resize_keyboard=True)
    context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
    return GET_USER_DICE_ONE

def user_roll1(update: Update, context: CallbackContext):
    usermsg = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if usermsg.dice:
            first_bot_roll_value = dicedata.get_round_value(gameid,'bot','1')
            value = usermsg.dice.value
            if value == first_bot_roll_value:
                context.bot.send_message(chat_id=userid,text=f"<b><u>Round 1 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{first_bot_roll_value}</code>\n\nRound 1 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                ongoing.remove_game(gameid) #remove this later
                #finish the logic
                return ConversationHandler.END #CHANGE THIS
            else:
                dicedata.add_round(gameid,'user','1',value)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
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
            context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
            return GET_USER_DICE_TWO

def user_roll2(update: Update, context: CallbackContext):
    usermsg2 = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if usermsg2.dice:
            second_bot_roll_value = dicedata.get_round_value(gameid,'bot','2')
            value = usermsg2.dice.value
            if value == second_bot_roll_value:
                context.bot.send_message(chat_id=userid,text=f"<b><u>Round 2 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{second_bot_roll_value}</code>\n\nRound 2 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                ongoing.remove_game(gameid) #remove this later
                #finish the logic
                return ConversationHandler.END #CHANGE THIS
            else:
                dicedata.add_round(gameid,'user','2',value)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                curr_bot_score, curr_user_score = dicedata.get_scores(gameid)
                print(curr_bot_score,curr_user_score)
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
            context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
            return GET_USER_DICE_THREE

def user_roll3(update: Update, context: CallbackContext):
    usermsg3 = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if usermsg3.dice:
            third_bot_roll_value = dicedata.get_round_value(gameid,'bot','3')
            value = usermsg3.dice.value
            if value == third_bot_roll_value:
                context.bot.send_message(chat_id=userid,text=f"<b><u>Round 3 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{third_bot_roll_value}</code>\n\nRound 3 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                ongoing.remove_game(gameid) #remove this later
                #finish the logic
                return ConversationHandler.END #CHANGE THIS
            else:
                dicedata.add_round(gameid,'user','3',value)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                curr_bot_score, curr_user_score = dicedata.get_scores(gameid)
                print(curr_bot_score,curr_user_score)
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
                        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        context.bot.send_message(chat_id=userid,text=f'''<b>You won this match!🤑\n\nBet Placed: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance + credit}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
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
                        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
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
            context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
            return GET_USER_DICE_FOUR

def user_roll4(update: Update, context: CallbackContext):
    usermsg4 = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if usermsg4.dice:
            four_bot_roll_value = dicedata.get_round_value(gameid,'bot','4')
            value = usermsg4.dice.value
            if value == four_bot_roll_value:
                context.bot.send_message(chat_id=userid,text=f"<b><u>Round 4 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{four_bot_roll_value}</code>\n\nRound 4 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                ongoing.remove_game(gameid) #remove this later
                #finish the logic
                return ConversationHandler.END #CHANGE THIS
            else:
                dicedata.add_round(gameid,'user','4',value)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                curr_bot_score, curr_user_score = dicedata.get_scores(gameid)
                print(curr_bot_score,curr_user_score)
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
                        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        context.bot.send_message(chat_id=userid,text=f'''<b>You won this match!🤑\n\nBet Placed: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance + credit}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
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
                        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
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
            context.bot.send_message(chat_id=userid, text=f"<b>Bot rolled: <code>{dice_value}</code>\n\nPress the Dice Button to roll 🎲</b>", reply_markup=reply_markup, parse_mode="HTML")
            return GET_USER_DICE_FIVE

def user_roll5(update: Update, context: CallbackContext):
    usermsg5 = update.message
    userid = update.effective_user.id
    gameid = ongoing.get_gameid_from_userid(userid)
    if usermsg5.dice:
            five_bot_roll_value = dicedata.get_round_value(gameid,'bot','5')
            value = usermsg5.dice.value
            if value == five_bot_roll_value:
                context.bot.send_message(chat_id=userid,text=f"<b><u>Round 5 Results🎉</u>\n\nYou Rolled: <code>{value}</code>\nBot Rolled: <code>{five_bot_roll_value}</code>\n\nRound 5 is tied.\n\nPress the button to make the bot roll the dice again🎲️</b>",reply_markup=ReplyKeyboardRemove(),parse_mode=ParseMode.HTML)
                ongoing.remove_game(gameid) #remove this later
                #finish the logic
                return ConversationHandler.END #CHANGE THIS
            else:
                dicedata.add_round(gameid,'user','5',value)
                context.bot.send_message(chat_id=userid, text=f"<b>You rolled <code>{value}</code>.</b>",reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
                curr_bot_score, curr_user_score = dicedata.get_scores(gameid)
                print(curr_bot_score,curr_user_score)
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
                        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        context.bot.send_message(chat_id=userid,text=f'''<b>You won this match!🤑\n\nBet Placed: <code>${bet_amt}</code>\nUpdated Balance: <code>${curr_balance + credit}</code></b>''',reply_markup=reply_markup,parse_mode=ParseMode.HTML)
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
                        keyboard = [[InlineKeyboardButton("🎲Play Dice", callback_data='dice'),InlineKeyboardButton("💻Main Menu", callback_data='mainmenu')]]
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
