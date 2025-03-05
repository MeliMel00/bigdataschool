import os
import logging
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import librosa
import language_tool_python

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)  # Activation du CORS pour autoriser les requêtes du frontend

# Configuration du dossier temporaire pour les uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialisation de LanguageTool pour l'anglais
tool = language_tool_python.LanguageTool('en-US')

# Setup logging
app.logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

# Classe pour la transcription audio
class AudioTranscriber:
    def __init__(self, model_name="facebook/wav2vec2-base-960h"):
        """
        Initialise le modèle de transcription audio.
        """
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
    
    def transcribe_audio(self, audio_path):
        """
        Transcrit un fichier audio en texte.
        """
        audio, _ = librosa.load(audio_path, sr=16000)
        input_values = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_values
        with torch.no_grad():
            logits = self.model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        return transcription

# Fonction pour corriger le texte
def correct_text(text):
    matches = tool.check(text)
    corrected_text = language_tool_python.utils.correct(text, matches)
    return corrected_text

# Initialisation du transcripteur
transcriber = AudioTranscriber()

@app.route('/upload', methods=['POST'])
def upload_file():
    app.logger.debug("Route /upload appelée")

    if 'file' not in request.files:
        app.logger.error("Aucun fichier reçu")
        return jsonify({"error": "Aucun fichier reçu"}), 400

    file = request.files['file']

    if file.filename == '':
        app.logger.error("Aucun fichier sélectionné")
        return jsonify({"error": "Aucun fichier sélectionné"}), 400

    # Sauvegarder le fichier
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        # Transcrire le fichier
        transcription = transcriber.transcribe_audio(filepath)
        
        # Corriger la transcription
        corrected_transcription = correct_text(transcription)

        # Supprimer le fichier après transcription
        os.remove(filepath)
        
        app.logger.debug(f"Transcription : {corrected_transcription}")

        return jsonify({
            "transcription": corrected_transcription
        })

    except Exception as e:
        app.logger.error(f"Erreur lors du traitement du fichier: {str(e)}")
        return jsonify({"error": str(e)}), 500

def main():
    # Pour le développement local
    app.run(debug=True)

if __name__ == "__main__":
    main()
