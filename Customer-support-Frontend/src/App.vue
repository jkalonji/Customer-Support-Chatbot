<template>
  <div class="chat-container">
    <h1>Dialog chat bot</h1>
    <div class="message-area" ref="messageArea">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.type]">
        {{ msg.text }}
      </div>
    </div>
    <div class="input-area">
      <input 
        v-model="message" 
        type="text" 
        placeholder="What's on your mind ?"
        @keyup.enter="submitMessage"
      >
      <button @click="submitMessage" :disabled="!message">Send</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      message: '',
      messages: [],
      currentApiUrl: 'http://192.168.1.32:8080',
      apiUrls: ['http://192.168.1.32:8080', 'http://192.168.1.32:8090'],
      previousApiUrl: null
    }
  },
  methods: {
    async submitMessage() {
      if (!this.message.trim()) return;

      this.addMessage(this.message, 'user');
      const userMessage = this.message;
      this.message = '';
      
      try {
        const response = await axios.post(`${this.currentApiUrl}/chat`, {
          message: userMessage
        });
        this.addMessage(response.data, 'api');

      } catch (error) {
        console.log(error.code);
        
        if (error.code === 'ERR_NETWORK' || error.response?.status === 404) {
          await this.switchApiAndCheck();
          this.addMessage('Basculement vers une autre API, veuillez réessayer.', 'system');
        } else {
          this.addMessage('Message non valide, recommencez', 'error');
        }
      }
    },

    addMessage(text, type) {
      this.messages.push({ text, type });
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    },

    scrollToBottom() {
      const messageArea = this.$refs.messageArea;
      messageArea.scrollTop = messageArea.scrollHeight;
    },

    async switchApiAndCheck() {
      this.previousApiUrl = this.currentApiUrl;
      this.switchApi();
      
      // Attendre un peu avant de vérifier l'ancienne API
      await new Promise(resolve => setTimeout(resolve, 15000)); // attends 15 sec avant de tester le switch
      
      const checkResults = await this.checkPreviousApi();
      if (checkResults.every(result => result === true)) {
        this.switchApi(); // Revenir à l'API précédente
        this.addMessage('L\'API précédente est de nouveau disponible. Retour à celle-ci.', 'system');
      }
    },
    switchApi() {
      this.currentApiUrl = this.apiUrls[(this.apiUrls.indexOf(this.currentApiUrl) + 1) % this.apiUrls.length];
      console.log(`Switched to API: ${this.currentApiUrl}`);
      this.addMessage(`Connexion à l'API: ${this.currentApiUrl}`, 'system');
    },
    async checkPreviousApi() { // Check avec exponential backoff
      const maxRetries = 6;
      const baseDelay = 1000; // Délai de base en millisecondes
      const results = [];

      for (let i = 0; i < maxRetries; i++) {
        const delay = baseDelay * Math.pow(2, i); // Calcul du délai exponentiel
        
        await new Promise(resolve => setTimeout(resolve, delay));

        try {
          await axios.get(`${this.previousApiUrl}`);
          results.push(true);
          console.log(`Tentative ${i + 1} réussie après ${delay}ms`);
          break;
        } catch (error) {
          results.push(false);
          console.log(`Tentative ${i + 1} échouée après ${delay}ms`);
        }
      }

      console.log(`Résultats des vérifications: ${results.join(', ')}`);
      return results;
    }

  }
}
</script>



<style scoped>
.chat-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  text-align: center;
  color: #333;
}

.message-area {
  height: 400px;
  overflow-y: auto;
  border: 1px solid #ddd;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 5px;
}

.message {
  margin-bottom: 10px;
  padding: 8px 12px;
  border-radius: 18px;
  max-width: 70%;
}

.user {
  background-color: #007bff;
  color: white;
  align-self: flex-end;
  margin-left: auto;
}

.api {
  background-color: #f1f0f0;
  color: black;
}

.error {
  background-color: #ff4d4d;
  color: white;
}

.input-area {
  display: flex;
}

input {
  flex-grow: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px 0 0 4px;
}

button {
  padding: 10px 20px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>
