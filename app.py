from flask import Flask, render_template, request
from pg_query import prettify

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello():
    result = ''
    if request.method == "POST":
        snippet = request.form['snippet']
        result = prettify(snippet)
    return render_template('index.html', results=result)


if __name__ == '__main__':
    app.run()
