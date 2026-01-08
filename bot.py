import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN
import database
import summarizer
from keep_alive import keep_alive

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type == 'private':
        await update.message.reply_text("🚫 I only work in Group chats. Add me to a group!")
        return

    await update.message.reply_text(
        "👋 **Summarizer Bot Ready!**\n\n"
        "I am now recording messages in this group securely.\n\n"
        "**Commands:**\n"
        "/catchup - Summarize the last 100 messages\n"
        "/who - Who is active today?\n"
        "/person [Name] - Count messages for a user"
    )

async def catchup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Feedback to user
    status = await update.message.reply_text("🧠 Reading messages & analyzing...")
    
    # 1. Get messages strictly for THIS chat_id
    messages = database.get_messages(chat_id, limit=100)
    
    # 2. Generate Summary
    text_summary = summarizer.summarize_chat(messages)
    
    # 3. Send result
    await status.edit_text(text_summary, parse_mode='Markdown')

async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users = database.get_active_users(chat_id)
    
    if users:
        msg = "👥 **Active Members (Last 24h):**\n\n" + "\n".join([f"• {u}" for u in users])
        await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("💤 It's been quiet. No active members recently.")

async def person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/person Name`", parse_mode='Markdown')
        return
    
    name = context.args[0]
    chat_id = update.effective_chat.id
    
    count = database.get_person_stats(chat_id, name)
    await update.message.reply_text(f"👤 **{name}** has sent **{count}** messages in this group.")

# --- MESSAGE HANDLER ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saves every message to the DB for the specific group."""
    if update.message and update.message.text:
        chat_id = update.effective_chat.id
        user = update.message.from_user
        username = user.username if user.username else user.first_name
        text = update.message.text
        
        # Save to database
        database.save_message(chat_id, user.id, username, text)

# --- MAIN ---

def main():
    # Initialize DB (Create table if missing)
    database.init_db()
    
    # Start Keep Alive (Web Server)
    keep_alive()
    
    print("🚀 Bot is running...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catchup", catchup))
    app.add_handler(CommandHandler("who", who))
    app.add_handler(CommandHandler("person", person))
    
    # Message Listener (Text only, no commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
