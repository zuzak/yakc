from flask import Flask, send_from_directory, abort, render_template
from random import choice
import os
app = Flask(__name__)

def get_all_webms():
    return os.listdir('webms/all')

def get_safe_webms():
    return list(set(get_all_webms()) - set(get_trash_webms()))

def get_trash_webms():
    return os.listdir('webms/trash')

@app.route('/<name>.webm')
def serve_webm(name):
    name = name + '.webm'
    if name not in get_all_webms():
        abort(404)

    if name in get_trash_webms():
        abort(403)

    return send_from_directory('webms/all', name)

@app.route('/')
def serve_random():
    return render_template('display.html', webm=choice(get_safe_webms()))


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=6667)

