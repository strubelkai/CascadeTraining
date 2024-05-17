from flask import (
    Flask,
    render_template,
    request,
    Response,
    stream_with_context,
    jsonify,
    redirect
)
import openai
import strava_api
import planner

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from datetime import datetime, time, date, timezone, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

client = openai.OpenAI()
strava_data = strava_api.getStravaData(14)
#print(strava_data)
#str(date.strftime("%m/%d, %H:%M"))
plans = planner.getPlans()

app = Flask(__name__)
# adding configuration for using a sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# Creating an SQLAlchemy instance
db = SQLAlchemy(app)

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()
    print("Success")

chat_history = [
    {"role": "system", "content": "Hey there, I'm Lionel Sanders. You might know me as a professional triathlete, but today, I'm here to be your coach, your mentor, and your biggest supporter. I've been through the trenches, battled my demons, and come out on top, and now, I'm here to share everything I've learned with you."},
    # {"role": "system", "content": str("Here's your current training block: "+str(plans))},
    {"role": "system", "content": str("Here's your training log for the last two weeks: "+str(strava_data))},  
]

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", chat_history=chat_history, activities=strava_data, plans=plans)

@app.route("/signup", methods=["GET"])
def sign_up():
    OAuthURL = "http://www.strava.com/oauth/authorize?client_id="+ os.getenv('CLIENT_ID') + "&response_type=code&redirect_uri=http://127.0.0.1:5000/exchange_token&approval_prompt=force&scope=read,activity:read_all"
    return redirect(OAuthURL)

@app.route("/exchange_token")
def exchange_token():
    code = request.args.get('code')
    refreshCode =  strava_api.getRefreshToken(code)
    return refreshCode
   

@app.route("/activities/<int:activity_id>", methods=["GET"])
def activities(activity_id):
    Activity = strava_api.getStravaActivites(activity_id)
    chat_history = [
        {"role": "system", "content": "Hey there, I'm Lionel Sanders. You might know me as a professional triathlete, but today, I'm here to be your coach, your mentor, and your biggest supporter. I've been through the trenches, battled my demons, and come out on top, and now, I'm here to share everything I've learned with you."},
        # {"role": "system", "content": str("Here's your current training block: "+str(plans))},
        {"role": "system", "content": str("Let's look at just one activity: "+str(Activity))},   
    ]
    return render_template("activity.html", chat_history=chat_history, activity=Activity)


@app.route('/data')
def return_data():
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    workouts = []
    strava_data = strava_api.getStravaData(90)
    for data in strava_data:
            workout = {
                "title":data['Activity'], 
                "start":data['Date'], 
            }
            workouts.append(workout)
    # n=0
    # today = date.today()
    # previousMonday = today + timedelta(days=-today.weekday())
    # plans = planner.getPlans()
    # for p in plans:
    #         workout = {
    #             "title":p['Activity'], 
    #             "start":str(previousMonday+timedelta(days=n))
    #         }
    #         n+=1
    #         workouts.append(workout)
    return workouts

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")


# @app.route("/plan", methods=["POST", "GET"])
# def plan():
#     swim = ["Swim", 0,0,'5x200M 30\"',0,'1x500M 2\' and 5x100M 20\"',0,0]
#     run = ["Run", 0,"5k",0,0,0,'10k',0]
#     bike  = ["Bike", "45min",0,0,'45min',0,0,0]
#     strength = ["Strength", 0,"Chest and Tris","Back and Bis",0,0,0,"Legs"]
#     plans = [swim, run, bike, strength]

#     if (request.method == "POST"):
#         # id = request.form['id']
#         name = request.form['name']
#         type = request.form['type']
#         sport_type = request.form['sport_type']
#         start_date_local = request.form['start_date_local']
#         elapsed_time = request.form['elapsed_time']
#         description = request.form['description']
#         distance = request.form['distance']


#         new_activity = Activity(name="Interval Run", type=type, sport_type="run", start_date_local=date.today(), elapsed_time="1200", description="1 on 2 off", distance="5000")
#         #new_activity = Activity(name=name, type=type, sport_type=type, start_date_local=start_date_local, elapsed_time=elapsed_time, description=description, distance=distance)
#         try:
#             db.session.add(new_activity)
#             db.session.commit()
#             return redirect('/plan')
#         except:
#             return "Error adding activity"
#     else: 
#         activities = Activity.query.order_by(Activity.start_date_local)
#         return render_template("plan.html", plans=plans, activities=activities)


@app.route("/chat", methods=["POST"])
def chat():
    content = request.json["message"]
    chat_history.append({"role": "user", "content": content})
    return jsonify(success=True)


@app.route("/stream", methods=["GET"])
def stream():
    def generate():
        assistant_response_content = ""

        with client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=chat_history,
            stream=True,
        ) as stream:
            for chunk in stream:
                if chunk.choices[0].delta and chunk.choices[0].delta.content:
                    # Accumulate the content only if it's not None
                    assistant_response_content += chunk.choices[0].delta.content
                    yield f"data: {chunk.choices[0].delta.content}\n\n"
                if chunk.choices[0].finish_reason == "stop":
                    break  # Stop if the finish reason is 'stop'

        # Once the loop is done, append the full message to chat_history
        chat_history.append(
            {"role": "assistant", "content": assistant_response_content}
        )

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/reset", methods=["POST"])
def reset_chat():
    global chat_history
    chat_history = [{"role": "system", "content": "You are Lionel Sanders, famous triathalete, helping here as a personal trainer."}]
    return jsonify(success=True)

# Models
class Activity(db.Model):
    # Id : Field which stores unique id for every row in 
    # database table.
    # -- name
    # -- required String, in form	The name of the activity.
    # -- type
    # -- String, in form	Type of activity. For example - Run, Ride etc.
    # -- sport_type
    # -- required String, in form	Sport type of activity. For example - Run, MountainBikeRide, Ride, etc.
    # -- start_date_local
    # -- required Date, in form	ISO 8601 formatted date time.
    # -- elapsed_time
    # -- required Integer, in form	In seconds.
    # -- description
    # -- String, in form	Description of the activity.
    # -- distance
    # -- Float, in form	In meters.

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=False, nullable=False)
    type = db.Column(db.String(20), unique=False, nullable=False)
    sport_type = db.Column(db.String(20), unique=False, nullable=False)
    start_date_local = db.Column(db.Date, unique=False, nullable=False)
    elapsed_time = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), unique=False, nullable=False)
    distance = db.Column(db.Float, unique=False, nullable=False)
 
    # repr method represents how one object of this datatable
    # will look like
    def __repr__(self):
        return f"Name : {self.name}, Description: {self.description}"
    
