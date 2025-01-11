from flask import Flask
from flask_socketio import SocketIO, emit

# Configuración de la app Flask y SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado del juego
game_state = {
    "players": [],        # Lista de jugadores conectados
    "turn": 0,            # Índice del jugador en turno
    "deck": [],           # Mazo de cartas
    "discard_pile": [],   # Pila de descarte
    "game_started": False # Estado del juego
}

# Mazo base de Skyjo
def create_deck():
    deck = [-2] * 5 + [-1] * 10 + [0] * 15
    for value in range(1, 13):
        deck += [value] * 10
    return deck

@app.route("/")
def index():
    return "Skyjo Server is Running"

# Manejo de conexión de clientes
@socketio.on("connect")
def on_connect():
    print("Nuevo jugador conectado")
    emit("game_state", game_state)

# Manejo de desconexión de clientes
@socketio.on("disconnect")
def on_disconnect():
    print("Jugador desconectado")
    # Aquí puedes manejar la desconexión, si lo deseas

# Evento: Unirse al juego
@socketio.on("join_game")
def on_join(data):
    username = data.get("username", "Jugador desconocido")
    if username not in [p["name"] for p in game_state["players"]]:
        game_state["players"].append({"name": username, "score": 0, "ready": False})
        emit("game_state", game_state, broadcast=True)
    else:
        emit("error", {"message": f"El nombre '{username}' ya está en uso."})

# Evento: Indicar que el jugador está listo
@socketio.on("ready")
def on_ready(data):
    username = data.get("username")
    for player in game_state["players"]:
        if player["name"] == username:
            player["ready"] = True
    emit("game_state", game_state, broadcast=True)
    check_all_ready()

# Verificar si todos los jugadores están listos para comenzar
def check_all_ready():
    if all(player["ready"] for player in game_state["players"]) and len(game_state["players"]) > 1:
        start_game()

# Iniciar el juego
def start_game():
    print("Iniciando el juego...")
    game_state["deck"] = create_deck()
    game_state["discard_pile"] = []
    game_state["game_started"] = True
    game_state["turn"] = 0
    emit("game_state", game_state, broadcast=True)

# Evento: Acción realizada por un jugador
@socketio.on("action")
def on_action(data):
    print(f"Acción recibida: {data}")
    action_type = data.get("type")
    username = data.get("player")

    if action_type == "draw_from_deck":
        handle_draw_from_deck(username)
    elif action_type == "draw_from_discard":
        handle_draw_from_discard(username)

    emit("game_state", game_state, broadcast=True)

# Acción: Tomar una carta del mazo
def handle_draw_from_deck(username):
    if game_state["deck"]:
        card = game_state["deck"].pop()
        print(f"{username} tomó una carta del mazo: {card}")
        # Aquí puedes procesar la carta según las reglas del juego

# Acción: Tomar una carta de la pila de descarte
def handle_draw_from_discard(username):
    if game_state["discard_pile"]:
        card = game_state["discard_pile"].pop()
        print(f"{username} tomó una carta del descarte: {card}")
        # Aquí puedes procesar la carta según las reglas del juego

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Usar el puerto proporcionado por Render
    socketio.run(app, host="0.0.0.0", port=port)
