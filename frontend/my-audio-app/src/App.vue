<script setup>
import { ref } from 'vue';

const file = ref(null);
const transcription = ref('');
const downloadUrl = ref('');

const uploadFile = async () => {
  if (!file.value) {
    alert("Sélectionnez un fichier audio.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file.value);

  try {
    const response = await fetch("http://127.0.0.1:5000/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    transcription.value = data.transcription;

    // Créer un lien de téléchargement
    const blob = new Blob([transcription.value], { type: "text/plain" });
    downloadUrl.value = URL.createObjectURL(blob);
  } catch (error) {
    console.error("Erreur :", error);
  }
};
</script>

<template>
  <div class="container">
    <h1>Transcription Audio</h1>
    <input type="file" @change="(e) => file = e.target.files[0]" accept="audio/*" />
    <button @click="uploadFile">Transcrire</button>

    <div v-if="transcription">
      <h2>Transcription :</h2>
      <p>{{ transcription }}</p>
      <a :href="downloadUrl" download="transcription.txt">📥 Télécharger la transcription</a>
    </div>
  </div>
</template>

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
</style>
