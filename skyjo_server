from flask import Flask
from flask_socketio import SocketIO, emit

# Configuración del servidor
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado del juego
game_state = {
    "players": [],
    "turn": 0,
    "deck": [],
    "discard_pile": [],
    "game_started": False,
}

# Ruta básica para comprobar que el servidor está corriendo
@app.route("/")
def index():
    return "Skyjo Server is Running"

# Cuando un cliente se conecta
@socketio.on("connect")
def on_connect():
    print("Nuevo jugador conectado")
    emit("game_state", game_state)

# Cuando un jugador se une al juego
@socketio.on("join_game")
def on_join(data):
    username = data.get("username", "Jugador")
    if not any(player["name"] == username for player in game_state["players"]):
        game_state["players"].append({"name": username, "score": 0, "ready": False})
    print(f"{username} se ha unido al juego")
    emit("game_state", game_state, broadcast=True)

# Cuando un jugador marca que está listo para empezar
@socketio.on("ready")
def on_ready(data):
    username = data.get("username")
    for player in game_state["players"]:
        if player["name"] == username:
            player["ready"] = True
            break
    emit("game_state", game_state, broadcast=True)

# Acción de juego (por ejemplo, robar carta, descartar)
@socketio.on("action")
def on_action(data):
    print(f"Acción recibida: {data}")
    # Aquí procesas las acciones de los jugadores
    # Ejemplo: Actualiza el estado del juego
    emit("game_state", game_state, broadcast=True)

# Desconexión de un cliente
@socketio.on("disconnect")
def on_disconnect():
    print("Un jugador se ha desconectado")

# Ejecuta el servidor
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
