import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from openai import OpenAI, OpenAIError

# Load environment variables
load_dotenv()

DEFAULT_SYSTEM_INSTRUCTIONS = "You are a helpful assistant inside Slack. Keep responses helpful but concise."

# Env vars
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_CUSTOM_INSTRUCTIONS = os.getenv("SLACK_CUSTOM_INSTRUCTIONS", DEFAULT_SYSTEM_INSTRUCTIONS)

# Init Slack + OpenAI clients
app = App(token=SLACK_BOT_TOKEN)
slack_client = WebClient(token=SLACK_BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


@app.event("app_mention")
def handle_mentions(body, say):
    event = body["event"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])

    try:
        # Get last 10 messages from thread
        history = slack_client.conversations_replies(channel=channel, ts=thread_ts).get("messages", [])[-10:]

        # Build message history for OpenAI
        messages = [{"role": "system", "content": SLACK_CUSTOM_INSTRUCTIONS}]
        for msg in history:
            text = msg.get("text", "")
            sender = "assistant" if msg.get("user") == SLACK_BOT_USER_ID else "user"
            messages.append({"role": sender, "content": text})

        response = openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            reasoning_effort="low", # 추론 노력 (응답 시간과 비례할듯)
        )

        say(text=response.choices[0].message.content.strip(), thread_ts=thread_ts)

    except Exception as e:
        say(text=f"⚠️ Error: {str(e)}", thread_ts=thread_ts)




if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()