from flask import (
    Flask,
    render_template,
    request,
    Response,
    stream_with_context,
    jsonify,
    redirect,
    url_for,
    session
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


app = Flask(__name__)
# adding configuration for using a sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# Set a secret key for session management
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # Use environment variable or fallback
# Creating an SQLAlchemy instance
db = SQLAlchemy(app)

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()
    print("Success")

chat_history = [
    {"role": "system", "content": "Hey there, I'm Lionel Sanders. You might know me as a professional triathlete, but today, I'm here to be your coach, your mentor, and your biggest supporter. How can I help today? Shall we discuss your past week of training?"},
]

@app.route("/coach", methods=["GET"])
def coach():
    if 'refresh_token' not in session:
        return redirect(url_for('sign_up'))
    
    try:
        # Get Strava data
        strava_data = strava_api.getStravaData(30, session['refresh_token'])
        
        if not strava_data:
            print("No Strava data returned")
            return redirect(url_for('sign_up'))
        
        # Store the formatted data in the session for AI context
        session['strava_context'] = format_strava_data(strava_data)
        
        # Initialize chat history with a system message if it doesn't exist
        if 'chat_history' not in session:
            session['chat_history'] = [{
                "role": "system",
                "content": """You are a helpful and concise running coach. You have access to the user's recent Strava activities.
                When responding:
                1. Keep responses brief and focused
                2. Reference specific activities when relevant
                3. Provide actionable advice
                4. Use bullet points for multiple suggestions
                5. Focus on one key point at a time"""
            }]
        
        return render_template("coach.html", activities=strava_data)
    except Exception as e:
        print(f"Error in coach route: {str(e)}")
        return redirect(url_for('sign_up'))

def format_strava_data(strava_data):
    """Format Strava data into a structured format for AI context"""
    if not strava_data:
        return "No recent activities found."
    
    formatted = []
    for activity in strava_data:
        formatted.append({
            "date": activity.get('Date', ''),
            "type": activity.get('Activity', ''),
            "name": activity.get('Name', ''),
            "distance": activity.get('Distance (KM)', 0),
            "time": activity.get('Time', 0)
        })
    return formatted

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", hidenav=True)

@app.route("/signup")
def sign_up():
    try:
        redirect_uri = os.getenv('REDIRECT_URL')
        if not redirect_uri:
            print("Error: REDIRECT_URL not set in environment variables")
            return redirect("/?error=config_error")
        
        # Ensure the redirect URL doesn't have a trailing slash
        redirect_uri = redirect_uri.rstrip('/')
        
        # Construct the OAuth URL
        oauth_url = f"https://www.strava.com/oauth/authorize?client_id={os.getenv('CLIENT_ID')}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=read,activity:read_all"
        
        print(f"Redirecting to Strava OAuth URL: {oauth_url}")
        return redirect(oauth_url)
    except Exception as e:
        print(f"Error in sign_up route: {str(e)}")
        return redirect("/?error=server_error")

@app.route("/exchange_token")
def exchange_token():
    try:
        code = request.args.get('code')
        if not code:
            print("No code provided in request")
            return redirect("/?error=no_code")
        
        print("Received authorization code, attempting token exchange...")
        refresh_token = strava_api.getRefreshToken(code)
        
        if not refresh_token:
            print("Failed to get refresh token")
            return redirect("/?error=token_failure")
            
        # Store the refresh token in the session
        session['refresh_token'] = refresh_token
        # Set a user_id in the session to indicate authenticated state
        session['user_id'] = 'strava_user'  # We can use a simple identifier since we're using Strava auth
        print("Successfully obtained refresh token")
        
        return redirect("/coach")
    except Exception as e:
        print(f"Error in exchange_token: {str(e)}")
        return redirect("/?error=server_error")

@app.route("/activities/<int:activity_id>", methods=["GET"])
def activities(activity_id):
    Activity = strava_api.getStravaActivites(activity_id)
    chat_history = [
        {"role": "system", "content": "Hey there, I'm Lionel Sanders. You might know me as a professional triathlete, but today, I'm here to be your coach, your mentor, and your biggest supporter. How can I help? Shall we discuss your past week of training?"},
        # {"role": "system", "content": str("Here's your current training block: "+str(plans))},
        {"role": "system", "content": str("Let's look at just one activity: "+str(Activity))},   
    ]
    return render_template("activity.html", chat_history=chat_history, activity=Activity)


@app.route('/data')
def get_calendar_data():
    print("Data route called")
    if 'refresh_token' not in session:
        print("No refresh token in session")
        return jsonify([])
    
    try:
        print("Getting Strava data...")
        # Get Strava data for the last 90 days
        activities = strava_api.getStravaData(90, session['refresh_token'])
        print(f"Received {len(activities) if activities else 0} activities")
        
        # Format activities for FullCalendar
        events = []
        for activity in activities:
            try:
                event = {
                    'id': activity['id'],
                    'title': f"{activity['Activity']} - {activity['Distance (KM)']} km",
                    'start': activity['Date'],
                    'allDay': True,
                    'extendedProps': {
                        'type': activity['Activity'],
                        'distance': activity['Distance (KM)'],
                        'unit': 'km',
                        'duration': activity['Time'],
                        'name': activity['Name']
                    }
                }
                events.append(event)
            except KeyError as e:
                print(f"Missing key in activity data: {str(e)}")
                print(f"Activity data: {activity}")
                continue
        
        print(f"Returning {len(events)} events")
        return jsonify(events)
    except Exception as e:
        print(f"Error fetching calendar data: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])

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
    if 'refresh_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get the Strava context from session
        strava_context = session.get('strava_context', [])
        
        # Add user message to chat history
        if 'chat_history' not in session:
            session['chat_history'] = []
        session['chat_history'].append({"role": "user", "content": user_message})
        
        # Prepare the messages for the AI
        messages = [
            {"role": "system", "content": """You are a helpful and concise running coach. You have access to the user's recent Strava activities.
            When responding:
            1. Keep responses brief and focused
            2. Reference specific activities when relevant
            3. Provide actionable advice
            4. Use bullet points for multiple suggestions
            5. Focus on one key point at a time"""},
            {"role": "user", "content": f"Here is my recent Strava data: {strava_context}"},
            {"role": "assistant", "content": "I've reviewed your recent activities. How can I help you today?"},
            {"role": "user", "content": user_message}
        ]
        
        # Get AI response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI response to chat history
        session['chat_history'].append({"role": "assistant", "content": ai_response})
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({'error': 'Failed to get response'}), 500


@app.route("/stream", methods=["GET"])
def stream():
    def generate():
        assistant_response_content = ""
        strava_data = strava_api.getStravaData(14)
        chat_history = [
            {"role": "system", "content": "Hey there, I'm Lionel Sanders. You might know me as a professional triathlete, but today, I'm here to be your coach, your mentor, and your biggest supporter. How can I help? Shall we discuss your past week of training?"},
            # {"role": "system", "content": str("Here's your current training block: "+str(plans))},
            {"role": "system", "content": str("Here's your training log for the last two weeks: "+str(strava_data))},  
        ]
        with client.chat.completions.create(
            model="gpt-4o",
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

# # Models
# class Activity(db.Model):
#     # Id : Field which stores unique id for every row in 
#     # database table.
#     # -- name
#     # -- required String, in form	The name of the activity.
#     # -- type
#     # -- String, in form	Type of activity. For example - Run, Ride etc.
#     # -- sport_type
#     # -- required String, in form	Sport type of activity. For example - Run, MountainBikeRide, Ride, etc.
#     # -- start_date_local
#     # -- required Date, in form	ISO 8601 formatted date time.
#     # -- elapsed_time
#     # -- required Integer, in form	In seconds.
#     # -- description
#     # -- String, in form	Description of the activity.
#     # -- distance
#     # -- Float, in form	In meters.

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(200), unique=False, nullable=False)
#     type = db.Column(db.String(20), unique=False, nullable=False)
#     sport_type = db.Column(db.String(20), unique=False, nullable=False)
#     start_date_local = db.Column(db.Date, unique=False, nullable=False)
#     elapsed_time = db.Column(db.Integer, nullable=False)
#     description = db.Column(db.String(200), unique=False, nullable=False)
#     distance = db.Column(db.Float, unique=False, nullable=False)
 
#     # repr method represents how one object of this datatable
#     # will look like
#     def __repr__(self):
#         return f"Name : {self.name}, Description: {self.description}"
    
if __name__ == '__main__':
    app.run()