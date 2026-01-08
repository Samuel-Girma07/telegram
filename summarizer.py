from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
import nltk

# Ensure NLTK data exists
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def summarize_chat(messages_list):
    """
    Input: List of sqlite3 Rows or tuples (username, message_text)
    Output: Formatted String
    """
    # 1. Validation
    if not messages_list:
        return "📭 No messages found to summarize."

    # 2. Logic for Short Chats (Don't use AI, just show the chat)
    # If less than 15 messages, AI summarization is bad. Just list them.
    if len(messages_list) < 15:
        summary = "📝 **Recent Messages (Too few to summarize):**\n\n"
        for row in messages_list:
            # Handle both dictionary-like rows and tuples
            user = row[0] if isinstance(row, tuple) else row['username']
            text = row[1] if isinstance(row, tuple) else row['message_text']
            summary += f"▫️ **{user}:** {text}\n"
        return summary

    # 3. AI Summarization for Long Chats
    full_text = ""
    for row in messages_list:
        user = row[0] if isinstance(row, tuple) else row['username']
        text = row[1] if isinstance(row, tuple) else row['message_text']
        # Format: "John said: Hello world."
        full_text += f"{user} said: {text}. "

    try:
        parser = PlaintextParser.from_string(full_text, Tokenizer("english"))
        summarizer = LuhnSummarizer()
        
        # dynamic number of sentences based on chat length
        num_sentences = 5 if len(messages_list) < 100 else 10
        
        summary_sentences = summarizer(parser.document, num_sentences)
        
        result = "📝 **Conversation Highlights:**\n\n"
        for sentence in summary_sentences:
            # Clean up the output to look like a bullet list
            clean_sent = str(sentence)
            result += f"• {clean_sent}\n"
            
        return result

    except Exception as e:
        return f"⚠️ Summarization failed: {str(e)}"
