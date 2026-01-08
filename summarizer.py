from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import nltk

# Ensure punkt is ready (Render build script does this, but this is a backup)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def summarize_chat(messages_list):
    """
    Input: list of tuples (username, text)
    Output: String summary
    """
    if not messages_list:
        return "Not enough messages to summarize yet!"

    # 1. Combine messages into one text block
    full_text = ""
    for username, text in messages_list:
        full_text += f"{text}. "

    # 2. Parse text
    try:
        parser = PlaintextParser.from_string(full_text, Tokenizer("english"))
        
        # 3. Summarize (LSA Algorithm)
        summarizer = LsaSummarizer()
        summary_sentences = summarizer(parser.document, 3) # Get top 3 sentences
        
        # 4. Format output
        summary_text = "📝 **Chat Summary:**\n\n"
        for sentence in summary_sentences:
            summary_text += f"- {sentence}\n"
            
        return summary_text
    except Exception as e:
        return f"⚠️ Could not generate summary. Error: {str(e)}"
