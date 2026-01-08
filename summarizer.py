from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
import nltk

class Summarizer:
    def __init__(self):
        self.summarizer = LuhnSummarizer()
    
    def summarize(self, messages_list):
        """
        Optimized for large message volumes (up to 500+ messages)
        messages_list: List of tuples (user_name, message_text, timestamp)
        """
        if not messages_list or len(messages_list) == 0:
            return "No messages to summarize!"
        
        num_messages = len(messages_list)
        
        # For very few messages, just show them
        if num_messages <= 3:
            result = []
            for msg in messages_list:
                result.append(f"• {msg[0]}: {msg[1]}")
            return "\n".join(result)
        
        # For large volumes (100+ messages), sample intelligently
        if num_messages > 100:
            first_chunk = messages_list[:max(10, num_messages // 10)]
            last_chunk = messages_list[-max(10, num_messages // 10):]
            
            middle = messages_list[len(first_chunk):-len(last_chunk)]
            step = max(1, len(middle) // 80)
            middle_sample = middle[::step]
            
            sampled_messages = first_chunk + middle_sample + last_chunk
            messages_to_process = sampled_messages
            
            print(f"📊 Sampled {len(messages_to_process)} from {num_messages} messages for faster processing")
        else:
            messages_to_process = messages_list
        
        # Build conversation flow with speaker names
        formatted_text = []
        for msg in messages_to_process:
            user_name = msg[0]
            message_text = msg[1]
            if len(message_text) > 200:
                message_text = message_text[:200]
            formatted_text.append(f"{user_name} said: {message_text}.")
        
        full_text = " ".join(formatted_text)
        
        # Limit total text length for performance
        if len(full_text) > 10000:
            full_text = full_text[:10000]
        
        # Calculate summary length based on volume
        if num_messages < 20:
            num_sentences = 3
        elif num_messages < 100:
            num_sentences = 5
        else:
            num_sentences = 8
        
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
        """Fallback method: Extract key messages using simple heuristics"""
        if len(messages_list) <= 10:
            selected = messages_list
        else:
            first = messages_list[:3]
            middle_idx = len(messages_list) // 2
            middle = messages_list[middle_idx-1:middle_idx+2]
            last = messages_list[-3:]
            selected = first + middle + last
        
        result = []
        for msg in selected:
            text = msg[1]
            if len(text) > 100:
                text = text[:100] + "..."
            result.append(f"• {msg[0]}: {text}")
        
        return "\n".join(result)
