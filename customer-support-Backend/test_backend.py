import pytest
from flask import json
import time
import signal
from exercice_v4_2classes import App1 

@pytest.fixture
def app():
    app = App1()
    app.setup_routes()
    return app

@pytest.fixture
def client(app):
    return app.app.test_client()

def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200
    # Vérifiez que le contenu de index.html est bien renvoyé
    assert b'<!DOCTYPE html>' in response.data

def test_chat_route_no_message(client):
    response = client.post('/chat', json={})
    assert response.status_code == 400
    assert json.loads(response.data) == {'error': 'No message provided'}

def test_chat_route_invalid_message(client, monkeypatch):
    # Simulez check_user_message pour qu'il retourne False
    monkeypatch.setattr(App1, 'check_user_message', lambda self, msg: False)
    
    response = client.post('/chat', json={'message': 'invalid message'})
    assert response.status_code == 403
    assert json.loads(response.data) == {'error': 'Message check failed'}

def test_chat_route_valid_message(client, monkeypatch):
    # Simulez check_user_message pour qu'il retourne True
    monkeypatch.setattr(App1, 'check_user_message', lambda self, msg: True)
    
    # Simulez chatbot_response
    monkeypatch.setattr(App1.ChatbotAPI, 'chatbot_response', lambda self, msg: "Bot response")
    
    response = client.post('/chat', json={'message': 'Hello'})
    assert response.status_code == 200
    assert json.loads(response.data) == {'response': 'Bot response'}

def test_chat_route_llm_failure(client, monkeypatch):
    # Simulez check_user_message pour qu'il retourne True
    monkeypatch.setattr(App1, 'check_user_message', lambda self, msg: True)
    
    # Simulez chatbot_response pour qu'il lève une exception
    def mock_chatbot_response(self, msg):
        raise Exception("LLM failed")
    monkeypatch.setattr(App1.ChatbotAPI, 'chatbot_response', mock_chatbot_response)
    
    response = client.post('/chat', json={'message': 'Hello'})
    assert response.status_code == 500
    assert json.loads(response.data) == {'error': 'LLM failed'}


def test_consulter_status_cache(client, app):
    # Préparer des données de test
    test_data = {
        '/': [
            {'status_code': 200, 'timestamp': time.time()},
            {'status_code': 404, 'timestamp': time.time()}
        ],
        '/chat': [
            {'status_code': 200, 'timestamp': time.time()},
            {'status_code': 500, 'timestamp': time.time()}
        ]
    }
    app.access_history = test_data

    # Faire la requête
    response = client.get('/consulter-status-cache')

    # Vérifier le code de statut
    assert response.status_code == 200

    # Vérifier le contenu de la réponse
    data = json.loads(response.data)
    assert set(data.keys()) == set(test_data.keys())

    for path in data:
        assert len(data[path]) == len(test_data[path])
        for i, access in enumerate(data[path]):
            assert 'status_code' in access
            assert 'timestamp' in access
            assert access['status_code'] == test_data[path][i]['status_code']
            # Vérifier que le timestamp est une chaîne formatée correctement
            assert time.strptime(access['timestamp'], '%Y-%m-%d %H:%M:%S')

def test_stop_route(client, monkeypatch):
    # Simuler la fonction os.kill pour éviter d'arrêter réellement le processus
    def mock_kill(pid, sig):
        assert pid == 12345  # Un PID fictif
        assert sig == signal.SIGINT

    monkeypatch.setattr('os.kill', mock_kill)
    monkeypatch.setattr('os.getpid', lambda: 12345)

    # Faire la requête
    response = client.get('/stop')

    # Vérifier le code de statut et le contenu
    assert response.status_code == 200
    assert response.data == b"L'application s'arr\xc3\xaate..."  # "L'application s'arrête..." en bytes
