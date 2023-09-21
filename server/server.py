from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
client = MongoClient("mongodb://root:examplepassword@localhost:27017")  # Replace with your MongoDB connection string
db = client["disc_golf"]  # Replace with your database name
games_collection = db["games"]

# Endpoint to create a new game
@app.route("/game", methods=["POST"])
def create_game():
    print("Creating a new game")
    # Generate a unique game ID (you can use ObjectId for this)
    game_id = str(ObjectId())
    # Randomly generate the game order (you can implement this logic)
    game_order = ["Player1", "Player2", "Player3"]  # Replace with your logic
    # Store game data in MongoDB
    games_collection.insert_one({"_id": game_id, "order": game_order})
    return jsonify({"game_id": game_id}), 200

# Endpoint to join a game
@app.route("/join", methods=["POST"])
def join_game():
    data = request.json
    game_id = data.get("game_id")
    player_name = data.get("player_name")

    # Check if the game exists
    game = games_collection.find_one({"_id": game_id})
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Check for duplicate player names
    if player_name in game["order"]:
        return jsonify({"error": "Player name already exists"}), 400

    # Add the player to the game
    game["order"].append(player_name)
    games_collection.update_one({"_id": game_id}, {"$set": {"order": game["order"]}})

    return jsonify({"message": "Player joined the game"}), 200

# Endpoint to record round scores
@app.route("/round_score", methods=["POST"])
def record_round_score():
    data = request.json
    game_id = data.get("game_id")
    player_name = data.get("player_name")
    round_number = data.get("round_number")
    score = data.get("score")

    # Check if the game exists
    game = games_collection.find_one({"_id": game_id})
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Check if the player is in the game order
    if player_name not in game["order"]:
        return jsonify({"error": "Player not in the game"}), 400

    # Update the player's score for the specified round
    # You can implement this logic based on your data structure

    return jsonify({"message": "Score recorded"}), 200

# Endpoint to calculate round order
@app.route("/round_order/<game_id>", methods=["GET"])
def calculate_round_order(game_id):
    # Check if the game exists
    game = games_collection.find_one({"_id": game_id})
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Calculate and return the round order
    # You can implement this based on your described logic

    return jsonify({"round_order": game["order"]}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5555)
