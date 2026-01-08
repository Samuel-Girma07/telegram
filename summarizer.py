from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
import nltk

class Summarizer:
    def __init__(self):
        # Ensure NLTK data exists before initializing
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        self.summarizer = LuhnSummarizer()
    
    def summarize(self, messages_list):
        """
        Optimized for large message volumes (up to 500+ messages)
        """
        if not messages_list or len(messages_list) == 0:
            return "No messages to summarize!"
        
        num_messages = len(messages_list)
        
        # 1. Direct return for very short chats
        if num_messages <= 3:
            result = []
            for msg in messages_list:
                result.append(f"• {msg[0]}: {msg[1]}")
            return "\n".join(result)
        
        # 2. Intelligent Sampling for Big Chats
        if num_messages > 100:
            # Take the first 10% (context)
            chunk_size = max(10, num_messages // 10)
            first_chunk = messages_list[:chunk_size]
            last_chunk = messages_list[-chunk_size:]
            
            # Sample the middle
            middle = messages_list[len(first_chunk):-len(last_chunk)]
            if middle:
                step = max(1, len(middle) // 80) # Aim for ~80 middle messages
                middle_sample = middle[::step]
            else:
                middle_sample = []
            
            messages_to_process = first_chunk + middle_sample + last_chunk
        else:
            messages_to_process = messages_list
        
        # 3. Format text for the algorithm
        formatted_text = []
        for msg in messages_to_process:
            user_name = msg[0]
            message_text = msg[1]
            # Truncate extremely long single messages to avoid skewing summary
            if len(message_text) > 200:
                message_text = message_text[:200]
            formatted_text.append(f"{user_name} said: {message_text}.")
        
        full_text = " ".join(formatted_text)
        
        # Hard limit to prevent memory crashes
        if len(full_text) > 15000:
            full_text = full_text[:15000]
        
        # 4. Determine summary length
        if num_messages < 20:
            num_sentences = 3
        elif num_messages < 100:
            num_sentences = 5
        else:
            num_sentences = 7
        
        try:
            parser = PlaintextParser.from_string(full_text, Tokenizer("english"))
            summary_sentences = self.summarizer(parser.document, num_sentences)
            
            summary_parts = [str(sentence) for sentence in summary_sentences]
            
            if not summary_parts:
                return self._fallback_summary(messages_list)
            
            return " ".join(summary_parts)
        
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            return self._fallback_summary(messages_list)
    
    def _fallback_summary(self, messages_list):
        """Fallback: Just pick the first, middle, and last few messages."""
        if len(messages_list) <= 10:
            selected = messages_list
        else:
            first = messages_list[:3]
            mid = len(messages_list) // 2
            middle = messages_list[mid-1:mid+2]
            last = messages_list[-3:]
            selected = first + middle + last
        
        result = []
        for msg in selected:
            text = msg[1]
            if len(text) > 100: text = text[:100] + "..."
            result.append(f"• {msg[0]}: {text}")
        
        return "\n".join(result)
