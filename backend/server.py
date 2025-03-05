import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import librosa
import numpy as np
import language_tool_python  # Import de la bibliothèque LanguageTool

app = Flask(__name__)
CORS(app)  # Activation du CORS pour autoriser les requêtes du frontend

# Configuration du dossier temporaire pour les uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialisation de LanguageTool pour l'anglais
tool = language_tool_python.LanguageTool('en-US')

class AudioTranscriber:
    def __init__(self, model_name="facebook/wav2vec2-base-960h"):
        """
        Initialise le modèle de transcription audio.
        """
        # Charger le processeur et le modèle
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
    
    def transcribe_audio(self, audio_path):
        """
        Transcrit un fichier audio en texte.
        """
        # Charger l'audio
        audio, _ = librosa.load(audio_path, sr=16000)
        
        # Prétraitement de l'audio
        input_values = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_values
        
        # Désactiver le calcul de gradient
        with torch.no_grad():
            # Obtenir les logits de prédiction
            logits = self.model(input_values).logits
        
        # Prédire les tokens
        predicted_ids = torch.argmax(logits, dim=-1)
        
        # Convertir en texte
        transcription = self.processor.batch_decode(predicted_ids)[0]
        
        return transcription

# Fonction pour corriger le texte
def correct_text(text):
    matches = tool.check(text)  # Vérifie les erreurs dans le texte
    corrected_text = language_tool_python.utils.correct(text, matches)  # Applique les corrections
    return corrected_text

# Initialiser le transcripteur
transcriber = AudioTranscriber()

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Route pour uploader et transcrire un fichier audio.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
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
        
        return jsonify({"transcription": corrected_transcription})
    
    except Exception as e:
        # Gérer les erreurs de transcription
        return jsonify({"error": str(e)}), 500

def main():
    # Pour le développement local
    app.run(debug=True)

if __name__ == "__main__":
    main()
