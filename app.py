import os, io, zipfile, uuid
from flask import Flask, render_template, request, send_file, session, url_for
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Créer le dossier static si besoin
os.makedirs("static", exist_ok=True)
os.makedirs("fonts", exist_ok=True)

# Mapping polices
FONTS = {
    "Arial": "fonts/arial.ttf",
    "Comic": "fonts/comic.ttf",
    "Futurist": "fonts/futurist.ttf"
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        prompt = request.form["prompt"]
        texte = request.form.get("texte", "").strip()
        style = request.form.get("style", "")
        police = request.form.get("police", "Arial")
        position = request.form.get("position", "bas")

        full_prompt = f"{prompt}, style {style}" if style else prompt
        response = openai.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        image_bytes = requests.get(image_url).content
        image = Image.open(io.BytesIO(image_bytes))

        image_id = str(uuid.uuid4())
        filename = f"{image_id}.png"
        img_path = f"static/{filename}"

        # Ajouter texte
        if texte:
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(FONTS[police], 32)
            w, h = image.size
            tw, th = draw.textsize(texte, font=font)

            pos = {
                "haut": (w/2 - tw/2, 20),
                "centre": (w/2 - tw/2, h/2 - th/2),
                "bas": (w/2 - tw/2, h - th - 20)
            }.get(position, (20, 20))

            draw.text(pos, texte, font=font, fill=(255, 255, 255))

        image.save(img_path)

        # Historique session
        if "history" not in session:
            session["history"] = []
        session["history"].append({
            "image": filename,
            "prompt": prompt,
            "texte": texte,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        # Génération zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr("infos.txt", f"Prompt: {prompt}\nTexte: {texte}")
            with open(img_path, "rb") as f:
                zipf.writestr(filename, f.read())
        zip_buffer.seek(0)

        return send_file(zip_buffer, as_attachment=True, download_name="image_trhacknon.zip", mimetype="application/zip")

    return render_template("index.html", fonts=FONTS.keys())

@app.route("/history")
def history():
    return render_template("history.html", history=session.get("history", []))
