from flask import (
    Flask,
    render_template,
    request,
    Response,
    stream_with_context,
    jsonify,
)
import openai
import strava_api

from datetime import datetime, time, date, timezone, timedelta

client = openai.OpenAI()
strava_data = strava_api.getStravaData(7)
#print(strava_data)
#str(date.strftime("%m/%d, %H:%M"))

app = Flask(__name__)

plans = [
    {'Day': 'M', 'Activity': 'Bike or Swim',  'Details': '45 min'},
    {'Day': 'Tu', 'Activity': 'Run and Chest/Tris',  'Details': '5k'},
    {'Day': 'W', 'Activity': 'Swim and Back/Bis',  'Details': '5x200M 30\"'},
    {'Day': 'Th', 'Activity': 'Bike',  'Details': '45 min'},
    {'Day': 'F', 'Activity': 'Swim and Shoulders/Abs',  'Details': '1x500M 2\' and 5x100M 20\"'},
    {'Day': 'Sa', 'Activity': 'Run',  'Details': '10k'},
    {'Day': 'Su', 'Activity': 'Legs',  'Details': '45 min'},
]

chat_history = [
    {"role": "system", "content": "Hi! I am your personal trainer."},
    {"role": "system", "content": str("Here's your training block for the next week: "+str(plans))},
    {"role": "system", "content": str("Here's your training log for the last week: "+str(strava_data))},   
]

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", chat_history=chat_history, activities=strava_data, plans=plans)

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
    n=0
    today = date.today()
    previousMonday = today + timedelta(days=-today.weekday())
    for p in plans:
            workout = {
                "title":p['Activity'], 
                "start":str(previousMonday+timedelta(days=n))
            }
            n+=1
            workouts.append(workout)
    return workouts

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

@app.route("/plan")
def plan():
    
    swim = ["Swim", 0,0,'5x200M 30\"',0,'1x500M 2\' and 5x100M 20\"',0,0]
    run = ["Run", 0,"5k",0,0,0,'10k',0]
    bike  = ["Bike", "45min",0,0,'45min',0,0,0]
    strength = ["Strength", 0,"Chest and Tris","Back and Bis",0,0,0,"Legs"]
    plans = [swim, run, bike, strength]
    print(plans)
    return render_template("plan.html", plans=plans)


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
    chat_history = [{"role": "system", "content": "You are a personal trainer."}]
    return jsonify(success=True)
