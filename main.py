from flask import Flask, render_template, request, redirect

app = Flask(__name__)

entries = []

@app.route("/", methods=["GET"])
def home():
    Balance = sum(float(e) for e in entries) if entries else 0
    return render_template("index.html", entries=entries, Balance=Balance)

@app.route("/moneh-enter", methods=["POST"])
def submit():
    title = request.form['title']
    if title:  
        try:
            entries.append(float(title))
        except ValueError:
            pass  
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
