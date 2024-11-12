# Customer Support Chatbot

This project is a chatbot application with a client-server architecture, using Vue.js for the frontend and Flask for the backend. The application integrates a failover system between two API servers to ensure high availability.

## Features

- Interactive chat interface
- User message intent classification
- Automatic failover between two API servers in case of failure
- Real-time monitoring of server error rate
- Error handling and invalid message management

## Project Structure

The project is divided into two main parts:

### Backend (Flask)

- Two API servers (App1 and App2) running on different ports
- Use of FlagEmbedding for intent classification
- Cache system for tracking accesses and errors
- Routes for chat, cache status consultation, and adding test entries

### Frontend (Vue.js)

- Simple and reactive user interface
- API request management with axios
- Failover logic between API servers
- Previous server availability check with exponential backoff

## Prerequisites

- Python 3.x
- Node.js and npm
- Vue.js CLI

## Installation

1. Clone the repository:
   
    git clone https://github.com/jkalonji/Customer-Support-Chatbot

    cd Customer-Support-Chatbot


2. Backend installation:

    cd customer-support-Backend
   
    pip install -r requirements.txt


3. Frontend installation:
   
    cd customer-support-Frontend

    npm install


## Launching the Application

1. Start the backend:

    cd customer-support-Backend
   
    python CustomerSuppportChatbotBackend.py

This will launch two instances of Flask server on ports 8080 and 8090.

2. Start the frontend:
   
    cd cd customer-support-Frontend

    npm run serve


3. Access the application in your browser at the address indicated by Vue CLI.

## Usage

- Enter a message in the text field and press "Send" or the Enter key.
- The bot will respond with the detected intent of the message.
- In case of main server error, the application will automatically switch to the secondary server.
- A 403 error can be triggered by sending the word 'racist'

## Contribution

Contributions to this project are welcome. Please follow these steps:

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
