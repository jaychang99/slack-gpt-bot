import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI
from dotenv import load_dotenv
from slack_sdk import WebClient
from openai import OpenAIError

load_dotenv()
# Slack WebClient for fetching thread history
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
bot_user_id = os.getenv("SLACK_BOT_USER_ID")  # <-- Add this to your .env file


# Init OpenAI client (v1+)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Init Slack app
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.event("app_mention")
def handle_mention_events(body, say):
    event = body["event"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])

    try:
        # Fetch thread messages
        history = slack_client.conversations_replies(channel=channel, ts=thread_ts).get("messages", [])

        # Only keep the last 10
        history = history[-10:]

        # Format for OpenAI
        messages = [{"role": "system", "content": "You are a helpful assistant inside a Slack thread."}]
        for msg in history:
            text = msg.get("text", "")
            user_id = msg.get("user")

            if user_id == bot_user_id:
                role = "assistant"
            else:
                role = "user"

            messages.append({
                "role": role,
                "content": text
            })

        # Send to OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        reply = response.choices[0].message.content.strip()
        say(text=reply, thread_ts=thread_ts)

    except OpenAIError as e:
        say(text="⚠️ GPT is unavailable. Possibly due to usage limits.", thread_ts=thread_ts)
    except Exception as e:
        say(text=f"⚠️ Unexpected error: {str(e)}", thread_ts=thread_ts)

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
