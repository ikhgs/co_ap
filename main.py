import os
from flask import Flask, request, jsonify
import cohere
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Récupérer la clé API de l'environnement
cohere_api_key = os.getenv('COHERE_API_KEY')

# Vérifier si la clé API est bien définie
if not cohere_api_key:
    raise ValueError("La clé API COHERE_API_KEY n'est pas définie dans les variables d'environnement.")

# Initialiser le client Cohere
co = cohere.Client(api_key=cohere_api_key)

# Dictionnaire pour stocker l'historique des conversations par user_id
user_histories = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id')  # Identifiant unique pour chaque utilisateur
    message = data.get('message', '')  # Message de l'utilisateur

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Si l'utilisateur n'a pas d'historique, en créer un nouveau
    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "User", "message": "Bonjour"},
            {"role": "Chatbot", "message": "Bonjour! Comment ça va?"}
        ]

    # Récupérer l'historique de conversation de l'utilisateur
    chat_history = user_histories[user_id]

    # Ajouter le nouveau message de l'utilisateur à l'historique
    chat_history.append({"role": "User", "message": message})

    # Démarrer le flux de chat avec le modèle 'command-r-plus'
    stream = co.chat_stream(
        model='command-r-plus',
        message=message,
        temperature=0.3,
        chat_history=chat_history,
        prompt_truncation='AUTO',
        connectors=[{"id": "web-search"}]
    )

    response_text = ""
    
    # Parcourir les événements générés par le modèle
    for event in stream:
        if event.event_type == "text-generation":
            response_text += event.text

    # Ajouter la réponse du chatbot à l'historique
    chat_history.append({"role": "Chatbot", "message": response_text})

    # Mettre à jour l'historique de l'utilisateur
    user_histories[user_id] = chat_history

    # Retourner uniquement la réponse générée, sans l'historique
    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
  
