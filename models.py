from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import calendar
import os
import uuid

if "MONGODB_PASS" in os.environ:
    uri = "mongodb+srv://{}:{}@cluster0.cmoki.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0".format(os.environ["MONGODB_USER"], os.environ["MONGODB_PASS"])
else:
    raise Exception("MONGODB_PASS not in environment")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["SMU_HealthTracker"]

def register_user(db, name, email, userID):
    db.users.insert_one({
        "name": name,
        "email": email,
        "userID":userID
    })


def complete_goal(db, userID, goalID):
    goal = db.goals.find_one({"goalID": goalID, "userID": userID})
    if goal:
        today_index = datetime.now().weekday()
        if goal['days'][today_index] and not (goal['completed'] or goal['daily_completed']):
            # Increment times_completed and update goal in the DB
            db.goals.update_one(
                {"goalID": goalID},
                {"$inc": {"times_completed": 1},
                "$set": {"daily_completed": True}}
            )
            # Check if limit is reached
            if goal['times_completed'] + 1 >= goal['limit']:
                db.goals.update_one({"goalID": goalID}, {"$set": {"completed": True}})
            return True
    return False


def calculate_limit(days_of_week, weeks):
    return sum(d for d in days_of_week if d) * weeks


def create_goal(db, userID, title, category, days, reminders, weeks):
    limit = calculate_limit(days, weeks)
    goalID = str(uuid.uuid4())
    #goalID = "123" 
    goal = {
        "goalID": goalID,
        "userID": userID,
        "title": title,
        "category": category,
        "days": days,
        "reminders": reminders,
        "times_completed": 0,
        "limit": limit,
        "weeks": weeks,
        "streak": 0,
        "completed": False,
        "daily_completed": False
    }
    db.goals.insert_one(goal) 


def update_goal(db, goalID):
    db.goals.update_one(
        {"goalID": goalID},
        {
            "$inc": {"times_completed": 1}, 
            "$set": {"daily_completed": True}  
        }
    )


def edit_goal(db, request, goalID):
    if request.method == 'DELETE':
        db.goals.delete_one({"goalID": goalID})

    if request.method == 'PUT':
        data = request.json 
        update_data = {key: data[key] for key in data if key != 'goalID'}
        
        db.goals.update_one({"goalID": goalID}, {"$set": update_data})

def reset_daily_goals(db):

    db.goals.update_many(
        {"daily_completed": True}, 
        {"$set": {"daily_completed": False}}
    )

scheduler = BackgroundScheduler()

scheduler.add_job(reset_daily_goals, 'cron', hour=0, minute=0, args=[db])
scheduler.start()

# import pymongo as mongo

##############TESTING#############
# def main():
    # user_name = "John Doe"
    # user_email = "john.doe@example.com"
    # userID = str(uuid.uuid4())
    # #register_user(db, user_name, user_email, userID)

    # create_goal(db, 123456, "Breakdown", "Health", [True, True, True, True, True, False, False], True, 4)
    # update_goal(db, "123")
    #complete_goal(db, 123456, 2468)

# if __name__ == "__main__":
#     main()


#####FIRST ATTEMPT#######
# def register_user(DB, name, username, email, password):
#     db = DB
#     db.users.insert_one({
#         "username": username,
#         "password": password,
#         "name": name,
#         "email": email
#     })
#     access_token = create_access_token(identity=username)
#     return access_token

# def register():
#     data = request.json
#     name = data.get('name')
#     username = data.get('username')
#     email = data.get('email')
#     password = data.get('password')
    
#     payload = {
#         "name": name,
#         "username": username,
#         "email": email,
#         "password": password
#     }
    
#     # Send the registration request to PropelAuth
#     response = requests.post(PROPEL_AUTH_REGISTER_URL, json=payload)
    
#     if response.status_code == 201:
#         return jsonify(success=True), 201
#     else:
#         return jsonify(success=False), response.status_code


# def complete_goal(db, userID, goalID):
#     goal = db.users.insert_one({"_id": goalID, "userID": userID})
#     if goal:
#         today_index = datetime.now().weekday()  # 0 = monday, 6 = sunday and loops every week
#         if goal['days_of_week'][today_index] and not goal['completed']:
#             goal['times_completed'] += 1
#             update_goal(goalID, datetime.now().date())
#             if goal['times_completed'] >= goal['limit']:
#                 db.goals.update_one({"_id": goalID}, {"$set": {"completed": True}})
#             return True
#     return False

# def calculate_limit(days_of_week):
#     today = datetime.now()
#     next_month = (today.month % 12) + 1
#     year = today.year if next_month > 1 else today.year + 1
    
#     num_days = calendar.monthrange(year, next_month)[1]
    
#     limit = 0
#     for day in range(1, num_days + 1):
#         weekday = (datetime(year, next_month, day).weekday()) 
#         if days_of_week[weekday]:
#             limit += 1
            
#     return limit

# def create_goal(db, userID, title, category, days, reminders):
#     limit = calculate_limit(days)
#     goal = {
#         "userID": userID,
#         "title": title,
#         "category": category,
#         # "description": description,
#         "days": days,
#         "reminders": reminders,
#         "times_completed": 0,
#         "limit": limit,
#         "streak": 0,
#         "completed": False
#     }
#     db.goals.insert_one(goal)

# def update_goal(db, goalID):
#     today = datetime.date.today()
#     db.goals.update_one(
#         {"_id": goalID},
#         {
#             "$inc": {"times_completed": 1}, 
#             "$set": {"completed": True}  
#         }
#     )


# def edit_goal(db, request, goalID):
#     if request.method == 'DELETE':
#         db.goals.delete_one({"_id": goalID})

#     if request.method == 'PUT':
#         data = request.json 
#         update_data = {key: data[key] for key in data if key != 'goalID'}
        
#         db.goals.update_one({"_id": goalID}, {"$set": update_data})





######OTHER REPOS#######
# from pymongo import MongoClient
# from bson.objectid import ObjectId
# from apscheduler.schedulers.background import BackgroundScheduler
# from datetime import datetime
# import smtplib
# from email.mime.text import MIMEText

# client = MongoClient('mongodb://localhost:27017/')
# db = client['goal_tracker']

# # Example goal document structure
# goal_schema = {
#     "userID": ObjectId(),  # Reference to user
#     "goal_type": "mental",  # or "physical"
#     "goal_name": "Meditate",
#     "days_of_week": ["Monday", "Friday"],  # Days to complete the goal
#     "notification_time": "09:00",  # Time to send email reminder
#     "created_at": datetime.now(),
#     "updated_at": datetime.now()
# }

# def add_goal():
#     data = request.json
#     mongo.db.goals.insert_one(data)
#     return jsonify({"status": "Goal added!"}), 201

# def get_goals(userID):
#     goals = mongo.db.goals.find({"userID": ObjectId(userID)})
#     return jsonify([goal for goal in goals]), 200

# def send_email_notification(goal):
#     msg = MIMEText(f"Reminder: It's time to {goal['goal_name']}!")
#     msg['Subject'] = f"Goal Reminder: {goal['goal_name']}"
#     msg['From'] = 'your_email@example.com'
#     msg['To'] = 'user_email@example.com'  # Replace with user email

#     with smtplib.SMTP('smtp.example.com') as server:
#         server.login('your_email@example.com', 'your_password')
#         server.sendmail(msg['From'], [msg['To']], msg.as_string())

# def check_goals():
#     today = datetime.now().strftime('%A')
#     time_now = datetime.now().strftime('%H:%M')

#     goals = mongo.db.goals.find({"days_of_week": today, "notification_time": time_now})
#     for goal in goals:
#         send_email_notification(goal)

# scheduler = BackgroundScheduler()
# scheduler.add_job(check_goals, 'cron', minute='*')  # Checks every minute
# scheduler.start()

# from flask_pymongo import PyMongo
# from datetime import datetime
# from flask import Flask

# app = Flask(__name__)
# app.config.from_object('config.Config')
# mongo = PyMongo(app)

# class User:
#     def __init__(self, username, email):
#         self.username = username
#         self.email = email

#     def save(self):
#         mongo.db.users.insert_one({
#             "username": self.username,
#             "email": self.email,
#             "goals": []
#         })

# class Goal:
#     def __init__(self, userID, description, category, days):
#         self.userID = userID
#         self.description = description
#         self.category = category
#         self.days = days
#         self.completed_days = []

#     def save(self):
#         mongo.db.users.update_one(
#             {"_id": self.userID},
#             {"$push": {"goals": {
#                 "description": self.description,
#                 "category": self.category,
#                 "days": self.days,
#                 "completed_days": []
#             }}}
#         )

# from flask_jwt_extended import create_access_token
# from datetime import datetime, timedelta
# from models import create_user, create_goal, update_goal, mongo

# def register_user(username, password):
#     create_user(username, password)
#     access_token = create_access_token(identity=username)
#     return access_token

# def add_goal(userID, title, description, consistency, notifications):
#     create_goal(userID, title, description, consistency, notifications)

# def complete_goal(userID, goalID):
#     goal = mongo.db.goals.find_one({"_id": goalID, "userID": userID})
#     if goal:
#         today = datetime.now().date()
#         if today.strftime("%A") in goal['consistency']:
#             update_goal(goalID, today)
#             # Update streak logic
#             return True
#     return False


