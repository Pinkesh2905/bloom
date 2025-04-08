from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatMessage
import json
import random
import pyjokes
from quote import quote
from datetime import datetime
from django.contrib.auth.decorators import login_required

# Chatbot homepage
@login_required
def chatbot_view(request):
    return render(request, 'chatbot/chatbot.html')

# Handle chat messages
@csrf_exempt
@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_msg = data.get('message', '').lower().strip()

        # Save user message
        ChatMessage.objects.create(sender="user", message=user_msg, user=request.user)

        # Generate reply
        bot_reply = get_bot_reply(user_msg)

        # Save bot message
        ChatMessage.objects.create(sender="bot", message=bot_reply, user=request.user)

        return JsonResponse({"reply": bot_reply})
    return JsonResponse({"error": "Invalid request"}, status=400)

# Bot logic
def get_bot_reply(user_msg):
    reply = "I'm still learning 🌱 Try words like 'stress', 'joke', 'quote', or 'hello'."

    if any(word in user_msg for word in ["joke", "funny", "laugh"]):
        reply = pyjokes.get_joke()
    elif any(word in user_msg for word in ["motivate", "motivation", "quote", "inspire"]):
        reply = random.choice([
            "You're amazing and you matter 💫",
            "Every day is a new beginning 🌄",
            "Believe you can and you're halfway there. – Theodore Roosevelt",
            "Push yourself, because no one else is going to do it for you.",
            "Dream it. Wish it. Do it.",
            "The harder you work for something, the greater you'll feel when you achieve it.",
            "Stay positive. Work hard. Make it happen.",
            "Don't watch the clock; do what it does. Keep going. ⏳",
            "You are stronger than you think. 💪",
            "Your mind is a powerful thing. When you fill it with positive thoughts, your life will start to change.",
            "Success doesn't just find you. You have to go out and get it.",
            "Difficult roads often lead to beautiful destinations. 🌸",
            "Start where you are. Use what you have. Do what you can.",
            "You don’t have to be perfect to be amazing.",
            "Stars can’t shine without darkness. ✨",
            "Take a deep breath. You’re doing great. 🌼",
            "You are capable of amazing things. Keep believing. 🌟",
            "It always seems impossible until it's done. – Nelson Mandela",
            "Small steps every day lead to big results. 🚶‍♂️➡️🏆",
            "You're not alone. You're doing great. Keep going. 💖"
        ])
    elif any(word in user_msg for word in ["hello", "hi", "hey"]):
        reply = "Hey there! I'm Bloom Bot 🌸 Here to chat anytime!"
    elif "sad" in user_msg:
        reply = "Let your emotions flow 💧 You're not alone."
    elif "stress" in user_msg:
        reply = "Breathe in... Breathe out... You got this 💪"
    elif "anxious" in user_msg:
        reply = "Focus on your breath and count 5 things you can see 👀"
    elif "bye" in user_msg:
        reply = "Take care! Come back whenever you want to talk 💖"
    elif "how are you" in user_msg:
        reply = "I am fine, how are you? I am here to help you with any questions or concerns you may have."
    elif "thanks" in user_msg:
        reply = "You're always welcome! 😊"

    return reply

# Fetch chat history
@login_required
def get_chat_history(request):
    history = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
    data = [
        {
            "sender": msg.sender,
            "message": msg.message,
            "timestamp": msg.timestamp.strftime('%H:%M')
        } for msg in history
    ]
    return JsonResponse({"history": data})

# Clear chat history
@csrf_exempt
@login_required
def clear_chat(request):
    if request.method == 'POST':
        ChatMessage.objects.filter(user=request.user).delete()
        return JsonResponse({"status": "cleared"})
    return JsonResponse({"error": "Invalid request"}, status=400)
