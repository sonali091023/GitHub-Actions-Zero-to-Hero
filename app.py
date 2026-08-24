from flask import Flask, jsonify, render_template

app = Flask(__name__)

#@app.route("/")               #Basic application response
#def home():
#    return "Hello from Flask application!"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")         #Health-check endpoint for Kubernetes probes
def health():
    return jsonify({
        "status": "UP"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80) 
    #Allows the app to be accessed outside the container & 8080 is application port