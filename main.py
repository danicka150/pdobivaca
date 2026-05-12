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
<title>OSINT</title>

<style>
body{
    background:#111;
    color:white;
    font-family:Arial;
    padding:30px;
}

input{
    width:350px;
    padding:14px;
    border:none;
    border-radius:12px;
    background:#1f1f1f;
    color:white;
    font-size:18px;
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
    background:#1b1b1b;
    margin-top:20px;
    padding:20px;
    border-radius:15px;
}

.line{
    margin:10px 0;
}
</style>
</head>

<body>

<h1>OSINT SEARCH</h1>

<input id="query" placeholder="+7705... or username">
<button onclick="search()">Search</button>

<div id="result"></div>

<script>
async function search(){

    let query = document.getElementById("query").value;

    let res = await fetch("/api/search?q=" + encodeURIComponent(query));
    let data = await res.json();

    let html = `<div class="card">`;

    if(data.phone.valid){

        html += `
        <div class="line"><b>PHONE:</b> ${data.phone.input}</div>
        <div class="line"><b>COUNTRY:</b> ${data.phone.country}</div>
        <div class="line"><b>OPERATOR:</b> ${data.phone.operator}</div>
        <div class="line"><b>FORMAT:</b> ${data.phone.format}</div>
        `;
    }

    if(data.username){

        html += `
        <div class="line"><b>USERNAME:</b> ${data.username}</div>
        `;
    }

    if(data.accounts.length > 0){

        html += `<h3>ACCOUNTS</h3>`;

        data.accounts.forEach(acc => {

            html += `
            <div class="line">
            ${acc.site}: ${acc.url}
            </div>
            `;
        });
    }

    html += `</div>`;

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
            "valid": False,
            "input": q,
            "country": "",
            "operator": "",
            "format": ""
        },
        "username": None,
        "accounts": []
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

            result["phone"]["format"] = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )

    except:
        pass

    # USERNAME
    username = re.sub(r'[^a-zA-Z0-9_.]', '', q)

    if len(username) >= 3:

        result["username"] = username

        sites = [
            ("Instagram", f"https://instagram.com/{username}"),
            ("TikTok", f"https://tiktok.com/@{username}"),
            ("Telegram", f"https://t.me/{username}"),
            ("GitHub", f"https://github.com/{username}"),
            ("YouTube", f"https://youtube.com/@{username}"),
            ("Twitter/X", f"https://x.com/{username}"),
            ("Reddit", f"https://reddit.com/user/{username}"),
            ("Twitch", f"https://twitch.tv/{username}"),
            ("Pinterest", f"https://pinterest.com/{username}"),
            ("Steam", f"https://steamcommunity.com/id/{username}")
        ]

        for site, url in sites:

            result["accounts"].append({
                "site": site,
                "url": url
            })

    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
