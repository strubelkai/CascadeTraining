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

client = openai.OpenAI()
print("Getting activities")
strava_data = strava_api.getStravaData()
print(strava_data)

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
    {"role": "system", "content": str("Here's your training log for the last two weeks: "+str(strava_data))},
    {"role": "system", "content": str("Here's your training block for the next week: "+str(plans))},
]



@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", chat_history=chat_history, activities=strava_data, plans=plans)


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
