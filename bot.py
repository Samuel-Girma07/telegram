import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN
import database
import summarizer
from keep_alive import keep_alive

# 1. Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 2. Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm the Summarizer Bot.\n\n"
        "I need to be an **Admin** in this group to work properly.\n\n"
        "Commands:\n"
        "/catchup - Summarize recent conversation\n"
        "/who - See active members\n"
        "/person [name] - Stats for a specific user"
    )

async def catchup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⏳ Reading messages and summarizing...")
    
    # Get last 100 messages from DB
    messages = database.get_recent_messages(limit=100)
    
    # Generate summary
    summary = summarizer.summarize_chat(messages)
    
    await status_msg.edit_text(summary, parse_mode='Markdown')

async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = database.get_active_members()
    if users:
        await update.message.reply_text(f"👥 **Active (last 24h):**\n" + "\n".join(users))
    else:
        await update.message.reply_text("💤 No one has been active recently.")

async def person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /person Name")
        return
    
    name = context.args[0]
    count = database.get_person_stats(name)
    await update.message.reply_text(f"👤 **{name}** has sent {count} messages.")

# 3. Message Handler (Saves ALL messages)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user = update.message.from_user
        username = user.username if user.username else user.first_name
        text = update.message.text
        group_id = update.message.chat_id
        
        # Save to DB
        database.save_message(user.id, username, text, group_id)

# 4. Main Execution
def main():
    # Initialize DB
    database.init_db()
    
    # Start Web Server for Uptime
    keep_alive()
    
    # Start Bot
    print("🚀 Bot is starting...")
    app = Application.builder().token(TOKEN).build()

    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catchup", catchup))
    app.add_handler(CommandHandler("who", who))
    app.add_handler(CommandHandler("person", person))
    
    # Add Message Handler (Must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
