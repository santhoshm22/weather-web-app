
const weatherForm = document.querySelector("#weather-form");
const cityInput = document.querySelector("#city-input");
const searchButton = document.querySelector("#search-button");
const weatherStatus = document.querySelector("#weather-status");
const weatherResult = document.querySelector("#weather-result");

const aiForm = document.querySelector("#ai-form");
const aiQuestion = document.querySelector("#ai-question");
const aiButton = document.querySelector("#ai-button");
const aiStatus = document.querySelector("#ai-status");
const aiAnswer = document.querySelector("#ai-answer");

let currentWeather = null;

const weatherIcons = {
    Clear: "/images/clear.png",
    Clouds: "/images/clouds.png",
    Rain: "/images/rain.png",
    Drizzle: "/images/drizzle.png",
    Mist: "/images/mist.png",
    Haze: "/images/mist.png",
    Fog: "/images/mist.png",
    Smoke: "/images/mist.png",
    Snow: "/images/snow.png",
    Thunderstorm: "/images/rain.png"
};

weatherForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const city = cityInput.value.trim();

    if (!city) {
        weatherStatus.textContent = "Please enter a city name.";
        return;
    }

    searchButton.disabled = true;
    weatherStatus.textContent = "Loading weather...";
    weatherResult.hidden = true;
    currentWeather = null;

    try {
        const response = await fetch(
            "/api/weather?city=" + encodeURIComponent(city)
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Unable to load weather.");
        }

        currentWeather = {
            city: data.name,
            temperature_c: data.main.temp,
            condition: data.weather[0].main,
            humidity_percent: data.main.humidity,
            wind_speed_kmh: Math.round(data.wind.speed * 3.6)
        };

        document.querySelector("#city-name").textContent = data.name;
        document.querySelector("#temperature").textContent =
            Math.round(data.main.temp) + "°C";
        document.querySelector("#condition").textContent =
            data.weather[0].description;
        document.querySelector("#humidity").textContent =
            data.main.humidity + "%";
        document.querySelector("#wind").textContent =
            Math.round(data.wind.speed * 3.6) + " km/h";
        document.querySelector("#high-low").textContent =
            Math.round(data.main.temp_max) + "° / " +
            Math.round(data.main.temp_min) + "°";

        const iconPath = weatherIcons[data.weather[0].main];

        if (iconPath) {
            document.querySelector("#weather-icon").src = iconPath;
        } else {
            document.querySelector("#weather-icon").src =
                "/images/clear.png";
        }

        weatherResult.hidden = false;
        weatherStatus.textContent = "";
        aiStatus.textContent = "";
        aiAnswer.textContent = "";

    } catch (error) {
        weatherStatus.textContent = error.message;
    } finally {
        searchButton.disabled = false;
    }
});

aiForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const question = aiQuestion.value.trim();

    if (!question) {
        aiStatus.textContent = "Please enter a question.";
        return;
    }

    if (!currentWeather) {
        aiStatus.textContent =
            "Search for a city and load its weather first.";
        return;
    }

    aiButton.disabled = true;
    aiStatus.textContent = "Gemini is thinking...";
    aiAnswer.textContent = "";

    try {
        const response = await fetch("/api/assistant", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                weather: currentWeather
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Unable to get an AI response."
            );
        }

        aiAnswer.textContent = data.answer;
        aiStatus.textContent = "Answer received.";

    } catch (error) {
        aiStatus.textContent =
            error.message || "The AI assistant is unavailable.";
    } finally {
        aiButton.disabled = false;
    }
});
