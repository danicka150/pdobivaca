from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import phonenumbers
from phonenumbers import geocoder, carrier
import uvicorn
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>OSINT Search</title>

<style>
body{
    background:#0f0f0f;
    color:white;
    font-family:Arial;
    padding:30px;
}

input{
    width:350px;
    padding:14px;
    border:none;
    border-radius:12px;
    font-size:18px;
    background:#1f1f1f;
    color:white;
}

button{
    padding:14px 20px;
    border:none;
    border-radius:12px;
    background:#00aa55;
    color:white;
    font-size:18px;
    cursor:pointer;
}

.card{
    background:#1a1a1a;
    margin-top:20px;
    padding:20px;
    border-radius:15px;
}

a{
    color:#66ccff;
    text-decoration:none;
}

h1,h2,h3{
    margin-top:0;
}
</style>
</head>

<body>

<h1>Phone / Username OSINT</h1>

<input id="query" placeholder="+7705... or username">
<button onclick="search()">Search</button>

<div id="result"></div>

<script>
async function search(){

    let query = document.getElementById("query").value;

    let res = await fetch("/api/search?q=" + encodeURIComponent(query));
    let data = await res.json();

    let html = "";

    html += `
    <div class="card">
    <h2>Result</h2>
    `;

    if(data.phone.valid){

        html += `
        <p><b>Phone:</b> ${data.phone.input}</p>
        <p><b>Country:</b> ${data.phone.country}</p>
        <p><b>Operator:</b> ${data.phone.operator}</p>
        `;
    }

    if(data.username){

        html += `
        <p><b>Username:</b> ${data.username}</p>
        `;
    }

    html += "<h3>Public Search</h3>";

    data.links.forEach(link => {
        html += `
        <p>
            <a href="${link.url}" target="_blank">
                ${link.name}
            </a>
        </p>
        `;
    });

    html += "</div>";

    document.getElementById("result").innerHTML = html;
}
</script>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML

@app.get("/api/search")
async def search(q: str):

    result = {
        "phone": {
            "input": q,
            "valid": False,
            "country": None,
            "operator": None
        },
        "username": None,
        "links": []
    }

    # PHONE INFO
    try:

        parsed = phonenumbers.parse(q)

        if phonenumbers.is_valid_number(parsed):

            result["phone"]["valid"] = True

            result["phone"]["country"] = geocoder.description_for_number(
                parsed,
                "en"
            )

            result["phone"]["operator"] = carrier.name_for_number(
                parsed,
                "en"
            )

            normalized = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )

            phone_queries = [
                ("Google Exact", f'https://google.com/search?q="{normalized}"'),
                ("Yandex Search", f'https://yandex.ru/search/?text="{normalized}"'),
                ("Telegram Search", f'https://t.me/{normalized.replace("+","")}'),
                ("WhatsApp Check", f'https://wa.me/{normalized.replace("+","")}'),
            ]

            for name, url in phone_queries:
                result["links"].append({
                    "name": name,
                    "url": url
                })

    except:
        pass

    # USERNAME SEARCH
    username = re.sub(r'[^a-zA-Z0-9_.]', '', q)

    if len(username) >= 3:

        result["username"] = username

        username_sites = [
            ("Instagram", f"https://instagram.com/{username}"),
            ("TikTok", f"https://tiktok.com/@{username}"),
            ("GitHub", f"https://github.com/{username}"),
            ("Telegram", f"https://t.me/{username}"),
            ("YouTube", f"https://youtube.com/@{username}"),
            ("Twitter/X", f"https://x.com/{username}"),
            ("Reddit", f"https://reddit.com/user/{username}"),
            ("Twitch", f"https://twitch.tv/{username}"),
            ("Pinterest", f"https://pinterest.com/{username}"),
            ("Steam", f"https://steamcommunity.com/id/{username}")
        ]

        for name, url in username_sites:

            result["links"].append({
                "name": name,
                "url": url
            })

    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)

