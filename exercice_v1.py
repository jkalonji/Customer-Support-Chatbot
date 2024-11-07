import os
from flask import Flask, render_template, request, jsonify
from FlagEmbedding import FlagReranker
from tenacity import retry, stop_after_attempt, wait_exponential
from flask_caching import Cache
import time
from functools import wraps
from collections import defaultdict
import threading
import multiprocessing
from flask_cors import CORS
import signal
from statistics import mean

class App1:
    def __init__(self):
        self.app = Flask(__name__)
        self.cache = Cache(self.app, config={'CACHE_TYPE': 'flask_caching.backends.SimpleCache'})
        self.access_history = defaultdict(list)
        self.primary_llm = self.ChatbotAPI(model_name='BAAI/bge-reranker-large')
        self.secondary_llm = self.ChatbotAPI(model_name='BAAI/bge-reranker-base')
        self.current_llm = self.primary_llm
        CORS(self.app)

    class ChatbotAPI:
        def __init__(self, model_name, use_fp16=True):
            self.reranker = FlagReranker(model_name, use_fp16=use_fp16)
            self.tag_list = ['complaint', 'refund', 'query', 'inventory', 'satisfaction']

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1.5, min=4, max=10))
        def chatbot_response(self, message):
            scores = []
            for e in self.tag_list:
                score = self.reranker.compute_score([[e, message]], normalize=True)
                scores.append([e, score])

            sorted_data = sorted(scores, key=lambda x: x[1][0])
            winner_tag = sorted_data[-1][0]
            return f"intent: \"{winner_tag}\""

    def log_status(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            response = f(*args, **kwargs)
            status_code = response[1] if isinstance(response, tuple) else 200
            timestamp = time.time()
            
            key = request.path
            self.access_history[key].append({
                'status_code': status_code,
                'timestamp': timestamp
            })
            
            return response
        return wrapper

    def check_user_message(self, message):
        message_is_correct = False
        conditions = (
            'racist' not in message.lower() and  # Vérifie l'absence du mot "racist" (insensible à la casse)
            len(message.strip()) > 0 and  # Vérifie que le message n'est pas vide après suppression des espaces
            not message.strip().isdigit()  # Vérifie que le message ne contient pas que des chiffres
        )
        message_is_correct = conditions
        return message_is_correct

    def count_server_error_rate_in_chat_cache(self):
        #Permet d'obtenir les statistiques des erreurs du backend
        # Récupère les données en cache
        # Compte le nombre de 200 et les erreurs
        # Retourne le taux d'erreur du backend (en pourcentage)

        # Example:
        # chat_cache = {
        #     '/chat': [
        #         {'status_code': 200, 'timestamp': 1673040000},
        #         {'status_code': 404, 'timestamp': 1673040060},
        #         {'status_code': 200, 'timestamp': 1673040090},
        #         {'status_code': 500, 'timestamp': 1673040120}
        #     ]
        # }

        # count_200 = 2
        # count_error = 2

        count_200, count_error = 0, 0
        server_error_list = [404, 403, 410, 500, 503]
        chat_cache = dict(self.access_history.items()).get('/chat', [])

        for access in chat_cache:
            if access['status_code'] == 200:
                count_200 += 1
            elif access['status_code'] in server_error_list:
                count_error += 1

        return 100*(count_error)/(count_200+count_error) if count_200+count_error > 0 else 0

    def background_error_rate_counter(self, interval=3):
        while True:
            error_rate = self.count_server_error_rate_in_chat_cache()
            print(f"||| Server 8080 error rate: {error_rate}% |||")
            time.sleep(interval)



    def start_background_tasks(self):
        error_rate_thread = threading.Thread(target=self.background_error_rate_counter)
        error_rate_thread.daemon = True
        error_rate_thread.start()


    def setup_routes(self):
        @self.app.route('/')
        @self.log_status
        def home():
            return render_template('index.html')

        @self.app.route('/chat', methods=['POST'])
        @self.log_status
        def chat():
            if  request.json =='' or not request.json:
                return jsonify({'error': 'No message provided'}), 400

            user_message = request.json['message']
            
            if not self.check_user_message(user_message):
                return jsonify({'error': 'Message check failed'}), 403
            
            if self.count_server_error_rate_in_chat_cache() > 50.0:
                return jsonify({'error': 'Server error rate limit exceeded'}), 404  #Temporary redirect

            try:
                bot_response = self.current_llm.chatbot_response(user_message)
            except Exception as e:
                print(f"Current LLM failed: {str(e)}")
                return jsonify({'error': 'LLM failed'}), 500

            return jsonify({'response': bot_response})

        @self.app.route('/consulter-status-cache')
        def consulter_status_cache():
            formatted_history = {}
            for path, accesses in self.access_history.items():
                formatted_history[path] = [
                    {
                        'status_code': access['status_code'],
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(access['timestamp']))
                    }
                    for access in accesses
                ]
            return jsonify(formatted_history)
        
        @self.app.route('/add-success-entries')
        @self.log_status
        def add_success_entries():
            current_time = time.time()
            
            # Ajouter 10 entrées de succès dans le cache
            for _ in range(10):
                self.access_history['/chat'].append({
                    'status_code': 200,
                    'timestamp': current_time
                })
                current_time += 0.01  # Ajouter un petit décalage entre chaque entrée
            
            return jsonify({
                "message": "10 entrées de succès ajoutées au cache",
                "total_entries": len(self.access_history['/chat'])
            }), 200

        @self.app.route('/add-error-entries')
        @self.log_status
        def add_error_entries():
            current_time = time.time()
            
            # Ajouter 10 entrées d'erreur dans le cache
            for _ in range(10):
                self.access_history['/chat'].append({
                    'status_code': 403,
                    'timestamp': current_time
                })
                current_time += 0.01  # Ajouter un petit décalage entre chaque entrée
            
            return jsonify({
                "message": "10 entrées d'erreur ajoutées au cache",
                "total_entries": len(self.access_history['/chat'])
            }), 403

        @self.app.route('/stop')
        def stop():
            os.kill(os.getpid(), signal.SIGINT)
            return "L'application s'arrête..."
                    
        

    def run(self):
        self.setup_routes()
        self.start_background_tasks()
        self.app.run(host='0.0.0.0', port=8080)
        #self.app.run(host='0.0.0.0', port=8080, debug=True)

# On crée une 2e classe App, qui correspond à l'appli de backup

class App2:
    def __init__(self):
        self.app = Flask(__name__)
        self.cache = Cache(self.app, config={'CACHE_TYPE': 'flask_caching.backends.SimpleCache'})
        self.access_history = defaultdict(list)
        self.primary_llm = self.ChatbotAPI(model_name='BAAI/bge-reranker-large')
        self.secondary_llm = self.ChatbotAPI(model_name='BAAI/bge-reranker-base')
        self.current_llm = self.primary_llm
        CORS(self.app)

    class ChatbotAPI:
        def __init__(self, model_name, use_fp16=True):
            self.reranker = FlagReranker(model_name, use_fp16=use_fp16)
            self.tag_list = ['complaint', 'refund', 'query', 'inventory', 'satisfaction']

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1.5, min=4, max=10))
        def chatbot_response(self, message):
            scores = []
            for e in self.tag_list:
                score = self.reranker.compute_score([[e, message]], normalize=True)
                scores.append([e, score])

            sorted_data = sorted(scores, key=lambda x: x[1][0])
            winner_tag = sorted_data[-1][0]
            return f"Intent of the message : \"{winner_tag}\""

    def log_status(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            response = f(*args, **kwargs)
            status_code = response[1] if isinstance(response, tuple) else 200
            timestamp = time.time()
            
            key = request.path
            self.access_history[key].append({
                'status_code': status_code,
                'timestamp': timestamp
            })
            
            return response
        return wrapper

    def check_user_message(self, message):
        message_is_correct = False
        conditions = (
            'racist' not in message.lower() and  # Vérifie l'absence du mot "racist" (insensible à la casse)
            len(message.strip()) > 0 and  # Vérifie que le message n'est pas vide après suppression des espaces
            not message.strip().isdigit()  # Vérifie que le message ne contient pas que des chiffres
        )
        message_is_correct = conditions
        return message_is_correct

    def count_server_error_rate_in_chat_cache(self):
        #Permet d'obtenir les statistiques des erreurs du backend
        # Récupère les données en cache
        # Compte le nombre de 200 et les erreurs
        # Retourne le taux d'erreur du backend (en pourcentage)

        # count_200 = 2
        # count_error = 2

        count_200, count_error = 0, 0
        server_error_list = [404, 403, 410, 500, 503]
        chat_cache = dict(self.access_history.items()).get('/chat', [])

        for access in chat_cache:
            if access['status_code'] == 200:
                count_200 += 1
            elif access['status_code'] in server_error_list:
                count_error += 1

        return 100*(count_error)/(count_200+count_error) if count_200+count_error > 0 else 0

    def background_error_rate_counter(self, interval=3):
        while True:
            error_rate = self.count_server_error_rate_in_chat_cache()
            print(f"||| Server 8090 error rate: {error_rate}% |||")
            time.sleep(interval)

    def start_background_tasks(self):
        error_rate_thread = threading.Thread(target=self.background_error_rate_counter)
        error_rate_thread.daemon = True
        error_rate_thread.start()


    def setup_routes(self):
        @self.app.route('/')
        @self.log_status
        def home():
            return render_template('index.html')

        @self.app.route('/chat', methods=['POST'])
        @self.log_status
        def chat():
            if  request.json =='' or not request.json:
                return jsonify({'error': 'No message provided'}), 400

            user_message = request.json['message']
            
            if not self.check_user_message(user_message):
                return jsonify({'error': 'Message check failed'}), 403
            
            if self.count_server_error_rate_in_chat_cache() > 50.0:
                return jsonify({'error': 'Server error rate limit exceeded'}), 404  #Temporary redirect

            try:
                bot_response = self.current_llm.chatbot_response(user_message)
            except Exception as e:
                print(f"Current LLM failed: {str(e)}")
                return jsonify({'error': 'LLM failed'}), 500

            return jsonify({'response': bot_response})

        @self.app.route('/consulter-status-cache')
        def consulter_status_cache():
            formatted_history = {}
            for path, accesses in self.access_history.items():
                formatted_history[path] = [
                    {
                        'status_code': access['status_code'],
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(access['timestamp']))
                    }
                    for access in accesses
                ]
            return jsonify(formatted_history)
        
        @self.app.route('/add-success-entries')
        @self.log_status
        def add_success_entries():
            current_time = time.time()
            
            # Ajouter 10 entrées de succès dans le cache
            for _ in range(10):
                self.access_history['/chat'].append({
                    'status_code': 200,
                    'timestamp': current_time
                })
                current_time += 0.01  # Ajouter un petit décalage entre chaque entrée
            
            return jsonify({
                "message": "10 entrées de succès ajoutées au cache",
                "total_entries": len(self.access_history['/chat'])
            }), 200
        
        
        
        @self.app.route('/add-error-entries')
        @self.log_status
        def add_error_entries():
            current_time = time.time()
            
            # Ajouter 10 entrées d'erreur dans le cache
            for _ in range(10):
                self.access_history['/chat'].append({
                    'status_code': 403,
                    'timestamp': current_time
                })
                current_time += 0.01  # Ajouter un petit décalage entre chaque entrée
            
            return jsonify({
                "message": "10 entrées d'erreur ajoutées au cache",
                "total_entries": len(self.access_history['/chat'])
            }), 403
    
        @self.app.route('/stop')
        def stop():
            os.kill(os.getpid(), signal.SIGINT)
            return "L'application s'arrête..."
        
    def run(self):
        self.setup_routes()
        self.start_background_tasks()
        self.app.run(host='0.0.0.0', port=8090)
        #self.app.run(host='0.0.0.0', port=8080, debug=True)

def run_app1():
    app1 = App1()
    app1.run()

def run_app2():
    app2 = App2()
    app2.run()



if __name__ == '__main__':
    # Création des processus pour chaque application
    process1 = multiprocessing.Process(target=run_app1)
    process2 = multiprocessing.Process(target=run_app2)
    
    # Démarrage des processus
    process1.start()
    process2.start()
    
    # Attente de la fin des processus
    process1.join()
    process2.join()
