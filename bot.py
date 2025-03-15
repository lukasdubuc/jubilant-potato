from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Railway!"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
