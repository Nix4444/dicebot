from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram.ext import CallbackContext

# States
NAME = 0
NAME1 = 1

def start(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask for the user's name."""
    keyboard = [[InlineKeyboardButton("Click here to start", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Hi there! Click on the button below to start.", reply_markup=reply_markup)
    return NAME

def handle_button_click(update: Update, context: CallbackContext) -> int:
    """Handle the button click."""
    query = update.callback_query
    query.answer()
    query.message.reply_text("Please tell me your name.")
    return NAME

def save_name(update: Update, context: CallbackContext) -> int:
    """Save the name and send it back."""
    name = update.message.text
    update.message.reply_text(f"Nice to meet you, {name}!")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel and end the conversation."""
    update.message.reply_text("Canceled.")
    return ConversationHandler.END

def main():
    # Set up the Telegram Bot
    updater = Updater("7010604660:AAFSXx_QkDK3RT3-0sci4Y0ctWQ7tpswvk4", use_context=True)
    dispatcher = updater.dispatcher

    # Add command handler for /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Define ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_button_click, pattern='^start$')],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, save_name)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Add ConversationHandler to dispatcher
    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
