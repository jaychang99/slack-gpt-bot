import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from openai import OpenAI, OpenAIError

# Load environment variables
load_dotenv()

DEFAULT_SYSTEM_INSTRUCTIONS = "You are a helpful assistant inside Slack. Keep responses helpful but concise."
DEFAULT_OPENAI_MODEL = "gpt-5-nano"
DEFAULT_OPENAI_SEARCH_MODEL = "gpt-4o-mini-search-preview"
DEFAULT_OPENAI_REASONING_EFFORT = "low"
DEFAULT_CONTEXT_WINDOW = 10
DEFAULT_OPENAI_SEARCH_REQUIRED_IDENTIFIER = "SLACK_BOT_WEB_SEARCH_REQUIRED"

# Env vars
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_CUSTOM_INSTRUCTIONS = os.getenv("SLACK_CUSTOM_INSTRUCTIONS", DEFAULT_SYSTEM_INSTRUCTIONS)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
OPENAI_SEARCH_MODEL = os.getenv("OPENAI_SEARCH_MODEL", DEFAULT_OPENAI_SEARCH_MODEL)
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", DEFAULT_OPENAI_REASONING_EFFORT)
OPENAI_CONTEXT_WINDOW = int(os.getenv("OPENAI_CONTEXT_WINDOW", DEFAULT_CONTEXT_WINDOW))
OPENAI_SEARCH_REQUIRED_IDENTIFIER = os.getenv("OPENAI_SEARCH_REQUIRED_IDENTIFIER", DEFAULT_OPENAI_SEARCH_REQUIRED_IDENTIFIER)

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
        history = slack_client.conversations_replies(channel=channel, ts=thread_ts).get("messages", [])[-OPENAI_CONTEXT_WINDOW:]

        # Build message history for OpenAI
        messages = [{"role": "system", "content": SLACK_CUSTOM_INSTRUCTIONS}]
        for msg in history:
            text = msg.get("text", "")
            sender = "assistant" if msg.get("user") == SLACK_BOT_USER_ID else "user"
            messages.append({"role": sender, "content": text})

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            reasoning_effort=OPENAI_REASONING_EFFORT, # 추론 노력 (응답 시간과 비례할듯) # GPT-4o-mini-search-preview 모델에서 지원 안함
        )
        
        if OPENAI_SEARCH_REQUIRED_IDENTIFIER in response.choices[0].message.content:
            # If search is required, use the search model
            response = openai_client.chat.completions.create(
                model=OPENAI_SEARCH_MODEL,
                messages=messages,
            )
            
            # add (Used web search) to the end of the response
            response.choices[0].message.content += "\n\n🌐 (Used web search)"
            

        say(text=response.choices[0].message.content.strip(), thread_ts=thread_ts)

    except Exception as e:
        say(text=f"⚠️ Error: {str(e)}", thread_ts=thread_ts)




if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()