from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import phonenumbers
from phonenumbers import geocoder, carrier
import uvicorn

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
    <title>OSINT Search</title>
    <meta charset="utf-8">
    <style>
        body{
            background:#111;
            color:white;
            font-family:Arial;
            padding:40px;
        }

        input{
            width:300px;
            padding:12px;
            border:none;
            border-radius:10px;
            font-size:18px;
        }

        button{
            padding:12px 20px;
            border:none;
            border-radius:10px;
            background:#00aa55;
            color:white;
            font-size:18px;
            cursor:pointer;
        }

        .card{
            margin-top:20px;
            background:#1e1e1e;
            padding:20px;
            border-radius:15px;
        }

        a{
            color:#66ccff;
        }
    </style>
</head>
<body>

<h1>Phone OSINT</h1>

<input id="phone" placeholder="+7705...">
<button onclick="search()">Search</button>

<div id="result"></div>

<script>
async function search(){

    let phone = document.getElementById("phone").value;

    let res = await fetch("/api/search?phone=" + encodeURIComponent(phone));
    let data = await res.json();

    let html = "";

    if(data.valid){

        html += `
        <div class="card">
            <h2>Result</h2>
            <p><b>Phone:</b> ${data.input}</p>
            <p><b>Country:</b> ${data.country}</p>
            <p><b>Operator:</b> ${data.operator}</p>

            <h3>Search Links</h3>
        `;

        data.google_search.forEach(s => {
            html += `<p><a href="${s.url}" target="_blank">${s.query}</a></p>`;
        });

        html += "</div>";

    }else{
        html = `<div class="card">Invalid number</div>`;
    }

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
async def search(phone: str):

    result = {
        "input": phone,
        "valid": False,
        "country": None,
        "operator": None,
        "google_search": []
    }

    try:

        parsed = phonenumbers.parse(phone)

        if phonenumbers.is_valid_number(parsed):

            result["valid"] = True

            result["country"] = geocoder.description_for_number(
                parsed,
                "en"
            )

            result["operator"] = carrier.name_for_number(
                parsed,
                "en"
            )

            normalized = phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )

            queries = [
                f'"{normalized}"',
                f'"{phone}"'
            ]

            for q in queries:

                url = (
                    "https://www.google.com/search?q="
                    + q.replace(" ", "+")
                )

                result["google_search"].append({
                    "query": q,
                    "url": url
                })

    except Exception as e:
        result["error"] = str(e)

    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
