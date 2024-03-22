from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

def check_forwarded_dice(update: Update, context: CallbackContext):
    message = update.effective_message
    if message.forward_from or message.forward_from_chat:
        # Check if the message is a forwarded message
        if hasattr(message, 'dice'):
            # The message has a dice object, meaning it's a dice roll
            context.bot.send_message(chat_id=message.chat_id,
                                     text=f"Dice with value {message.dice.value} was forwarded to the bot.")
        elif '🎲' in message.text:
            # The message contains a static dice emoji in text
            context.bot.send_message(chat_id=message.chat_id,
                                     text="A message with a dice emoji was forwarded to the bot.")
        else:
            context.bot.send_message(chat_id=message.chat_id,
                                     text="The forwarded message does not contain a dice emoji.")
    else:
        context.bot.send_message(chat_id=message.chat_id,
                                 text="This message was not forwarded.")

def main():
    updater = Updater("7010604660:AAFSXx_QkDK3RT3-0sci4Y0ctWQ7tpswvk4", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.all, check_forwarded_dice))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
