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
