from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    TextMessageContent
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ShowLoadingAnimationRequest
)
from openai import OpenAI
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
GPT_API_KEY = os.getenv("GPT_API_KEY")
    
line_handler = WebhookHandler(CHANNEL_SECRET)

configuration = Configuration(
    access_token=CHANNEL_ACCESS_TOKEN
)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_messsage(event):
    messages = [TextMessage(text=reply_GPT_message(event))]
    # messages = [TextMessage(text=event.message.text)]
    return reply_message(event, messages)
    
@line_handler.add(FollowEvent)
def handle_follow(event):
    play_animation(event)
    messages = [TextMessage(text="歡迎加入我的AI-LINE-BOT，您可以詢問我任何問題，我會盡力回答您！")]
    return reply_message(event, messages)
    
def reply_message(event, messages):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=messages
            )
        )
        
import openai

def reply_GPT_message(event):
    play_animation(event)
    openai.api_key = GPT_API_KEY
    user_message = event.message.text

    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {
                "role": "system",
                "content": "你是一個來自台灣的AI機器人，需要回答我的問題請使用繁體中文。"
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        max_tokens=1000,
        temperature=0.2
    )
    return completion.choices[0].message.content
        
def play_animation(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.show_loading_animation(
            ShowLoadingAnimationRequest(
                chatId=event.source.user_id,
                loadingSeconds=10
            )
        )
        
if __name__ == "__main__":
    app.run()