from flask import Flask, send_from_directory, abort, render_template, request, flash, redirect
from random import choice
from uuid import uuid4
from hashlib import sha256
import os
app = Flask(__name__)


def get_name(webm):
    return os.path.splittext(webm)[0]

def generate_webm_token(webm, salt=None):
    if not salt:
        salt = uuid4().hex
    return sha256(app.secret_key.encode() + webm.encode() + salt).hexdigest() + ':' + salt

def get_all_webms():
    return os.listdir('webms/all')

def get_good_webms():
    return os.listdir('webms/good')

def get_bad_webms():
    return os.listdir('webms/bad')

def get_safe_webms():
    return list(set(get_all_webms()) - set(get_trash_webms()))

def get_pending_webms():
    return list(set(get_safe_webms()) - set(get_good_webms()) - set(get_bad_webms()))

def get_trash_webms():
    return os.listdir('webms/trash')

@app.route('/<name>.webm')
def serve_webm(name):
    if request.accept_mimetypes.best_match(['video/webm', 'text/html']) == 'text/html':
        return redirect(name)
    name = name + '.webm'
    if name not in get_all_webms():
        abort(404)

    if name in get_trash_webms():
        abort(403)

    return send_from_directory('webms/all', name)

@app.route('/<name>')
def show_webm(name):
    name = name + '.webm'
    queue = 'pending'
    if name not in get_safe_webms():
        abort(404)
    if name in get_good_webms():
        queue = 'good'
    elif name in get_bad_webms():
        queue = 'bad'

    return render_template('display.html', webm=name, queue=queue)

@app.route('/')
def serve_random():
    try:
        pending = get_pending_webms()
        webm = choice(pending)
    except IndexError:
        abort(404)
    return render_template('display.html', webm=webm, token=generate_webm_token(webm), count=len(pending))

@app.route('/good/')
@app.route('/', subdomain='good')
def serve_good():
    try:
        webm = choice(get_good_webms())
    except IndexError:
        abort(404)
    return render_template('display.html', webm=webm, queue='good')

@app.route('/bad/')
@app.route('/', subdomain='bad')
def serve_bad():
    try:
        webm = choice(get_bad_webms())
    except IndexError:
        abort(404)
    return render_template('display.html', webm=webm, token=generate_webm_token(webm), queue='bad')

def mark_good(webm):
    os.symlink('webms/all/'+webm, 'webms/good/'+webm)

def mark_bad(webm):
    os.symlink('webms/all/'+webm, 'webms/bad/'+webm)

def mark_ugly(webm):
    os.symlink('webms/all/'+webm, 'webms/trash/'+webm)

@app.route('/moderate', methods=['POST'])
def moderate_webm():
    webm = request.form['webm']
    token = request.form['token'].split(':')
    if not ( token[0]+':'+token[1] == generate_webm_token(webm, token[1]) ):
        abort(400)

    verdict = request.form['verdict']

    status = None
    try:
        if verdict == 'good':
            status = mark_good(webm)
        elif verdict == 'bad':
            status = mark_bad(webm)
        elif verdict == 'report':
            status = mark_ugly(webm)
        else:
            abort(400)

        flash('Marked ' + webm + ' as ' + verdict)
        return redirect('/', '303')
    except OSError:  # file exists
        flash('Unable to mark ' + webm + ' as ' + verdict)
    return redirect('/')




if __name__ == '__main__':
    # probably should make this persist
    app.secret_key = uuid4().hex

    required_dirs = [
        'webms'
        'webms/good',
        'webms/bad',
        'webms/trash'
    ]
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)

    app.run(host='0.0.0.0', port=3000)

