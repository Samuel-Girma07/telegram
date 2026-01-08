from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import Conflict, NetworkError, TimedOut
from database import MessageDB
from summarizer import Summarizer
from config import TELEGRAM_TOKEN
from keep_alive import keep_alive, set_bot_status
import logging
import signal
import sys
import time
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Suppress noisy httpx logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize
db = MessageDB()
summarizer = Summarizer()

# Track startup time for conflict grace period
STARTUP_TIME = datetime.now()
CONFLICT_GRACE_PERIOD = timedelta(seconds=90)  # Suppress conflict errors for 90 seconds after start

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    signal_name = signal.Signals(signum).name
    logger.info(f"🛑 Received {signal_name}, shutting down...")
    set_bot_status(False)
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

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
    """Save all group messages to database with full user info"""
    if not is_group_chat(update):
        return
    
    if update.message and update.message.text:
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        user_id = user.id
        user_name = user.first_name or "Unknown"
        username = user.username
        message_text = update.message.text
        
        if not message_text.startswith('/'):
            db.add_message(chat_id, user_id, user_name, username, message_text)
            display = f"@{username}" if username else user_name
            logger.info(f"💾 Saved: {display}: {message_text[:30]}...")

async def catchup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate summary of all messages"""
    if not is_group_chat(update):
        await private_chat_response(update, context)
        return
    
    chat_id = update.effective_chat.id
    
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
    
    summary = summarizer.summarize(messages)
    
    participants_set = set()
    for msg in messages:
        name = msg[0]
        username = msg[3] if len(msg) > 3 else None
        if username:
            participants_set.add(f"{name} (@{username})")
        else:
            participants_set.add(name)
    
    participants_text = ", ".join(sorted(participants_set))
    
    response = (
        f"📝 *Catch Up Summary ({time_label})*\n\n"
        f"{summary}\n\n"
        f"👥 _Participants: {participants_text}_\n"
        f"💬 _{len(messages)} messages_"
    )
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def who_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show who's been active today with usernames"""
    if not is_group_chat(update):
        await private_chat_response(update, context)
        return
    
    chat_id = update.effective_chat.id
    participants = db.get_participants(chat_id)
    
    if not participants:
        await update.message.reply_text("No one has sent messages today yet!")
        return
    
    lines = []
    for name, username in participants:
        if username:
            lines.append(f"• {name} (@{username})")
        else:
            lines.append(f"• {name}")
    
    response = "👥 *Active Today:*\n\n" + "\n".join(lines)
    await update.message.reply_text(response, parse_mode='Markdown')

async def person_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get messages from specific person(s) - supports @username format"""
    if not is_group_chat(update):
        await private_chat_response(update, context)
        return
    
    if not context.args:
        await update.message.reply_text(
            "❓ *How to use:*\n\n"
            "`/person @username` - What @username said today\n"
            "`/person John` - What John said today\n"
            "`/person John @sarah` - What both said\n"
            "`/person @user 3` - Last 3 hours\n\n"
            "Use `/who` to see who's active today",
            parse_mode='Markdown'
        )
        return
    
    chat_id = update.effective_chat.id
    args = context.args
    hours = None
    names = []
    
    if args[-1].isdigit():
        hours = int(args[-1])
        raw_names = args[:-1]
        time_label = f"last {hours} hours"
    else:
        raw_names = args
        time_label = "today"
    
    for name in raw_names:
        names.append(name.lstrip('@'))
    
    if not names:
        await update.message.reply_text("Please specify at least one name or @username!")
        return
    
    messages = db.get_messages_by_person(chat_id, names, hours)
    
    if not messages:
        names_text = " & ".join(names)
        await update.message.reply_text(
            f"📭 No messages from {names_text} {time_label}.\n\n"
            f"Tip: Use `/who` to see who's active."
        )
        return
    
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
    """Set up the bot commands menu and clear any existing webhooks"""
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("🔄 Cleared webhooks and pending updates")
    
    commands = [
        BotCommand("start", "Start the bot and see info"),
        BotCommand("catchup", "Get summary of today's chat"),
        BotCommand("person", "Get what someone said (@user or name)"),
        BotCommand("who", "See who's been active today"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Command menu ready")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors - suppress expected conflicts during startup"""
    if isinstance(context.error, Conflict):
        # During deployment, conflicts are expected - only log after grace period
        if datetime.now() - STARTUP_TIME < CONFLICT_GRACE_PERIOD:
            return  # Silently ignore during grace period
        logger.warning("⚠️ Conflict detected - this usually resolves automatically")
    elif isinstance(context.error, (NetworkError, TimedOut)):
        logger.debug("Network hiccup - retrying automatically")
    else:
        logger.error(f"❌ Error: {context.error}")

def main():
    """Main function"""
    logger.info("🤖 Starting Telegram Summarizer Bot...")
    
    # Start keep_alive server
    keep_alive()
    set_bot_status(True)
    
    # Wait for any old instances to fully shut down
    logger.info("⏳ Waiting 5 seconds for old instances to terminate...")
    time.sleep(5)
    
    # Build application
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("catchup", catchup_command))
    application.add_handler(CommandHandler("person", person_command))
    application.add_handler(CommandHandler("who", who_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_message))
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Bot is running!")
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            poll_interval=2.0,  # Slower polling = less chance of conflict
            timeout=30
        )
    except Conflict:
        logger.info("Instance conflict detected, exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        set_bot_status(False)
        db.close()

if __name__ == '__main__':
    main()
