# Import the necessary modules
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
import random

app = Flask(__name__)

# Define the MongoDB URI using an environment variable
mongo_uri = os.getenv("MONGO_URI")

# Create a MongoClient using the URI
client = MongoClient(mongo_uri if mongo_uri else "mongodb://localhost:27017/")
db = client["disc_golf"]  # Replace with your database name
games_collection = db["games"]

# Helper function to check if the game has started
def has_game_started(game_id):
    game = games_collection.find_one({"_id": game_id})
    return game.get("started", False)

# Endpoint to create a new game
@app.route("/game", methods=["POST"])
def create_game():
    data = request.json
    player_name = data.get("playerName")  # Updated to match the spec

    if not player_name:
        return jsonify({"error": "Player name not provided"}), 400

    # Generate a unique game ID (you can use ObjectId for this)
    game_id = str(ObjectId())

    # Initialize the game_order array with the received player_name
    game_order = [player_name]

    # Store game data in MongoDB with 'started' set to False initially
    games_collection.insert_one({"_id": game_id, "order": game_order, "started": False})

    return jsonify({"gameId": game_id, "playerName": player_name}), 200


# Endpoint to join an existing game
@app.route("/game/join", methods=["POST"])
def join_game():
    data = request.json
    game_id = data.get("gameId")
    player_name = data.get("playerName")

    # Check if the game exists
    game = games_collection.find_one({"_id": game_id})
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Add the player to the game at the end of the order
    game_order = game.get("order", [])
    game_order.append(player_name)
    games_collection.update_one({"_id": game_id}, {"$set": {"order": game_order}})

    return jsonify({"message": "Player joined the game"}), 200

# Endpoint to start an existing game
@app.route("/game/start", methods=["POST"])
def start_game():
    data = request.json
    game_id = data.get("gameId")
    player_name = data.get("playerName")

    # Check if the game exists
    game = games_collection.find_one({"_id": game_id})
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Check if the game has already started
    if game.get("started", False):
        return jsonify({"error": "Game has already started"}), 400

    # Check if the player starting the game is the game creator
    if game["order"][0] != player_name:
        return jsonify({"error": "Only the game creator can start the game"}), 400

    # Implement start game logic here
    game["started"] = True

    # Shuffle the player order randomly
    random.shuffle(game["order"])

    # Set initial round to 1
    game["round"] = 1

    games_collection.update_one({"_id": game_id}, {"$set": {"started": True, "order": game["order"], "round": 1}})

    return jsonify({"message": "Game started with randomized order for Round 1"}), 200

# Endpoint to update a player's round score and advance to the next round
@app.route("/game/round/score", methods=["POST"])
def record_round_score():
    data = request.json
    game_id = data.get("gameId")
    player_name = data.get("playerName")
    score = data.get("score")

    # Check if the game exists
    game = games_collection.find_one({"_id": game_id})
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Check if the game has started
    if not game.get("started", False):
        return jsonify({"error": "Game has not started yet"}), 400

    # Check if the player is in the game order
    if player_name not in game["order"]:
        return jsonify({"error": "Player not in the game"}), 400

    # Update the player's current score
    games_collection.update_one(
        {"_id": game_id, "order": player_name},
        {"$set": {"scores.{}".format(player_name): score}}
    )

    game = games_collection.find_one({"_id": game_id})

    # Check if all players have submitted scores for the current round
    if len(game["scores"]) == len(game["order"]):
        # Calculate the order for the next round
        # Assuming you have a function calculate_next_round_order() for this
        next_round_order = calculate_next_round_order(game["order"], game["scores"])

        # Increment the round and wipe the 'scores' list
        game["round"] += 1
        game["scores"] = {}

        # Update the game data with the new order and round
        games_collection.update_one(
            {"_id": game_id},
            {"$set": {"order": next_round_order, "round": game["round"], "scores": {}}}
        )

        return jsonify({"message": f"Round {game['round']} started with a new order"}), 200

    return jsonify({"message": "Score recorded successfully"}), 200


def calculate_next_round_order(prev_order, prev_scores):
    # Create a list of player names sorted by their scores in ascending order
    sorted_players = sorted(prev_scores.keys(), key=lambda x: (prev_scores[x], prev_order.index(x)))

    return sorted_players


# Endpoint to get the ordered list of player names for a game
@app.route("/game/round/order/<gameId>", methods=["GET"])
def get_round_order(gameId):

    # Check if the game exists
    game = games_collection.find_one({"_id": gameId})
    if not game:
        return jsonify({"error": "Game not found"}), 404

    return jsonify(game["order"]), 200

if __name__ == "__main__":
    app.run(debug=True, port=5555, host="0.0.0.0")
