# Customer-Support-Chatbot


Ce projet est une application de chat bot avec une architecture client-serveur, utilisant Vue.js pour le frontend et Flask pour le backend. L'application intègre un système de basculement entre deux serveurs API pour assurer une haute disponibilité.

## Fonctionnalités

- Interface de chat interactive
- Classification d'intention des messages utilisateurs
- Basculement automatique entre deux serveurs API en cas de panne
- Surveillance en temps réel du taux d'erreur du serveur
- Gestion des erreurs et des messages invalides

## Structure du Projet

Le projet est divisé en deux parties principales :

### Backend (Flask)

- Deux serveurs API (App1 et App2) fonctionnant sur des ports différents
- Utilisation de FlagEmbedding pour la classification d'intention
- Système de cache pour le suivi des accès et des erreurs
- Routes pour le chat, la consultation du statut du cache, et l'ajout d'entrées de test

### Frontend (Vue.js)

- Interface utilisateur simple et réactive
- Gestion des requêtes API avec axios
- Logique de basculement entre les serveurs API
- Vérification de la disponibilité du serveur précédent avec backoff exponentiel

## Prérequis

- Python 3.x
- Node.js et npm
- Vue.js CLI

## Installation

1. Clonez le repository :
   
    git clone https://github.com/jkalonji/Customer-Support-Chatbot

    cd Customer-Support-Chatbot


3. Installation du backend :

    cd customer-support-Backend
   
    pip install -r requirements.txt


5. Installation du frontend :
   
    cd customer-support-Frontend

    npm install



## Lancement de l'Application

1. Démarrer le backend :

    cd customer-support-Backend
   
    python CustomerSuppportChatbotBackend.py

Cela lancera deux instances de serveur Flask sur les ports 8080 et 8090.

2. Démarrer le frontend :
   
    cd cd customer-support-Frontend

    npm run serve


4. Accédez à l'application dans votre navigateur à l'adresse indiquée par Vue CLI.

## Utilisation

- Entrez un message dans le champ de texte et appuyez sur "Envoyer" ou la touche Entrée.
- Le bot répondra avec l'intention détectée du message.
- En cas d'erreur du serveur principal, l'application basculera automatiquement vers le serveur secondaire.
- Une erreur 403 peut être déclenchéée en envoyant le mot 'racist'

## Contribution

Les contributions à ce projet sont les bienvenues. Veuillez suivre ces étapes :

1. Forkez le projet
2. Créez votre branche de fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Poussez vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.






