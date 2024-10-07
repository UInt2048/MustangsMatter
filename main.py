from flask import Flask, jsonify, render_template, request, session
from propelauth_py import init_base_auth, UnauthorizedException
from collections import namedtuple
from datetime import datetime
from bson import ObjectId
import os
import chatbot_module
import models

app = Flask(__name__)

# Initialize PropelAuth
auth = init_base_auth(os.environ["PROPELAUTH_BASE"], os.environ["PROPELAUTH_KEY"])

# Required for session
app.secret_key = hex(hash(os.environ["MONGODB_PASS"]))

@app.route("/")
def main():
     """Main page of the app"""
     # Front-end conversion for display
     return render_template("index.html", propelauth_base = os.environ["PROPELAUTH_BASE"])

@app.route("/login", methods=['GET', 'POST'])
def login_user():
    """Set session to authenticated user and show authenticated content"""
    user_id: str = request.args['id']
    email: str = request.args['email']
    name: str = request.args['name']
    
    if (models.db["users"].find_one({"userID": user_id}) is None):
        models.register_user(models.db, name, email, user_id)
    session["user_id"] = user_id
    return auth_data(user_id, email, name)

@app.route("/logout", methods=['GET', 'POST'])
def logout_user():
    """Ensure session is clear"""
    if (session["user_id"] is not None):
        models.db["users"].update_one({"userID": session["user_id"]}, {"$unset": {"chatbot_history": []}})
        session["user_id"] = None
    return ""

@app.route("/add", methods=['GET', 'POST'])
def add_data():
    """Add a goal to database and update authenticated content"""
    name: str = request.args['name']
    goal_type: str = request.args['type']
    days: list[bool] = [int(request.args[f"d{i}"]) != 0 for i in range(0, 7)]
    notifs: bool = int(request.args['notifs']) != 0
    weeks: int = int(request.args['weeks'])
    
    models.create_goal(models.db, session["user_id"], name, goal_type, days, notifs, weeks)
    return auth_data(session["user_id"])

@app.route("/edit", methods=['GET', 'POST'])
def edit_goal():
    """Edit a goal in database and update authenticated content"""
    goal_id: str = request.args['id']
    name: str = request.args['name']
    notifs: bool = int(request.args['notifs']) != 0
    
    Request = namedtuple("Request", ["method", "json"])
    models.edit_goal(models.db, Request("PUT", {"title": name, "reminders": notifs}), goal_id)
    return auth_data(session["user_id"])

@app.route("/delete", methods=['GET', 'POST'])
def delete_goal():
    """Remove a goal from database and update authenticated content"""
    goal_id: str = request.args['goal']
    
    Request = namedtuple("Request", ["method", "json"])
    models.edit_goal(models.db, Request("DELETE", {}), goal_id)
    return auth_data(session["user_id"])

@app.route("/complete", methods=['GET', 'POST'])
def complete_goal():
    """Complete a goal if permissible and update authenticated content"""
    goal_id: str = request.args['goal']
    
    models.complete_goal(models.db, session["user_id"], goal_id) 
    return auth_data(session["user_id"])

@app.route("/message", methods=['GET', 'POST'])
def message_chatbot():
    """Message the chatbot and update authenticated content"""
    msg: str = request.args['text']
    user_id: str = session["user_id"]
    
    chatbot_history = models.db["users"].find_one({"userID": user_id}).get("chatbot_history", [])
    result = {"user_date": datetime.now(), "user_msg": msg}
    history = generate_machine_history(chatbot_history)

    result["ai_msg"] = chatbot_module.call_chatbot(msg, history, user_id)
    result["ai_date"] = datetime.now()
    chatbot_history.append(result)
    models.db["users"].update_one({"userID": user_id}, {"$set": {"chatbot_history": chatbot_history}})
    return auth_data(user_id)

def generate_machine_history(history: list[dict]) -> str:
    """Convert history from frontend-facing form to chatbot-facing form"""
    return "".join(["Human message: {}\nAI message: {}\n".
        format(pair["user_msg"], pair["ai_msg"]) for pair in history])

def auth_data(user_id: str, email: str | None = None, name: str | None = None):
    """Get and display authenticated content"""
    return display_data(get_data(user_id, email, name))

def get_data(user_id: str, email: str | None, name: str | None) -> list[dict]:
    """Fetch data for authenticated user"""
    user = models.db["users"].find_one({"userID": user_id})
    if (user is None):
        return []
    
    # Update the database if email or name has been changed
    if (email is not None and email != user["email"]):
        models.db["users"].update_one({"userID": user_id}, {"$set": {"email": email}})
    if (name is not None and name != user["name"]):
        models.db["users"].update_one({"userID": user_id}, {"$set": {"name": name}})

    # Retrieve updated user and associated goals
    user = models.db["users"].find_one({"userID": user_id})
    goals = [user, *models.db["goals"].find({"userID": user["userID"]})]
    for goal in goals:
        if "_id" in goal:
            goal["_id"] = str(goal["_id"])
    return goals

def display_data(our_data: list[dict]):
     """Render authenticated content from provided data"""
     if len(our_data) > 0:
        profile_data = our_data[0]
        incomplete_goals = []
        complete_goals = []
        day_names = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
        for goal in our_data[1:]:
            days = []
            for day_index, _ in enumerate(goal["days"]):
                if (goal["days"][day_index]):
                    days.append(day_names[day_index])
            if len(days) > 0:
                goal["user_days"] = ', '.join(days)
                goal["weeks"] = goal["limit"] // len(days)
            else:
                goal["user_days"] = "None"
                goal["weeks"] = 1
                goal["limit"] = 1
            match goal["category"]:
                case "physical":
                    goal["color"] = "#cc0035"
                case "mental":
                    goal["color"] = "#354ca1"
            if (goal["times_completed"] == goal["limit"]):
                complete_goals.append(goal)
            else:
                incomplete_goals.append(goal)
        return render_template("auth.html",
            profile_data = profile_data,
            incomplete_goals = incomplete_goals,
            complete_goals = complete_goals)
     else:
         return render_template("auth.html",
             profile_data = {},
             incomplete_goals = [],
             complete_goals = [])

@app.route("/api/whoami", methods=["GET"])
def whoami():
     auth_header = request.headers.get("Authorization")
     if not auth_header:
          return jsonify({"error": "Missing authorization header"}), 401
     try:
        user = auth.validate_access_token_and_get_user(auth_header)
        return jsonify({"user_id": user.user_id, "email": user.email}), 200
     except UnauthorizedException:
        return jsonify({"error": "Invalid access token"}), 401

@app.route("/404")
@app.errorhandler(404)
def error_404(error = None):
    return "Peruna got lost :(<br/>Please ensure you typed the URL correctly."

@app.route("/500")
@app.errorhandler(500)
def error_500(error = None):
    return "Peruna pooped on the field :(<br/>A handler will take care of this soon." 
