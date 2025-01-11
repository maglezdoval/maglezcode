from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Estado del juego
game_state = {
    "players": [],
    "turn": 0,
    "deck": [],
    "discard_pile": [],
}

@app.route("/")
def index():
    return "Skyjo Server is Running"

@socketio.on("connect")
def on_connect():
    print("Nuevo jugador conectado")
    emit("game_state", game_state)

@socketio.on("join_game")
def on_join(data):
    username = data.get("username", "Unknown")
    if username not in [p["name"] for p in game_state["players"]]:
        game_state["players"].append({"name": username, "score": 0, "ready": False})
        emit("game_state", game_state, broadcast=True)
    else:
        emit("error", {"message": f"El nombre '{username}' ya está en uso."})

@socketio.on("ready")
def on_ready(data):
    username = data.get("username", "Unknown")
    for player in game_state["players"]:
        if player["name"] == username:
            player["ready"] = True
    emit("game_state", game_state, broadcast=True)

@socketio.on("action")
def on_action(data):
    print(f"Acción recibida: {data}")
    # Aquí procesas la acción y actualizas el estado del juego
    emit("game_state", game_state, broadcast=True)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Usar puerto proporcionado por Render o 5000 por defecto
    socketio.run(app, host="0.0.0.0", port=port)
