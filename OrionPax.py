#!/home/gabrielwong2/tele_bot/OptimumPride/bot_env/bin/python
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
sheet = client.open("BadAssATron").worksheet("Petrol Consumption")

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
        "Hello! \nI am here to help you monitor car related matters!\n Happy driving!",
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
    km_per_liter = mileage/petrol

    try:
        # Append data to Google Sheets
        sheet.append_row([formatted_date, mileage, petrol, cost,km_per_liter])
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

# Maintenance 
async def maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Open the Maintenance schedule sheet
    try:
        maintenance_sheet = client.open("BadAssATron").worksheet("Maintenance Schedule")
        # Get all values from the sheet
        maintenance_data = maintenance_sheet.get_all_values()
        
        # Assuming the first row is the header
        headers = maintenance_data[0]
        tasks = maintenance_data[1:]

        # Convert tasks to a list of dictionaries for easier handling
        tasks_list = [
            {
                "thing": task[0],
                "when": task[1],
                "status": task[2]
            }
            for task in tasks
        ]

        # Sort tasks by urgency (you can define urgency based on your criteria)
        # Example: if urgency is indicated in the "when" column, assuming it's a date or a priority
        sorted_tasks = sorted(tasks_list, key=lambda x: x['when'])

        # Get the next 5 tasks
        next_tasks = sorted_tasks[:5]

        # Prepare the response message
        if next_tasks:
            response_message = "Next 5 maintenance tasks:\n"
            for i, task in enumerate(next_tasks, start=1):
                response_message += f"{i}. {task['thing']} (Due: {task['when']}, Status: {task['status']})\n"
        else:
            response_message = "No maintenance tasks found."

        await update.message.reply_text(response_message, reply_markup=get_reply_markup())
    
    except Exception as e:
        await update.message.reply_text(f"Error retrieving maintenance tasks: {e}", reply_markup=get_reply_markup())

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
