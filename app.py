
import logging
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from google import genai

load_dotenv()

app = Flask(__name__, static_folder=None)
logging.basicConfig(level=logging.INFO)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)


@app.get("/")
def home():
    return send_from_directory(app.root_path, "index.html")


@app.get("/style.css")
def stylesheet():
    return send_from_directory(app.root_path, "style.css")


@app.get("/script.js")
def javascript():
    return send_from_directory(app.root_path, "script.js")


@app.get("/images/<path:filename>")
def images(filename):
    image_folder = os.path.join(app.root_path, "images")
    return send_from_directory(image_folder, filename)


@app.get("/api/weather")
def get_weather():
    city = request.args.get("city", "").strip()

    if not city:
        return jsonify({"message": "Please enter a city name."}), 400

    if len(city) > 100:
        return jsonify({"message": "City name is too long."}), 400

    if not OPENWEATHER_API_KEY:
        return jsonify({
            "message": "OpenWeatherMap API key is missing from .env."
        }), 503

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            },
            timeout=10
        )

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code == 404:
            return jsonify({
                "message": "City not found. Check the spelling."
            }), 404

        if response.status_code == 401:
            app.logger.error("OpenWeatherMap API key was rejected.")
            return jsonify({
                "message": "OpenWeatherMap API key is invalid or inactive."
            }), 502

        if not response.ok:
            return jsonify({
                "message": "Weather service is temporarily unavailable."
            }), 502

        return jsonify(data)

    except requests.RequestException:
        app.logger.exception("Weather API request failed.")
        return jsonify({
            "message": "Could not connect to the weather service."
        }), 502


@app.post("/api/assistant")
def weather_assistant():
    if gemini_client is None:
        return jsonify({
            "error": "Gemini API key is missing from .env."
        }), 503

    body = request.get_json(silent=True) or {}
    question = body.get("question", "")
    weather = body.get("weather", {})

    if not isinstance(question, str) or not question.strip():
        return jsonify({
            "error": "Please enter a question."
        }), 400

    if len(question) > 1000:
        return jsonify({
            "error": "Keep your question under 1000 characters."
        }), 400

    if not isinstance(weather, dict):
        return jsonify({
            "error": "Weather data is invalid. Search for a city again."
        }), 400

    safe_weather = {
        "city": str(weather.get("city", "Unknown"))[:100],
        "temperature_c": weather.get("temperature_c"),
        "condition": str(weather.get("condition", "Unknown"))[:100],
        "humidity_percent": weather.get("humidity_percent"),
        "wind_speed_kmh": weather.get("wind_speed_kmh")
    }

    prompt = f"""
You are a friendly assistant inside a weather application.

Answer the user's question in simple, clear language.
Use the provided current weather data when relevant.
Do not invent current conditions or forecast information.
This data describes current conditions, not a forecast.
If a forecast is requested but not provided, explain that limitation.

Current weather data:
{safe_weather}

User question:
{question.strip()}
"""

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        answer = response.text

        if not answer:
            return jsonify({
                "error": "Gemini returned an empty answer. Please try again."
            }), 502

        return jsonify({"answer": answer})

    except Exception:
        app.logger.exception("Gemini API request failed.")
        return jsonify({
            "error": (
                "Gemini is temporarily unavailable. Check your API key, "
                "model access, internet connection and quota."
            )
        }), 502


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
