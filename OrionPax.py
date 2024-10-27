import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# Set up the credentials and Google Sheets API access
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/Users/gab/Desktop/Credentials/cybertron-439513-ee89572f28d9.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheet by name
sheet = client.open("BadAssATron").sheet1

# Conversation states
MILEAGE, PETROL, COST = range(3)

today = datetime.now()
formatted_date = today.strftime("%Y-%m-%d")

# Start the conversation
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Set up reply keyboard with buttons
    keyboard = [
        [KeyboardButton("/add_mileage"), KeyboardButton("/maintenance")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Welcome! Use the buttons below to log your mileage, petrol volume, and cost, or to set a maintenance reminder.",
        reply_markup=reply_markup
    )

async def add_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please insert mileage:")
    return MILEAGE

async def get_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mileage'] = update.message.text
    await update.message.reply_text("Please insert petrol volume:")
    return PETROL

async def get_petrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['petrol'] = update.message.text
    await update.message.reply_text("Please insert cost:")
    return COST

async def get_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cost'] = update.message.text

    # Now we have all the information, so we append it to Google Sheets
    mileage = context.user_data['mileage']
    petrol = context.user_data['petrol']
    cost = context.user_data['cost']

    try:
        # Append data to Google Sheets
        sheet.append_row([formatted_date, mileage, petrol, cost])
        await update.message.reply_text(f"Data logged successfully! Mileage: {mileage}km, Petrol: {petrol} L, Cost: ${cost}")
    except Exception as e:
        await update.message.reply_text(f"Error logging data: {e}")

    return ConversationHandler.END

# Maintenance placeholder function
async def maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Maintenance reminder feature is coming soon!")

# End the conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    # Telegram bot token
    application = Application.builder().token("7943453785:AAESYSPXpCjUKKIxzYYLEzQVLk3pC8dKU9I").build()

    # Create the conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_mileage", add_mileage)],
        states={
            MILEAGE: [MessageHandler(filters.TEXT, get_mileage)],
            PETROL: [MessageHandler(filters.TEXT, get_petrol)],
            COST: [MessageHandler(filters.TEXT, get_cost)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("maintenance", maintenance))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
