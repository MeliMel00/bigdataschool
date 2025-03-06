<template>
  <div class="container">
    <h1>Transcription Audio</h1>

    <div class="upload-section">
      <!-- File selection button -->
      <label for="file-upload" class="custom-file-upload">
        📂 Choisir un fichier audio
      </label>
      <input
        type="file"
        id="file-upload"
        @change="(e) => file = e.target.files[0]"
        accept="audio/*"
        class="file-input"
      />

      <!-- Display selected filename -->
      <p v-if="file" class="file-name">Fichier sélectionné: {{ file.name }}</p>
    
      <!-- Transcription button -->
      <button 
        @click="uploadFile" 
        :disabled="isUploading || !file" 
        class="action-button transcribe-button"
      >
        Transcrire
      </button>
    </div>

    <!-- Loading spinner during upload and transcription -->
    <div v-if="isUploading" class="spinner-container">
      <div class="spinner"></div>
      <p>En cours de téléchargement et de transcription...</p>
    </div>

    <!-- Transcription results -->
    <div v-if="transcription" class="result-section">
      <div class="result-card">
        <h2>Transcription :</h2>
        <p class="result-text">{{ transcription }}</p>
        <div class="action-bar">
          <a :href="downloadUrl" download="transcription.txt" class="download-link">
            📥 Télécharger la transcription
          </a>
          
          <!-- Translation button - only appears after transcription -->
          <button 
            @click="translateText" 
            :disabled="isTranslating" 
            class="action-button translate-button"
          >
            {{ isTranslating ? 'Traduction en cours...' : 'Traduire' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Translation results -->
    <div v-if="translation" class="result-section">
      <div class="result-card translation-card">
        <h2>Traduction :</h2>
        <p class="result-text">{{ translation }}</p>
        <a 
          :href="translationDownloadUrl" 
          download="traduction.txt" 
          class="download-link"
        >
          📥 Télécharger la traduction
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const file = ref(null);
const transcription = ref('');
const downloadUrl = ref('');
const translationDownloadUrl = ref('');
const isUploading = ref(false);
const isTranslating = ref(false);
const translation = ref('');

// Function to upload and transcribe file
const uploadFile = async () => {
  if (!file.value) {
    alert("Veuillez sélectionner un fichier audio.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file.value);

  try {
    isUploading.value = true;

    const response = await fetch("http://127.0.0.1:5000/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    
    if (data.error) {
      alert(`Erreur: ${data.error}`);
      return;
    }
    
    transcription.value = data.transcription;

    // Create download link for transcription
    const blob = new Blob([transcription.value], { type: "text/plain" });
    downloadUrl.value = URL.createObjectURL(blob);
  } catch (error) {
    console.error("Erreur :", error);
    alert("Une erreur est survenue lors de la transcription.");
  } finally {
    isUploading.value = false;
  }
};

// Function to translate text
const translateText = async () => {
  if (!transcription.value) {
    alert("Aucune transcription à traduire.");
    return;
  }
  
  try {
    isTranslating.value = true;
    
    const response = await fetch("http://127.0.0.1:5000/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: transcription.value })
    });
    
    const data = await response.json();
    
    if (data.error) {
      alert(`Erreur: ${data.error}`);
      return;
    }
    
    translation.value = data.translation;
    
    // Create download link for translation
    const blob = new Blob([translation.value], { type: "text/plain" });
    translationDownloadUrl.value = URL.createObjectURL(blob);
  } catch (error) {
    console.error("Erreur lors de la traduction :", error);
    alert("Une erreur est survenue lors de la traduction.");
  } finally {
    isTranslating.value = false;
  }
};
</script>

<style>
/* Main container */
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #333;
}

h1 {
  color: #2c3e50;
  text-align: center;
  margin-bottom: 2rem;
  font-weight: 600;
}

h2 {
  color: #42b983;
  font-weight: 500;
  margin-top: 0;
}

/* Upload section */
.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: #f8f9fa;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

/* Custom file upload button */
.custom-file-upload {
  background-color: #42b983;
  padding: 12px 24px;
  color: white;
  cursor: pointer;
  border-radius: 6px;
  font-size: 16px;
  transition: background-color 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.custom-file-upload:hover {
  background-color: #3aa876;
}

/* Hide file input */
.file-input {
  display: none;
}

/* Filename display */
.file-name {
  margin: 1rem 0;
  color: #555;
  font-size: 0.9rem;
}

/* Action buttons */
.action-button {
  padding: 12px 24px;
  background: #42b983;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 6px;
  font-size: 16px;
  transition: background-color 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-button:hover {
  background-color: #3aa876;
}

.action-button:disabled {
  background-color: #c4c4c4;
  cursor: not-allowed;
  box-shadow: none;
}

.transcribe-button {
  width: 50%;
  max-width: 200px;
  margin-top: 1.5rem;
}

.translate-button {
  margin-left: 1rem;
}

/* Spinner */
.spinner-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  margin: 2rem 0;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b983;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Result sections */
.result-section {
  margin: 2rem 0;
}

.result-card {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.translation-card {
  background-color: #f0f7f4;
}

.result-text {
  white-space: pre-wrap;
  line-height: 1.6;
  background-color: white;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #42b983;
}

/* Action bar */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
}

/* Download links */
.download-link {
  display: inline-block;
  text-decoration: none;
  color: #42b983;
  font-weight: 500;
  transition: color 0.3s;
}

.download-link:hover {
  color: #358d5e;
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .container {
    padding: 1rem;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 1rem;
  }
  
  .translate-button {
    margin-left: 0;
    width: 100%;
  }
}
</style>