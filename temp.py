from telegram import Bot


import requests

'''# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot_token = '7010604660:AAFSXx_QkDK3RT3-0sci4Y0ctWQ7tpswvk4'

# Replace 'CHAT_ID' with the chat ID you want to send the dice animation to
chat_id = '5455454489'

# Telegram API endpoint for sending dice animation
url = f'https://api.telegram.org/bot{bot_token}/sendDice'

# Optional parameters:
# emoji: Emoji on which the dice animation should be based
# disable_notification: Sends the message silently (users will receive a notification with no sound)
params = {
    'chat_id': chat_id,
    'emoji': '🎲',  # You can customize the dice emoji
    'disable_notification': False  # Change to True if you want to disable notifications
}

# Sending the request
response = requests.get(url, params=params)

# Checking the response
if response.status_code == 200:
    print('Dice animation sent successfully!', response.text)
else:
    print('Failed to send dice animation:', response.text)'''



'''from telegram.ext import Updater, MessageHandler, Filters

# Define a function to handle incoming messages
def handle_message(update, context):
    message = update.message
    if message.dice:
        dice_emoji = message.dice.emoji
        value = message.dice.value
        chat_id = message.chat_id
        # Do something with the dice emoji, value, and chat_id
        print(f"Dice emoji received: {dice_emoji}, Value: {value}, Chat ID: {chat_id}")

# Set up the bot
updater = Updater(token='7010604660:AAFSXx_QkDK3RT3-0sci4Y0ctWQ7tpswvk4', use_context=True)
dispatcher = updater.dispatcher

# Register the message handler
dispatcher.add_handler(MessageHandler(Filters.dice, handle_message))

# Start the bot
updater.start_polling()
updater.idle()
print('polling')
'''

'''from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Define a function to handle the /roll command
def roll(update, context):
    confirmation_message = (
                "press to roll"
            )
    update.effective_message.reply_text(confirmation_message, reply_markup=ReplyKeyboardMarkup([['🎲']], one_time_keyboard=True, resize_keyboard=True))

# Define a function to handle incoming messages
def handle_message(update, context):
    message = update.message
    if message.dice:
        dice_emoji = message.dice.emoji
        value = message.dice.value
        chat_id = message.chat_id
        # Do something with the dice emoji, value, and chat_id
        print(f"Dice emoji received: {dice_emoji}, Value: {value}, Chat ID: {chat_id}")

# Set up the bot
updater = Updater(token='7010604660:AAFSXx_QkDK3RT3-0sci4Y0ctWQ7tpswvk4', use_context=True)
dispatcher = updater.dispatcher

# Register the /roll command handler
dispatcher.add_handler(CommandHandler("roll", roll))

# Register the message handler
dispatcher.add_handler(MessageHandler(Filters.dice, handle_message))

# Start the bot
updater.start_polling()
updater.idle()'''


import requests

# Set your bot's API token
bot_token = '7010604660:AAFSXx_QkDK3RT3-0sci4Y0ctWQ7tpswvk4'

# Set the chat ID and message ID of the message you want to edit
chat_id = '5455454489'
#message_id = 'YOUR_MESSAGE_ID'



'''# Form the API request URL
url = f'https://api.telegram.org/bot{bot_token}/editMessageText'

# Set the parameters for editing the message
params = {
    'chat_id': chat_id,
    'message_id': 418,
    'text': "edited lmfao"
}

url_send = f'https://api.telegram.org/bot{bot_token}/sendMessage'

# Set the parameters for sending the message
params_send = {
    'chat_id': chat_id,
    'text': "hey lol"
}

# Send the edit message request
response = requests.post(url, params=params)
print(response.text)
'''
