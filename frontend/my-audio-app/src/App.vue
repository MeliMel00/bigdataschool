<template>
  <div class="container">
    <h1>Transcription Audio</h1>
    <input type="file" @change="(e) => file = e.target.files[0]" accept="audio/*" />
    <button @click="uploadFile" :disabled="isUploading">Transcrire</button>

    <!-- Afficher un spinner pendant le téléchargement et la transcription -->
    <div v-if="isUploading" class="spinner-container">
      <div class="spinner"></div>
      <p>En cours de téléchargement et de transcription...</p>
    </div>

    <!-- Affichage de la transcription -->
    <div v-if="transcription">
      <h2>Transcription :</h2>
      <p>{{ transcription }}</p>
      <a :href="downloadUrl" download="transcription.txt">📥 Télécharger la transcription</a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const file = ref(null);
const transcription = ref('');
const downloadUrl = ref('');
const isUploading = ref(false);
const uploadProgress = ref(0);

// Fonction pour simuler la progression de la barre
const simulateUploadProgress = () => {
  let progress = 0;
  const interval = setInterval(() => {
    if (progress < 75) {
      progress += 1; // Augmenter la progression
      uploadProgress.value = progress;
    } else {
      clearInterval(interval); // Stopper la progression une fois 75%
    }
  }, 56); // 66ms pour faire 75% en 5 secondes
};

// Fonction pour télécharger et transcrire le fichier
const uploadFile = async () => {
  if (!file.value) {
    alert("Sélectionnez un fichier audio.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file.value);

  try {
    isUploading.value = true;
    simulateUploadProgress(); // Commencer à simuler la progression

    const response = await fetch("http://127.0.0.1:5000/upload", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    transcription.value = data.transcription;

    // Créer un lien de téléchargement pour la transcription
    const blob = new Blob([transcription.value], { type: "text/plain" });
    downloadUrl.value = URL.createObjectURL(blob);
  } catch (error) {
    console.error("Erreur :", error);
  } finally {
    isUploading.value = false;
  }
};
</script>

<style>
.container {
  text-align: center;
  margin-top: 50px;
}

button {
  margin-top: 10px;
  padding: 10px;
  background: #42b983;
  color: white;
  border: none;
  cursor: pointer;
}

/* Spinner */
.spinner-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  margin-top: 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #42b983;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
