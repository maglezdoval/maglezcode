from flask import Flask
from flask_socketio import SocketIO, emit
import random

# Configuración de la app Flask y SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado del juego
game_state = {
    "players": [],  # Lista de jugadores conectados
    "turn": 0,      # Índice del jugador en turno
    "deck": [],     # Mazo de cartas
    "discard_pile": [], # Pila de descarte
    "game_started": False, # Estado del juego
    "player_hands": {},   # Manos de los jugadores
    "revealed_cards": {}, # Cartas reveladas de cada jugador
    "round_ended": False  # Indica si la ronda ha terminado
}

# Mazo base de Skyjo
def create_deck():
    deck = [-2] * 5 + [-1] * 10 + [0] * 15
    for value in range(1, 13):
        deck += [value] * 10
    random.shuffle(deck)
    return deck

def deal_initial_cards():
    for player in game_state["players"]:
        username = player["name"]
        if username not in game_state["player_hands"]:
            game_state["player_hands"][username] = []
            game_state["revealed_cards"][username] = [False] * 12
            
            # Repartir 12 cartas a cada jugador
            for _ in range(12):
                if game_state["deck"]:
                    card = game_state["deck"].pop()
                    game_state["player_hands"][username].append(card)

@app.route("/")
def index():
    return "Skyjo Server is Running"

@socketio.on("connect")
def on_connect():
    print("Nuevo jugador conectado")
    emit("game_state", game_state)

@socketio.on("disconnect")
def on_disconnect():
    print("Jugador desconectado")
    # Eliminar al jugador del juego
    for player in game_state["players"][:]:
        if player["name"] in game_state["player_hands"]:
            del game_state["player_hands"][player["name"]]
            del game_state["revealed_cards"][player["name"]]
            game_state["players"].remove(player)
    emit("game_state", game_state, broadcast=True)

@socketio.on("join_game")
def on_join(data):
    username = data.get("username", "Jugador desconocido")
    if username not in [p["name"] for p in game_state["players"]]:
        game_state["players"].append({
            "name": username,
            "score": 0,
            "ready": False
        })
        emit("game_state", game_state, broadcast=True)
    else:
        emit("error", {"message": f"El nombre '{username}' ya está en uso."})

@socketio.on("ready")
def on_ready(data):
    username = data.get("username")
    for player in game_state["players"]:
        if player["name"] == username:
            player["ready"] = True
            emit("game_state", game_state, broadcast=True)
            check_all_ready()
            break

def check_all_ready():
    if all(player["ready"] for player in game_state["players"]) and len(game_state["players"]) > 1:
        start_game()

def start_game():
    print("Iniciando el juego...")
    game_state["deck"] = create_deck()
    game_state["discard_pile"] = []
    game_state["game_started"] = True
    game_state["turn"] = 0
    game_state["round_ended"] = False
    
    # Repartir cartas iniciales
    deal_initial_cards()
    
    # Colocar primera carta en la pila de descarte
    if game_state["deck"]:
        game_state["discard_pile"].append(game_state["deck"].pop())
    
    emit("game_state", game_state, broadcast=True)

@socketio.on("reveal_card")
def on_reveal_card(data):
    username = data.get("username")
    card_index = data.get("card_index")
    
    if (username in game_state["revealed_cards"] and 
        0 <= card_index < len(game_state["revealed_cards"][username])):
        game_state["revealed_cards"][username][card_index] = True
        emit("game_state", game_state, broadcast=True)
        check_round_end()

@socketio.on("action")
def on_action(data):
    if not game_state["game_started"] or game_state["round_ended"]:
        return
        
    action_type = data.get("type")
    username = data.get("player")
    
    # Verificar si es el turno del jugador
    current_player = game_state["players"][game_state["turn"]]["name"]
    if username != current_player:
        emit("error", {"message": "No es tu turno"})
        return
        
    if action_type == "draw_from_deck":
        card = handle_draw_from_deck(username)
        emit("card_drawn", {"card": card, "player": username}, broadcast=True)
    elif action_type == "draw_from_discard":
        card = handle_draw_from_discard(username)
        emit("card_drawn", {"card": card, "player": username}, broadcast=True)
    elif action_type == "replace_card":
        handle_replace_card(username, data.get("card_index"), data.get("card"))
    
    # Pasar al siguiente turno
    game_state["turn"] = (game_state["turn"] + 1) % len(game_state["players"])
    emit("game_state", game_state, broadcast=True)

def handle_draw_from_deck(username):
    if game_state["deck"]:
        return game_state["deck"].pop()
    return None

def handle_draw_from_discard(username):
    if game_state["discard_pile"]:
        return game_state["discard_pile"].pop()
    return None

def handle_replace_card(username, card_index, new_card):
    if (username in game_state["player_hands"] and 
        0 <= card_index < len(game_state["player_hands"][username])):
        old_card = game_state["player_hands"][username][card_index]
        game_state["player_hands"][username][card_index] = new_card
        game_state["discard_pile"].append(old_card)
        game_state["revealed_cards"][username][card_index] = True

def check_round_end():
    for username in game_state["revealed_cards"]:
        if all(revealed for revealed in game_state["revealed_cards"][username]):
            game_state["round_ended"] = True
            calculate_scores()
            emit("round_end", game_state, broadcast=True)
            break

def calculate_scores():
    for player in game_state["players"]:
        username = player["name"]
        if username in game_state["player_hands"]:
            score = sum(game_state["player_hands"][username])
            player["score"] += score

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app, host="0.0.0.0", port=port)
