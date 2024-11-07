import os
from flask import Flask, render_template, request, jsonify
from FlagEmbedding import FlagReranker
from tenacity import retry, stop_after_attempt, wait_exponential
from flask_caching import Cache
import time
from functools import wraps
from collections import defaultdict
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Configuration du cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Dictionnaire pour stocker l'historique des accès
access_history = defaultdict(list)

class ChatbotAPI:
    def __init__(self, model_name, use_fp16=True):
        self.reranker = FlagReranker(model_name, use_fp16=use_fp16)
        self.tag_list = ['complaint', 'refund', 'query', 'inventory', 'satisfaction', 'irrelevant']

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1.5, min=4, max=10))
    def chatbot_response(self, message):
        scores = []
        for e in self.tag_list:
            score = self.reranker.compute_score([[e, message]], normalize=True)
            scores.append([e, score])

        sorted_data = sorted(scores, key=lambda x: x[1][0])
        winner_tag = sorted_data[-1][0]
        return f"Intent of the message : \"{winner_tag}\""


# Création de deux instances de l'API
primary_api = ChatbotAPI(model_name='BAAI/bge-reranker-large')
secondary_api = ChatbotAPI(model_name='BAAI/bge-reranker-base')

# =================== Définition des fonctions et routes =================

# Décorateur pour enregistrer le code de statut et le timestamp
def log_status(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        response = f(*args, **kwargs)
        status_code = response[1] if isinstance(response, tuple) else 200
        timestamp = time.time()
        
        # Stocker dans l'historique
        key = request.path
        access_history[key].append({
            'status_code': status_code,
            'timestamp': timestamp
        })
        
        return response
    return wrapper

def check_user_message(message):
    return 'race' not in message

def count_server_error_rate_in_cache():
    # Récupérer les données du cache
    cache_data = access_history

    # Initialiser le compteur
    count_200, count_error = 0
    server_error_list = [404, 410, 500, 503]
    # 404 = Not Found | 410 = Forbidden | 500 = Internal Server Error | 503 = Service Unavailable
    

    # Parcourir toutes les entrées du cache
    for path, accesses in cache_data.items():
        for access in accesses:
            if access['status_code'] == 200:
                count_200 += 1
            elif access['status_code'] in server_error_list :
                count_error += 1

    return (count_200-count_error)/count_200

@app.route('/')
@log_status
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
@log_status
def chat():
    if not request.json or 'message' not in request.json:
        return jsonify({'error': 'No message provided'}), 400

    user_message = request.json['message']
    
    if not check_user_message(user_message):
        return jsonify({'error': 'Message check failed'}), 403

    try:
        # Essayer d'abord avec le LLM primaire
        bot_response = primary_api.chatbot_response(user_message)
    except Exception as e:
        print(f"Primary API failed: {str(e)}")
        try:
            # En cas d'échec, utiliser le LLM secondaire
            bot_response = secondary_api.chatbot_response(user_message)
        except Exception as e:
            print(f"Secondary API failed: {str(e)}")
            return jsonify({'error': 'Both APIs failed'}), 500

    return jsonify({'response': bot_response})

@app.route('/consulter-status-cache')
def consulter_status_cache():
    formatted_history = {}
    for path, accesses in access_history.items():
        formatted_history[path] = [
            {
                'status_code': access['status_code'],
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(access['timestamp']))
            }
            for access in accesses
        ]
    return jsonify(formatted_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
