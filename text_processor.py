"""
Advanced Text Processing System
Smart text formatting, correction, and enhancement
"""

import re
import json
import os
from datetime import datetime
import requests

class TextProcessor:
    def __init__(self):
        self.settings_file = "text_processing_settings.json"
        self.custom_vocabulary = {}
        self.abbreviations = {}
        self.load_settings()
        self.load_vocabularies()
        
    def load_settings(self):
        """Load text processing settings"""
        default_settings = {
            "smart_punctuation": True,
            "auto_capitalize": True,
            "number_formatting": True,
            "date_time_formatting": True,
            "custom_replacements": True,
            "grammar_correction": False,
            "spell_check": False
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings = {**default_settings, **json.load(f)}
            except:
                self.settings = default_settings
        else:
            self.settings = default_settings
    
    def load_vocabularies(self):
        """Load custom vocabularies and abbreviations"""
        # Common abbreviations and their expansions
        self.abbreviations = {
            "etc": "et cetera",
            "vs": "versus",
            "eg": "for example",
            "ie": "that is",
            "btw": "by the way",
            "fyi": "for your information",
            "asap": "as soon as possible",
            "api": "A P I",
            "url": "U R L",
            "html": "H T M L",
            "css": "C S S",
            "js": "JavaScript",
            "ai": "A I",
            "ml": "machine learning",
            "ui": "user interface",
            "ux": "user experience"
        }
        
        # Technical terms and proper nouns
        self.custom_vocabulary = {
            "github": "GitHub",
            "javascript": "JavaScript",
            "python": "Python",
            "microsoft": "Microsoft",
            "google": "Google",
            "amazon": "Amazon",
            "facebook": "Facebook",
            "netflix": "Netflix",
            "youtube": "YouTube",
            "linkedin": "LinkedIn",
            "stackoverflow": "Stack Overflow",
            "realtime stt": "RealtimeSTT",
            "openai": "OpenAI",
            "chatgpt": "ChatGPT"
        }
        
        # Load custom vocabularies from file if exists
        try:
            if os.path.exists("custom_vocabulary.json"):
                with open("custom_vocabulary.json", 'r') as f:
                    custom_vocab = json.load(f)
                    self.custom_vocabulary.update(custom_vocab)
        except:
            pass
    
    def process_text(self, text):
        """Apply all text processing enhancements"""
        if not text or not text.strip():
            return text
            
        processed = text
        
        # Apply custom vocabulary replacements
        if self.settings["custom_replacements"]:
            processed = self.apply_custom_vocabulary(processed)
        
        # Format numbers
        if self.settings["number_formatting"]:
            processed = self.format_numbers(processed)
        
        # Format dates and times
        if self.settings["date_time_formatting"]:
            processed = self.format_dates_times(processed)
        
        # Apply smart punctuation
        if self.settings["smart_punctuation"]:
            processed = self.apply_smart_punctuation(processed)
        
        # Apply capitalization
        if self.settings["auto_capitalize"]:
            processed = self.apply_smart_capitalization(processed)
        
        return processed.strip()
    
    def apply_custom_vocabulary(self, text):
        """Replace words with custom vocabulary"""
        words = text.split()
        processed_words = []
        
        for word in words:
            # Remove punctuation for matching
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            
            # Check custom vocabulary
            if clean_word in self.custom_vocabulary:
                # Preserve original punctuation
                punctuation = re.findall(r'[^\w\s]', word)
                replacement = self.custom_vocabulary[clean_word]
                if punctuation:
                    replacement += ''.join(punctuation)
                processed_words.append(replacement)
            # Check abbreviations
            elif clean_word in self.abbreviations:
                punctuation = re.findall(r'[^\w\s]', word)
                replacement = self.abbreviations[clean_word]
                if punctuation:
                    replacement += ''.join(punctuation)
                processed_words.append(replacement)
            else:
                processed_words.append(word)
        
        return ' '.join(processed_words)
    
    def format_numbers(self, text):
        """Format spoken numbers intelligently"""
        # Convert written numbers to digits
        number_words = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
            'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
            'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
            'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
            'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '1000'
        }
        
        for word, digit in number_words.items():
            text = re.sub(r'\b' + word + r'\b', digit, text, flags=re.IGNORECASE)
        
        # Format phone numbers
        text = re.sub(r'\b(\d{3})\s*(\d{3})\s*(\d{4})\b', r'(\1) \2-\3', text)
        
        # Format percentages
        text = re.sub(r'\b(\d+)\s*percent\b', r'\1%', text, flags=re.IGNORECASE)
        
        return text
    
    def format_dates_times(self, text):
        """Format dates and times"""
        # Current date/time insertions
        now = datetime.now()
        
        text = re.sub(r'\btoday\'?s?\s+date\b', now.strftime('%B %d, %Y'), text, flags=re.IGNORECASE)
        text = re.sub(r'\bcurrent\s+time\b', now.strftime('%I:%M %p'), text, flags=re.IGNORECASE)
        text = re.sub(r'\btoday\b', now.strftime('%B %d, %Y'), text, flags=re.IGNORECASE)
        
        # Format common date patterns
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', r'\1/\2/\3', text)
        text = re.sub(r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b', r'\1/\2/\3', text)
        
        return text
    
    def apply_smart_punctuation(self, text):
        """Apply intelligent punctuation"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Add periods to sentences that don't end with punctuation
        sentences = re.split(r'[.!?]+', text)
        processed_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Check if it's a question
                if any(word in sentence.lower() for word in ['what', 'where', 'when', 'why', 'how', 'who', 'which', 'is', 'are', 'can', 'could', 'would', 'should']):
                    if sentence.lower().startswith(('what', 'where', 'when', 'why', 'how', 'who', 'which')):
                        sentence += '?'
                    elif any(sentence.lower().startswith(word) for word in ['is', 'are', 'can', 'could', 'would', 'should']):
                        sentence += '?'
                    else:
                        sentence += '.'
                # Check if it's an exclamation
                elif any(word in sentence.lower() for word in ['wow', 'amazing', 'great', 'excellent', 'fantastic', 'awesome']):
                    sentence += '!'
                else:
                    sentence += '.'
                
                processed_sentences.append(sentence)
        
        return ' '.join(processed_sentences)
    
    def apply_smart_capitalization(self, text):
        """Apply intelligent capitalization"""
        # Capitalize first letter
        if text:
            text = text[0].upper() + text[1:]
        
        # Capitalize after sentence endings
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        # Capitalize proper nouns and acronyms
        proper_nouns = ['I', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
                       'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                       'September', 'October', 'November', 'December']
        
        for noun in proper_nouns:
            text = re.sub(r'\b' + noun.lower() + r'\b', noun, text, flags=re.IGNORECASE)
        
        return text
    
    def add_custom_word(self, spoken_form, written_form):
        """Add a custom word to vocabulary"""
        self.custom_vocabulary[spoken_form.lower()] = written_form
        self.save_custom_vocabulary()
    
    def save_custom_vocabulary(self):
        """Save custom vocabulary to file"""
        try:
            with open("custom_vocabulary.json", 'w') as f:
                json.dump(self.custom_vocabulary, f, indent=2)
        except Exception as e:
            print(f"Error saving custom vocabulary: {e}")
    
    def get_text_statistics(self, text):
        """Get statistics about the text"""
        if not text:
            return {}
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'average_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'reading_time_minutes': len(words) / 200  # Average reading speed
        }