from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
import logging

logger = logging.getLogger(__name__)

class Summarizer:
    def __init__(self):
        self.summarizer = LuhnSummarizer()
    
    def summarize(self, messages_list):
        """
        Optimized for large message volumes (up to 500+ messages)
        messages_list: List of tuples (user_name, message_text, timestamp, [username])
        """
        if not messages_list or len(messages_list) == 0:
            return "No messages to summarize!"
        
        num_messages = len(messages_list)
        
        # For very few messages, just show them nicely
        if num_messages <= 5:
            return self._format_few_messages(messages_list)
        
        # For large volumes (100+ messages), sample intelligently
        if num_messages > 100:
            messages_to_process = self._sample_messages(messages_list)
            logger.info(f"📊 Sampled {len(messages_to_process)} from {num_messages} messages")
        else:
            messages_to_process = messages_list
        
        # Group consecutive messages by same user
        grouped_text = self._group_by_user(messages_to_process)
        
        # Limit total text length for performance
        if len(grouped_text) > 12000:
            grouped_text = grouped_text[:12000]
        
        # Calculate summary length based on volume
        num_sentences = self._get_sentence_count(num_messages)
        
        try:
            parser = PlaintextParser.from_string(grouped_text, Tokenizer("english"))
            summary_sentences = self.summarizer(parser.document, num_sentences)
            
            summary_parts = [str(sentence) for sentence in summary_sentences]
            
            if not summary_parts:
                return self._fallback_summary(messages_list)
            
            return " ".join(summary_parts)
        
        except Exception as e:
            logger.error(f"❌ Summarization error: {e}")
            return self._fallback_summary(messages_list)
    
    def _format_few_messages(self, messages_list):
        """Format a small number of messages nicely"""
        result = []
        for msg in messages_list:
            name = msg[0]
            text = msg[1]
            username = msg[3] if len(msg) > 3 and msg[3] else None
            
            display_name = f"{name} (@{username})" if username else name
            result.append(f"• *{display_name}*: {text}")
        return "\n".join(result)
    
    def _sample_messages(self, messages_list):
        """Intelligently sample messages for large volumes"""
        num = len(messages_list)
        chunk_size = max(10, num // 10)
        
        first_chunk = messages_list[:chunk_size]
        last_chunk = messages_list[-chunk_size:]
        
        middle = messages_list[chunk_size:-chunk_size]
        step = max(1, len(middle) // 80)
        middle_sample = middle[::step]
        
        return first_chunk + middle_sample + last_chunk
    
    def _group_by_user(self, messages_list):
        """Group messages and format with speaker attribution"""
        formatted_parts = []
        current_user = None
        current_messages = []
        
        for msg in messages_list:
            user_name = msg[0]
            message_text = msg[1][:200]  # Truncate long messages
            
            if user_name == current_user:
                current_messages.append(message_text)
            else:
                if current_user and current_messages:
                    combined = " ".join(current_messages)
                    formatted_parts.append(f"{current_user} said: {combined}.")
                current_user = user_name
                current_messages = [message_text]
        
        # Don't forget the last group
        if current_user and current_messages:
            combined = " ".join(current_messages)
            formatted_parts.append(f"{current_user} said: {combined}.")
        
        return " ".join(formatted_parts)
    
    def _get_sentence_count(self, num_messages):
        """Determine summary length based on message count"""
        if num_messages < 20:
            return 3
        elif num_messages < 50:
            return 4
        elif num_messages < 100:
            return 5
        else:
            return 8
    
    def _fallback_summary(self, messages_list):
        """Fallback method: Extract key messages"""
        num = len(messages_list)
        
        if num <= 10:
            selected = messages_list
        else:
            # Get first 3, middle 3, last 3
            first = messages_list[:3]
            middle_idx = num // 2
            middle = messages_list[middle_idx-1:middle_idx+2]
            last = messages_list[-3:]
            selected = first + middle + last
        
        result = []
        for msg in selected:
            name = msg[0]
            text = msg[1]
            if len(text) > 80:
                text = text[:80] + "..."
            result.append(f"• {name}: {text}")
        
        return "\n".join(result)
