import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import os
from dotenv import load_dotenv
import json

load_dotenv()
json_string = os.getenv("JSON_DATA")
Google_Cloud = json.loads(json_string)

# Set up the credentials and Google Sheets API access
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(Google_Cloud, scope)
client = gspread.authorize(creds)

# Open the Google Sheet by name
sheet = client.open("BadAssATron").sheet1

# Conversation states
MILEAGE, PETROL, COST = range(3)

today = datetime.now()
formatted_date = today.strftime("%Y-%m-%d")

# Set up the reply keyboard with buttons
def get_reply_markup():
    keyboard = [
        [KeyboardButton("/top_up 🚗"), KeyboardButton("/maintenance"), KeyboardButton("/delete_recent_entry")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Start the conversation
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Use the buttons below to log your mileage, petrol volume, cost, or to set a maintenance reminder.",
        reply_markup=get_reply_markup()
    )

async def add_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("How far did you drive with this tank?", reply_markup=get_reply_markup())
    return MILEAGE

async def get_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mileage'] = update.message.text
    await update.message.reply_text("Great! How much petrol did you top up?", reply_markup=get_reply_markup())
    return PETROL

async def get_petrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['petrol'] = update.message.text
    await update.message.reply_text("And that cost?", reply_markup=get_reply_markup())
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
        await update.message.reply_text(f"Thank you! Your data has been uploaded successfully!\n{formatted_date}\nMileage: {mileage} km\nPetrol: {petrol} L\nCost: ${cost}", reply_markup=get_reply_markup())
    except Exception as e:
        await update.message.reply_text(f"Error logging data: {e}", reply_markup=get_reply_markup())

    return ConversationHandler.END

# Function to delete the most recent entry
async def delete_recent_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get the last row number and delete it
        last_row = len(sheet.get_all_values())
        if last_row > 1:  # Ensure there's data to delete (skip header)
            sheet.delete_rows(last_row)
            await update.message.reply_text("The most recent entry has been deleted.", reply_markup=get_reply_markup())
        else:
            await update.message.reply_text("No entries to delete.", reply_markup=get_reply_markup())
    except Exception as e:
        await update.message.reply_text(f"Error deleting entry: {e}", reply_markup=get_reply_markup())

# Maintenance placeholder function
async def maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Maintenance reminder feature is coming soon!", reply_markup=get_reply_markup())

# End the conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.", reply_markup=get_reply_markup())
    return ConversationHandler.END

def main():
    # Telegram bot token
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Create the conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("top_up", add_mileage)],  # Updated entry point
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
    application.add_handler(CommandHandler("delete_recent_entry", delete_recent_entry))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
