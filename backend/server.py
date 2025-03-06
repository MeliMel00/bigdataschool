import os
import logging
import torch
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import (
    Wav2Vec2ForCTC, 
    Wav2Vec2Processor, 
    MarianMTModel, 
    MarianTokenizer,
    AutoModelForSeq2SeqLM,
    AutoTokenizer
)
import librosa
import soundfile as sf
import language_tool_python
from pydub import AudioSegment
import nltk
from nltk.tokenize import sent_tokenize

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Initialize Flask application
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize LanguageTool for English and French
english_tool = language_tool_python.LanguageTool('en-US')
french_tool = language_tool_python.LanguageTool('fr')

class AudioPreprocessor:
    @staticmethod
    def normalize_audio(audio_path):
        """Normalize audio volume and convert to correct format"""
        try:
            # Load audio using pydub (supports more formats)
            audio = AudioSegment.from_file(audio_path)
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Normalize volume
            normalized_audio = audio.normalize()
            
            # Export to temporary WAV file at 16kHz
            temp_path = f"{audio_path}_normalized.wav"
            normalized_audio.export(temp_path, format="wav", parameters=["-ar", "16000"])
            
            logger.info(f"Audio normalized and saved to {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            return audio_path  # Return original path if processing fails

    @staticmethod
    def remove_noise(audio_data, sr):
        """Simple noise reduction using spectral gating"""
        # Simple high-pass filter to remove low frequency noise
        from scipy import signal
        sos = signal.butter(10, 100, 'hp', fs=sr, output='sos')
        filtered_audio = signal.sosfilt(sos, audio_data)
        return filtered_audio

# Enhanced audio transcription class
class AudioTranscriber:
    def __init__(self, model_name="facebook/wav2vec2-large-960h-lv60-self"):
        logger.info(f"Initializing transcriber with model: {model_name}")
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
        self.model.eval()  # Set model to evaluation mode
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        self.model.to(self.device)
    
    def transcribe_audio(self, audio_path):
        logger.info(f"Starting transcription for: {audio_path}")
        
        # Preprocess audio
        normalized_path = AudioPreprocessor.normalize_audio(audio_path)
        
        # Load audio
        audio, sr = librosa.load(normalized_path, sr=16000)
        
        # Apply noise reduction
        audio = AudioPreprocessor.remove_noise(audio, sr)
        
        # Process long audio in chunks to avoid memory issues
        MAX_DURATION = 30  # seconds
        chunk_size = 16000 * MAX_DURATION  # 30 seconds at 16kHz
        
        all_transcriptions = []
        
        # Process audio in chunks if it's long
        if len(audio) > chunk_size:
            chunks = [audio[i:i + chunk_size] for i in range(0, len(audio), chunk_size)]
            logger.info(f"Processing audio in {len(chunks)} chunks")
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                chunk_transcription = self._process_audio_chunk(chunk)
                all_transcriptions.append(chunk_transcription)
            
            transcription = " ".join(all_transcriptions)
        else:
            transcription = self._process_audio_chunk(audio)
        
        # Clean up temporary file
        if normalized_path != audio_path and os.path.exists(normalized_path):
            os.remove(normalized_path)
        
        # Post-process transcription
        transcription = self._post_process_text(transcription)
        logger.info("Transcription complete")
        
        return transcription
    
    def _process_audio_chunk(self, audio_chunk):
        # Apply padding if chunk is too short
        if len(audio_chunk) < 16000:  # Less than 1 second
            padding = np.zeros(16000 - len(audio_chunk))
            audio_chunk = np.concatenate([audio_chunk, padding])
        
        # Convert to tensor and process
        with torch.no_grad():
            input_values = self.processor(
                audio_chunk, 
                sampling_rate=16000, 
                return_tensors="pt"
            ).input_values.to(self.device)
            
            logits = self.model(input_values).logits
            predicted_ids = torch.argmax(logits, dim=-1)
            
        transcription = self.processor.batch_decode(predicted_ids)[0]
        return transcription
    
    def _post_process_text(self, text):
        # Fix common transcription issues
        text = text.lower()
        
        # Remove repeated words (a common ASR issue)
        words = text.split()
        filtered_words = []
        for i, word in enumerate(words):
            if i == 0 or word != words[i-1]:
                filtered_words.append(word)
        
        text = " ".join(filtered_words)
        
        # Apply grammar correction
        matches = english_tool.check(text)
        text = language_tool_python.utils.correct(text, matches)
        
        # Capitalize sentences
        sentences = sent_tokenize(text)
        text = ' '.join(s.capitalize() for s in sentences)
        
        return text

# Enhanced text translation class
class Translator:
    def __init__(self):
        # For English to French
        en_fr_model_name = "Helsinki-NLP/opus-mt-en-fr"
        logger.info(f"Loading EN->FR model: {en_fr_model_name}")
        self.en_fr_tokenizer = MarianTokenizer.from_pretrained(en_fr_model_name)
        self.en_fr_model = MarianMTModel.from_pretrained(en_fr_model_name)
        
        # For improved English to French (optional fallback model)
        self.t5_model_name = "t5-base"
        logger.info(f"Loading T5 model: {self.t5_model_name}")
        self.t5_tokenizer = AutoTokenizer.from_pretrained(self.t5_model_name)
        self.t5_model = AutoModelForSeq2SeqLM.from_pretrained(self.t5_model_name)
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device for translation: {self.device}")
        self.en_fr_model.to(self.device)
        self.t5_model.to(self.device)
    
    def translate(self, text):
        logger.info("Starting translation")
        
        # Break text into smaller chunks to avoid model limitations
        MAX_LENGTH = 512
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.en_fr_tokenizer.encode(sentence))
            if current_length + sentence_tokens > MAX_LENGTH:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_length += sentence_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        logger.info(f"Translating text in {len(chunks)} chunks")
        
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Translating chunk {i+1}/{len(chunks)}")
            
            # Primary translation using MarianMT
            try:
                translated_chunk = self._translate_with_marian(chunk)
                translated_chunks.append(translated_chunk)
            except Exception as e:
                logger.error(f"Error with primary translation model: {e}")
                # Fallback to T5 if MarianMT fails
                try:
                    translated_chunk = self._translate_with_t5(chunk)
                    translated_chunks.append(translated_chunk)
                except Exception as e2:
                    logger.error(f"Error with fallback translation model: {e2}")
                    # If both models fail, return the original text for this chunk
                    translated_chunks.append(f"[Translation Error: {chunk}]")
        
        # Combine all translated chunks
        translation = ' '.join(translated_chunks)
        
        # Post-process translation
        translation = self._post_process_translation(translation)
        
        logger.info("Translation complete")
        return translation
    
    def _translate_with_marian(self, text):
        """Translate using MarianMT model"""
        with torch.no_grad():
            inputs = self.en_fr_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512).to(self.device)
            translated_ids = self.en_fr_model.generate(**inputs)
            translation = self.en_fr_tokenizer.batch_decode(translated_ids, skip_special_tokens=True)[0]
        return translation
    
    def _translate_with_t5(self, text):
        """Translate using T5 model as fallback"""
        with torch.no_grad():
            inputs = self.t5_tokenizer("translate English to French: " + text, return_tensors="pt", max_length=512, truncation=True).to(self.device)
            outputs = self.t5_model.generate(**inputs)
            translation = self.t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return translation
    
    def _post_process_translation(self, text):
        """Apply post-processing to improve translation quality"""
        # Apply grammar correction for French
        matches = french_tool.check(text)
        text = language_tool_python.utils.correct(text, matches)
        
        # Fix common issues in French translations
        text = text.replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?")
        
        return text

# Initialize models
transcriber = AudioTranscriber()
translator = Translator()

@app.route('/upload', methods=['POST'])
def upload_file():
    logger.info("Received request to /upload")
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({"error": "Aucun fichier reçu"}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("Empty filename submitted")
        return jsonify({"error": "Aucun fichier sélectionné"}), 400
    
    try:
        # Save uploaded file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        logger.info(f"File saved to {filepath}")
        
        # Process the audio file
        transcription = transcriber.transcribe_audio(filepath)
        
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Removed temporary file: {filepath}")
        
        return jsonify({"transcription": transcription})
    
    except Exception as e:
        logger.exception(f"Error during transcription: {e}")
        return jsonify({"error": f"Erreur lors de la transcription: {str(e)}"}), 500

@app.route('/translate', methods=['POST'])
def translate_text():
    logger.info("Received request to /translate")
    if not request.is_json:
        logger.error("Request is not JSON")
        return jsonify({"error": "Le contenu doit être en format JSON"}), 400
    
    data = request.json
    if 'text' not in data:
        logger.error("No text provided in request")
        return jsonify({"error": "Aucun texte fourni"}), 400
    
    try:
        text = data['text']
        translated_text = translator.translate(text)
        return jsonify({"translation": translated_text})
    
    except Exception as e:
        logger.exception(f"Error during translation: {e}")
        return jsonify({"error": f"Erreur lors de la traduction: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "ok"})

def main():
    logger.info("Starting application")
    app.run(debug=True)

if __name__ == "__main__":
    main()