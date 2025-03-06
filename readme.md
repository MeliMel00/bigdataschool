# Documentation du système de transcription et traduction audio

## Table des matières
1. [Introduction](#introduction)
2. [Architecture du système](#architecture-du-système)
3. [Fonctionnalités](#fonctionnalités)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Utilisation](#utilisation)
7. [API de service](#api-de-service)
8. [Interface utilisateur](#interface-utilisateur)
9. [Dépannage](#dépannage)
10. [Notes techniques](#notes-techniques)

## Introduction

Ce système est conçu pour faciliter la transcription audio et la traduction de l'anglais vers le français. Il comprend un backend Flask qui utilise des modèles d'intelligence artificielle pour la reconnaissance vocale et la traduction, ainsi qu'une interface utilisateur Vue.js pour interagir avec ces services.

Le système permet aux utilisateurs de:
- Télécharger des fichiers audio
- Obtenir une transcription textuelle du contenu audio
- Traduire automatiquement cette transcription de l'anglais vers le français
- Télécharger les résultats de transcription et de traduction

## Architecture du système

Le système est composé de deux parties principales:

1. **Backend (Flask)**: Gère le traitement audio, la transcription et la traduction en utilisant des modèles d'apprentissage automatique.
2. **Frontend (Vue.js)**: Fournit une interface utilisateur intuitive pour interagir avec les services backend.

### Composants du backend:

- **AudioPreprocessor**: Prépare les fichiers audio en normalisant le volume et en effectuant une réduction du bruit.
- **AudioTranscriber**: Utilise le modèle Wav2Vec2 pour transcrire l'audio en texte.
- **Translator**: Utilise des modèles de traduction MarianMT et T5 pour traduire le texte anglais en français.

## Fonctionnalités

### Traitement audio
- Normalisation du volume
- Conversion mono pour les fichiers stéréo
- Réduction du bruit et filtrage des basses fréquences
- Traitement par segments pour les fichiers audio longs

### Transcription
- Reconnaissance vocale de haute précision avec Wav2Vec2
- Post-traitement intelligent du texte
- Correction grammaticale automatique
- Formatage des phrases pour améliorer la lisibilité

### Traduction
- Traduction de haute qualité de l'anglais vers le français
- Modèle principal: MarianMT (Helsinki-NLP/opus-mt-en-fr)
- Modèle de secours: T5-base
- Post-traitement spécifique au français pour améliorer la qualité

## Installation

### Prérequis
- Python 3.8+
- Node.js et npm
- Espace disque suffisant pour les modèles d'IA

### Installation du backend

1. Cloner le dépôt:
```bash
git clone [URL_DU_REPO]
cd [NOM_DU_DOSSIER]/backend
```

2. Créer un environnement virtuel:
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installer les dépendances:
```bash
pip install -r requirements.txt
```

Les dépendances principales incluent:
- Flask et Flask-CORS
- PyTorch
- Transformers
- Librosa
- SoundFile
- Language-tool-python
- Pydub
- NLTK

### Installation du frontend

1. Naviguer vers le dossier frontend:
```bash
cd ../frontend
```

2. Installer les dépendances:
```bash
npm install
```

## Configuration

### Configuration du backend

Le backend utilise les configurations par défaut suivantes:
- Port: 5000
- Dossier de téléchargement: `uploads/` (créé automatiquement)
- Modèle de transcription: `facebook/wav2vec2-large-960h-lv60-self`
- Modèle de traduction principal: `Helsinki-NLP/opus-mt-en-fr`
- Modèle de traduction secondaire: `t5-base`

### Journalisation
Les journaux sont configurés pour être sauvegardés dans `app.log` et également affichés dans la console. Le niveau de journalisation est défini sur DEBUG.

## Utilisation

### Démarrage du backend

1. Activer l'environnement virtuel:
```bash
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

2. Lancer le serveur:
```bash
python app.py
```

Le serveur démarrera sur http://127.0.0.1:5000.

### Démarrage du frontend

1. Dans un terminal séparé, naviguer vers le dossier frontend:
```bash
cd frontend
```

2. Lancer le serveur de développement:
```bash
npm run dev
```

Accéder à l'application via l'URL indiquée dans le terminal (généralement http://localhost:3000).

## API de service

Le backend expose les points de terminaison API suivants:

### 1. `/upload` (POST)
Accepte les fichiers audio pour la transcription.

**Paramètres de la requête:**
- `file`: Fichier audio (multipart/form-data)

**Réponse:**
```json
{
    "transcription": "Texte transcrit de l'audio"
}
```

### 2. `/translate` (POST)
Traduit du texte de l'anglais vers le français.

**Corps de la requête:**
```json
{
    "text": "Text to translate"
}
```

**Réponse:**
```json
{
    "translation": "Texte traduit en français"
}
```

### 3. `/health` (GET)
Vérifie l'état de santé du service.

**Réponse:**
```json
{
    "status": "ok"
}
```

## Interface utilisateur

L'interface utilisateur est conçue pour être intuitive et réactive. Elle comprend les sections suivantes:

### Section de téléchargement
- Bouton pour sélectionner un fichier audio
- Affichage du nom du fichier sélectionné
- Bouton pour lancer la transcription

### Section de résultats de transcription
- Affichage du texte transcrit
- Option pour télécharger la transcription au format texte
- Bouton pour traduire la transcription

### Section de résultats de traduction
- Affichage du texte traduit
- Option pour télécharger la traduction au format texte

## Dépannage

### Problèmes courants et solutions

#### Le serveur backend ne démarre pas
- Vérifier que tous les packages requis sont installés
- Vérifier les erreurs dans les journaux d'application
- S'assurer qu'aucun autre service n'utilise le port 5000

#### Erreurs de transcription
- Vérifier que le format audio est pris en charge
- Essayer de réduire la taille du fichier audio
- Vérifier la qualité de l'enregistrement audio

#### Erreurs de traduction
- Vérifier que le texte à traduire est en anglais
- Vérifier que le texte n'est pas trop long (préférablement moins de 5000 caractères)

#### Problèmes d'interface utilisateur
- Vider le cache du navigateur
- Vérifier la console du navigateur pour les erreurs
- S'assurer que le backend est en cours d'exécution

## Notes techniques

### Modèles d'IA utilisés

#### Transcription
- **Wav2Vec2**: Modèle de reconnaissance vocale entraîné sur 960 heures de données LibriSpeech
- Capacités: Traitement robuste de différents accents et conditions audio

#### Traduction
- **MarianMT**: Modèle spécialisé pour la traduction anglais-français
- **T5**: Modèle de secours plus polyvalent utilisant une architecture encoder-decoder

### Optimisations
- Traitement par segments pour gérer de longs enregistrements audio
- Normalisation audio pour améliorer la qualité de la transcription
- Filtrage du bruit pour améliorer les résultats sur les enregistrements de qualité variable
- Correction grammaticale post-traitement pour améliorer la qualité du texte

### Considérations de performance
- Le premier chargement de modèle peut prendre quelques secondes
- L'utilisation du GPU est automatiquement activée si disponible
- La transcription et la traduction de fichiers longs peuvent prendre un temps significatif

### Limitations connues
- Reconnait principalement l'anglais pour la transcription
- La qualité de transcription diminue avec du bruit de fond excessif
- Ne prend pas en charge la transcription/traduction en temps réel
- Nécessite une connexion Internet active pour les téléchargements et téléversements