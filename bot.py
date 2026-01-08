from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from database import MessageDB
from summarizer import Summarizer
from config import TELEGRAM_TOKEN
from keep_alive import keep_alive
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize
db = MessageDB()
summarizer = Summarizer()

def is_group_chat(update: Update) -> bool:
    """Check if message is from a group chat"""
    return update.effective_chat.type in ['group', 'supergroup']

async def private_chat_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Response for private chats"""
    await update.message.reply_text(
        "🚫 I only work in groups!\n\n"
        "Add me to a group and make me admin to use my features."
    )

async def save_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save all group messages to database"""
    if not is_group_chat(update):
        return
    
    if update.message and update.message.text:
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name or "Unknown"
        message_text = update.message.text
        
        if not message_text.startswith('/'):
            db.add_message(chat_id, user_name, message_text)
            logging.info(f"💾 Saved: {user_name}: {message_text[:30]}...")

async def catchup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate summary of all messages"""
    if not is_group_chat(update):
        await private_chat_response(update, context)
        return
    
    chat_id = update.effective_chat.id
    
    # Parse time parameter
    if context.args and context.args[0].isdigit():
        hours = int(context.args[0])
        messages = db.get_messages_last_hours(chat_id, hours)
        time_label = f"last {hours} hours"
    else:
        messages = db.get_messages_today(chat_id)
        time_label = "today"
    
    if not messages or len(messages) == 0:
        await update.message.reply_text(
            "📭 No messages to catch up on!\n"
            "Messages are saved from when I started running."
        )
        return
    
    # Generate summary
    summary = summarizer.summarize(messages)
    
    # Get participants
    participants = list(set([msg[0] for msg in messages]))
    participants_text = ", ".join(participants)
    
    response = (
        f"📝 *Catch Up Summary ({time_label})*\n\n"
        f"{summary}\n\n"
        f"👥 _Participants: {participants_text}_\n"
        f"💬 _{len(messages)} messages_"
    )
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def who_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show who's been active today"""
    if not is_group_chat(update):
        await private_chat_response(update, context)
        return
    
    chat_id = update.effective_chat.id
    participants = db.get_participants(chat_id)
    
    if not participants:
        await update.message.reply_text("No one has sent messages today yet!")
        return
    
    response = "👥 *Active Today:*\n\n" + "\n".join([f"• {name}" for name in participants])
    await update.message.reply_text(response, parse_mode='Markdown')

async def person_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get messages from specific person(s)"""
    if not is_group_chat(update):
        await private_chat_response(update, context)
        return
    
    if not context.args:
        await update.message.reply_text(
            "❓ *How to use:*\n\n"
            "`/person John` - What John said today\n"
            "`/person John Sarah` - What John & Sarah said\n"
            "`/person John 3` - What John said in last 3 hours\n\n"
            "Use `/who` to see who's active today",
            parse_mode='Markdown'
        )
        return
    
    chat_id = update.effective_chat.id
    
    # Parse arguments: names and optional hours
    args = context.args
    hours = None
    names = []
    
    # Check if last argument is a number (hours)
    if args[-1].isdigit():
        hours = int(args[-1])
        names = args[:-1]
        time_label = f"last {hours} hours"
    else:
        names = args
        time_label = "today"
    
    if not names:
        await update.message.reply_text("Please specify at least one name!")
        return
    
    # Get messages from these people
    messages = db.get_messages_by_person(chat_id, names, hours)
    
    if not messages:
        names_text = " & ".join(names)
        await update.message.reply_text(
            f"📭 No messages from {names_text} {time_label}.\n\n"
            f"Tip: Names are case-sensitive. Use `/who` to see exact names."
        )
        return
    
    # Generate summary
    summary = summarizer.summarize(messages)
    names_text = " & ".join(names)
    
    response = (
        f"📝 *What {names_text} said ({time_label})*\n\n"
        f"{summary}\n\n"
        f"💬 _{len(messages)} messages_"
    )
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    if not is_group_chat(update):
        await update.message.reply_text(
            "🚫 I only work in groups!\n\n"
            "To use me:\n"
            "1️⃣ Add me to your group\n"
            "2️⃣ Make me admin\n"
            "3️⃣ Use /catchup to summarize messages"
        )
        return
    
    await update.message.reply_text(
        "👋 Hi! I'm your chat summarizer.\n\n"
        "✅ I'm now saving all messages!\n\n"
        "Type / to see all available commands.",
        parse_mode='Markdown'
    )

async def post_init(application: Application):
    """Set up the bot commands menu"""
    commands = [
        BotCommand("start", "Start the bot and see info"),
        BotCommand("catchup", "Get summary of today's chat"),
        BotCommand("person", "Get specific person's messages"),
        BotCommand("who", "See who's been active today"),
    ]
    await application.bot.set_my_commands(commands)
    print("✅ Command menu set up successfully!")

def main():
    print("🤖 Starting Telegram Summarizer Bot...")
    print("✅ Using local summarization (instant & unlimited)")
    
    application = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("catchup", catchup_command))
    application.add_handler(CommandHandler("person", person_command))
    application.add_handler(CommandHandler("who", who_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_message))
    
    # Start keep_alive for deployment
    keep_alive()
    
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
