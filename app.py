import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Init OpenAI client (v1+)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Init Slack app
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.event("app_mention")
def handle_mention_events(body, say):
    user_message = body["event"]["text"]
    prompt = user_message.split('>', 1)[1].strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant in Slack."},
            {"role": "user", "content": prompt}
        ]
    )

    reply = response.choices[0].message.content.strip()

    say(
        text=reply,
        thread_ts=body["event"].get("thread_ts", body["event"]["ts"])  # 👈 Respond in same thread
    )

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
