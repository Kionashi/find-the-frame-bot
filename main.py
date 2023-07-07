import ast
from typing import Final
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ConversationHandler, ContextTypes, CallbackQueryHandler, CallbackContext
import requests
import logging

BOT_TOKEN: Final = '6358703639:AAEY-bHVc4-cE3vZhdHxbDQE3pAs_nN3bic'
BOT_USERNAME: Final = 'find_the_frame_bot'
BASE_URL: Final = 'http://127.0.0.1:8000/bot'
VIDEO_NAME: Final = 'Falcon Heavy Test Flight (Hosted Webcast)-wbSwFU6tY1c'
FAQ: Final = [
    {'How do I begin?': 'Is easy, just type /begin and I will show you the first image so you can tell me when you found the correct frame when my rocket launches ' },
    {'How do I know if I found the frame?': 'Check the numbers in the top right corner of the image, if it has a T- it means the rocket has not launched yet, if it has T+ it means the rocket already launched, you must pin point when the timer is in T+ 00:00:00 by choosing between "It already launched" and "not yet" depending on what you see in each image. Of course when you find the frame push the "Found the frame" button'},
    {'Who made this amazing bot?': "Im glad you ask!, the developer who made this awesome bot is no other than Anibal Cardozo, this is actually his very first bot, so don't be too harsh on him. 😅 Im sure he did his best" },
    {'Are you the real Elon Musk? 👀': 'No, Im not the real Elon Musk....yet 👀'}
]

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    
    # Send introduction message
    await update.message.reply_text("Hello fellow human! 🤖")
    await update.message.reply_text("Im the Muskbot and I want to play a game with you. Im trying to find the exact frame in which one of my beautiful rockets launched, so if you wanna help me I will show you an image and you must tell me if the rocket already launched or not")
    await update.message.reply_text("Easy right?, If you have any questions check the FAQ with the /help command")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ Show the questions defined in the FAQ."""
        row1 = [
            InlineKeyboardButton(list(FAQ[0].keys())[0],callback_data=f"3*{{'question': '0'}}"),
        ]
        row2 = [
            InlineKeyboardButton(list(FAQ[1].keys())[0],callback_data=f"3*{{'question': '1'}}"),
        ]
        row3 = [
            InlineKeyboardButton(list(FAQ[2].keys())[0],callback_data=f"3*{{'question': '2'}}"),
        ]
        row4 = [
            InlineKeyboardButton(list(FAQ[3].keys())[0],callback_data=f"3*{{'question': '3'}}"),
        ]
        reply_markup=InlineKeyboardMarkup([row1,row2,row3,row4])
        await update.message.reply_text("What do you need to know?",reply_markup=reply_markup)

async def begin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Command to start the game."""
    try:
        response: requests.Response = requests.get(f'{BASE_URL}/video/{VIDEO_NAME}/start/')
        response =response.json()
        await update.message.reply_photo(response['frame_url'])
        reply_markup=generate_markup(response=response)
        await update.message.reply_text("Was the rocket launched? 👀 Im lost: /help Try again: /begin",reply_markup=reply_markup)
    
    except Exception as error:
        print('error==>',error)
        await update.message.reply_text('Hubo un error!')

async def frame_found(update: Update, context: CallbackContext, attributes:dict):
    """Show success message"""
    frame = attributes['frame']
    try:
        response: requests.Response = requests.get(f'{BASE_URL}/video/{VIDEO_NAME}/finish/{frame}')
        response =response.json()
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id,
            text=f'🎉🎉🎉You did it! 🎉 🎉 🎉'
        )
        await context.bot.send_message(chat_id=chat_id,
            text=f'This frame is located in the following timeline: {response}. Good to know Thank you human!. If you wanna help me again feel free to type the /begin command'
        )
    except Exception as error:
        print('error==>',error)
        chat_id = update.effective_chat.id
        await context.bot.send_message( chat_id=chat_id,
            text="Hubo un error!"
        )
    return ConversationHandler.END

def generate_markup(response: dict):
    """Generate buttons for the begin command and the get_next_frame method."""
    # Generate payloads to pass data to the different buttons
    payloadLow = {
        'frame':response['frame'],
        'range': f"{response['low']}-{response['high']}",
        'input': 'low',
    }
    payloadHigh = {
        'frame':response['frame'],
        'range': f"{response['low']}-{response['high']}",
        'input': 'high',
    }
    payloadFound = {
        'frame':response['frame']
    }
    keyboard = [
        [
            InlineKeyboardButton("Not yet! 🧐", callback_data=f"1*{payloadLow}"),
        ],
        [
            InlineKeyboardButton("Found the frame 😎", callback_data=f"2*{payloadFound}"),
        ],
        [
            InlineKeyboardButton('It already launched 😱', callback_data=f"1*{payloadHigh}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_new_frame(update: Update, context: CallbackContext, attributes: dict):
    """Sends a request to the backend server to get a new frame to evaluate."""
    try:
        frame = attributes['frame']
        input = attributes['input']
        range = attributes['range'].split('-')
        low = int(range[0])
        high = int(range[1])
        url = f'{BASE_URL}/video/{VIDEO_NAME}/frame/{frame}/low/{low}/high/{high}/input/{input}'
        response: requests.Response = requests.get(url)
        response =response.json()
        chat_id = update.effective_chat.id
        await context.bot.send_photo(chat_id=chat_id, photo=response['frame_url'])
        
        reply_markup = generate_markup(response=response)
        await context.bot.send_message( chat_id=chat_id,
            text="Was the rocket launched? 👀 Im lost: /help Try again: /begin", reply_markup=reply_markup
        )
    except Exception as error:
        print('error==>',error)
        chat_id = update.effective_chat.id
        await context.bot.send_message( chat_id=chat_id,
            text="Hubo un error!"
        )

async def get_faq_response(update: Update, context: CallbackContext, attributes: dict):
    """Send message with the answer to the question selected in the attributes"""
    question_index = attributes['question']
    faq_element = FAQ[int(question_index)]
    question, response = list(faq_element.items())[0]
    print('response==>',response)
    chat_id = update.effective_chat.id
    await context.bot.send_message( chat_id=chat_id,
        text=response
    )

async def process_payload(update: Update, context: CallbackContext):
    """Get the event of the button press and calls the callback function depending on the code in the payload."""
    query = update.callback_query
    await query.answer()
    data = query.data  # Get the serialized data
    # Deserialize the data back into a dictionary
    string_payload = data[2:]
    attributes = ast.literal_eval(string_payload)

    # Getting the code from the payload to determine the function that will be called
    code = data[:2]
    match code:
        case '1*': # Not yet / Already launched
            return await get_new_frame(update=update, context=context, attributes=attributes)
        case '2*': # Frame found
            return await frame_found(update=update, context=context, attributes=attributes)
        case '3*': # FAQ
            return await get_faq_response(update=update, context=context, attributes=attributes)
        case _: # Code invalid, return error message
            print(f'error ==>{code}')
            chat_id = update.effective_chat.id
            await context.bot.send_message( chat_id=chat_id,
                text="The button event was not processed properly"
            )
async def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")

def main() -> None:
    """Run the bot."""
    # Create the Application and pass the bot's token.
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('begin', begin_command))
    application.add_handler(CommandHandler('help', help_command))

    # Query handler
    application.add_handler(CallbackQueryHandler(process_payload))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
if __name__ == "__main__":
    main()