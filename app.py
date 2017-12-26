from flask import Flask, render_template, request
from parser import Parser


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello():
    result = {}
    errors = []

    if request.method == "POST":
        snippet = request.form['snippet']
        try:
            parser = Parser()
            result = parser.process(snippet)
        except Exception:
            errors.append("Error while parsing the snippet, please try again!")
            return render_template('index.html', errors=errors)

    return render_template('index.html', errors=errors, results=result)


if __name__ == '__main__':
    app.run()
