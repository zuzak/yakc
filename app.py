from flask import (Flask, send_from_directory, abort,
                   render_template, request, flash, redirect, g, jsonify)
from random import choice, random
from uuid import uuid4
import json
import logging
from hashlib import sha256
import shutil
import socket
import subprocess
import os
from time import strftime

from raven.contrib.flask import Sentry

app = Flask(__name__)
sentry = Sentry(app)


delta = 0


def map_ips(ip, default):
    return get_ips().get(ip, default)


def get_ips():
    with open('addresses.json') as fp:
        return json.load(fp)

git_version = subprocess.check_output(['git', 'describe', '--all', '--long'])[:-1].decode('utf-8')

def md5_to_file(md5):
    with open('webms/md5.txt', 'r') as fp:
        strings = fp.read()
        fp.close()
    if strings is not None:
        strings = strings.split('\n')
        for string in strings:
            string = string.split('  ')
            if md5 == string[0]:
                return string[1].split('/')[1]
    return False


def get_ip():
    if (request.environ.get('HTTP_X_REAL_IP')):
        return request.environ.get('HTTP_X_REAL_IP')
    elif request.environ.get('X-Forwarded-For'):
        return request.environ.get('X-Forwarded-For')
    else:
        return request.access_route[0]


def add_log(webm, action):
    global delta
    ip = get_user()
    string = strftime('%Y-%m-%d %H:%M:%S ' + ip + ' ' + action)
    with open('webms/metadata/' + webm, 'a') as logfile:
        logfile.write(string + '\n')
    print(str(delta) + ' ' + string + ' http://webm.website/' + webm)


def get_user():
    user = get_ip()
    user = map_ips(user, user)
    return user


def set_user(ip, user):
    ips = get_ips()
    blacklist = [
        ' ',
        'good',
        'demote',
        'held',
        'censure',
        'affirm',
        'feature',
        '.'
    ]
    if user in ips.values():
        return False

    if any(substr in user for substr in blacklist):
        return False

    ips[ip] = user

    with open('addresses.json', 'w') as fp:
        fp.write(json.dumps(ips))
    return True


def ban_user():
    with open('bans.txt', 'a') as fp:
        fp.write(get_ip()+'\n')


def user_banned():
    bans = open('bans.txt').read().splitlines()
    if get_ip() in bans:
        return True
    else:
        return False


@app.route('/settings/request-ban')
def request_ban():
    ban_user()
    return send_from_directory('webms', 'neil.jpg'), 201


def get_user_censured(webm):
    log = get_log(webm)
    if log is not None:
        user = get_user()
        log = log.split('\n')
        for line in log:
            if user in line:
                if 'censure' in line:
                    return True
                if 'demote' in line:
                    return True
    return False


def is_unpromotable(webm):
    if webm in get_best_webms():
        return 'already featured'
    if webm in get_vetoed_webms():
        return 'this video has been vetoed'
    user = get_user()
    if user.startswith('94.119'):
        return 'this shared IP address is banned'
    if user.startswith('('):
        return 'this shared IP address is banned'
    log = get_log(webm)
    if log is not None:
        log = log.split('\n')
        for line in log:
            if user in line:
                if 'marked good' in line:
                    return 'cannot feature own videos'
                if 'demoted' in line:
                    return 'you demoted this before!'
                if 'held' in line:
                    return 'you held this last time'
    return False


def is_votable(webm):
    user = get_user()
    log = get_log(webm)
    if log is not None:
        log = log.split('\n')
        for line in log:
            if user in line:
                if 'marked good' in line:
                    return 'cannot feature own videos'
                if 'demoted' in line:
                    return 'you demoted this before!'
                if 'censure' in line:
                    return 'you already censured'
                if 'affirm' in line:
                    return 'you already affirmed'
                if 'featured' in line:
                    return 'you featured this!'
    return False


def get_log(webm):
    try:
        fp = open('webms/metadata/' + webm, 'r')
        string = fp.read()
        fp.close()
        return string
    except IOError:
        return None


def get_name(webm):
    return os.path.splittext(webm)[0]


def generate_webm_token(webm, salt=None):
    if not salt:
        salt = uuid4().hex
    return sha256(app.secret_key.encode(
        ) + webm.encode() + salt.encode()).hexdigest() + ':' + salt


def get_all_webms():
    return os.listdir('webms/all')


def get_good_webms():
    return os.listdir('webms/good')


def get_music_webms():
    return os.listdir('webms/music')


def get_best_webms():
    return os.listdir('webms/best')


def get_vetoed_webms():
    return os.listdir('webms/veto')


def get_bad_webms():
    return os.listdir('webms/bad')


def get_safe_webms():
    return list(set(get_all_webms()) - set(get_trash_webms()))


def get_quality_webms():
    """Allows whitelisting of reports to stop the top-tier webms being 403'd"""
    return list(set(get_good_webms()).union(get_best_webms()))


def get_pending_webms():
    return list(set(get_safe_webms()) - set(get_good_webms()) -
                set(get_bad_webms()) - set(get_music_webms()))


def get_trash_webms():
    return os.listdir('webms/trash')


def get_held_webms():
    return os.listdir('webms/held')


def get_unheld_good_webms():
    return list(set(get_good_webms()) - set(get_held_webms()))


def get_stats():
    best = len(get_best_webms())
    return {
        'counts': {
            'good': (len(get_good_webms()) - best),
            'bad': len(get_bad_webms()),
            'music': len(get_music_webms()),
            'held': len(get_held_webms()),
            'best': best,
            'pending': len(get_pending_webms()),
            'trash': len(get_trash_webms()),
            'total': len(get_all_webms())
        },
        'version': str(git_version)
    }


def delete_holding_queue():
    shutil.rmtree('webms/held')
    os.makedirs('webms/held')


@app.route('/', subdomain='about')
@app.route('/', subdomain='privacy')
def privacy():
    return render_template(
        'privacypolicy.html',
        stats=get_stats(),
     user=get_user())


@app.route('/<name>.webm')
@app.route('/<name>.webm', subdomain='<domain>')
def serve_webm(name, domain=None):
    if request.accept_mimetypes.best_match(
            ['video/webm', 'text/html']) == 'text/html':
        return redirect(name)
    name = name + '.webm'
    if name not in get_all_webms():
        if metadata_exists(name):
            abort(410, 'This webm has been deleted.')
        else:
            abort(404, 'Cannot find that webm!')

    if name in get_trash_webms():
        if name not in get_quality_webms():
            add_log(name, 'was blocked from viewing')
            abort(403, 'webm was reported')

    add_log(name, 'viewed')
    return send_from_directory('webms/all', name)


def metadata_exists(webm):
    return os.path.isfile('webms/metadata/' + webm)


@app.route('/<name>', subdomain='<domain>')
@app.route('/<name>')
def show_webm(name, domain=None):
    name = name + '.webm'
    queue = 'pending'
    token = None
    if name not in get_all_webms():
        if metadata_exists(name):
            abort(410, "This webm has been deleted")
        else:
            abort(404, "No webm exists or has existed with that name")
    elif name not in get_safe_webms():
        if name not in get_quality_webms():
            abort(403)
    if name in get_best_webms():
        queue = 'best'
    elif name in get_music_webms():
        queue = 'music'
    elif name in get_good_webms():
        queue = 'good'
    elif name in get_bad_webms():
        queue = 'bad'
        token = generate_webm_token(name)

    return render_template(
        'display.html',
        webm=name,
        queue=queue,
        token=token,
     history=get_log(name))


@app.route('/md5/<md5>')
def serve_md5(md5):
    webm = md5_to_file(md5)
    if webm:
        return redirect(webm)
    else:
        abort(404, 'md5 match not found')


@app.route('/', subdomain='pending')
@app.route('/')
def serve_random():
    try:
        pending = get_pending_webms()
        webm = choice(pending)
    except IndexError:
        abort(404, 'no webms to show!')
        pass
    if user_banned():
        return send_from_directory('webms', 'neil.jpg'), 403
    return render_template(
        'display.html',
        webm=webm,
        token=generate_webm_token(webm),
        count=len(pending),
        history=get_log(webm),
        stats=get_stats(),
        unpromotable=is_unpromotable(webm),
     user=get_user())


@app.route('/', subdomain='decent')
def serve_good():
    global delta
    best = None
    held = 0
    try:
        good = get_unheld_good_webms()
        if len(good) == 0:
            delete_holding_queue()
            good = get_unheld_good_webms()
        else:
            held = len(get_held_webms())
        webm = choice(good)
        if webm in get_best_webms():
            best = True
    except IndexError:
        abort(404, 'You need to promote some webms!')
    return render_template(
        'display.html',
        webm=webm,
        token=generate_webm_token(webm),
        queue='good',
        count=len(good),
        best=best,
        held=held,
        unpromotable=is_unpromotable(webm),
        stats=get_stats(),
        history=get_log(webm),
        debug=u'\u0394'+str(delta),
     user=get_user())


@app.route('/', subdomain='new.decent')
def serve_unjudged_good():
    global delta
    best = None
    held = 0
    try:
        good = get_unheld_good_webms()
        if len(good) == 0:
            delete_holding_queue()
            good = get_unheld_good_webms()
        else:
            held = len(get_held_webms())
        webm = choice(good)
        if webm in get_best_webms():
            best = True
    except IndexError:
        abort(404, 'You need to promote some webms!')
    unpromotable = is_unpromotable(webm)
    if unpromotable:
        return redirect('/')
    else:
        return render_template(
            'display.html',
            webm=webm,
            token=generate_webm_token(webm),
            queue='good',
            count=len(good),
            best=best,
            held=held,
            unpromotable=is_unpromotable(webm),
            stats=get_stats(),
            history=get_log(webm),
            debug=u'\u0394'+str(delta),
            user=get_user())


@app.route('/', subdomain='good')
def redirect_to_held():
    return redirect('//decent.' + app.config['SERVER_NAME'])


@app.route('/', subdomain='held')
def serve_held():
    try:
        good = get_held_webms()
        webm = choice(good)
    except IndexError:
        abort(404, 'There are no held webms.')
    return render_template(
        'display.html',
        webm=webm,
        queue='decent',
        stats=get_stats(),
     history=get_log(webm))


@app.route('/', subdomain='best')
def serve_best():
    try:
        webm = choice(get_best_webms())
    except IndexError:
        abort(404, 'You need to feature some webms!')
    if get_user_censured(webm):
        return redirect('/', 302)
    token = generate_webm_token(webm)
    return render_template(
        'display.html',
        webm=webm,
        queue='best',
        token=token,
        unpromotable=is_votable(webm),
     user=get_user())


@app.route('/', subdomain='top')
def serve_best_nocensor():
    try:
        webm = choice(get_best_webms())
    except IndexError:
        abort(404, 'There are no featured webms.')
    token = generate_webm_token(webm)
    return render_template(
        'display.html',
        webm=webm,
        queue='best',
        token=token,
        history=get_log(webm),
     unpromotable=is_votable(webm))


@app.route('/', subdomain='music')
def serve_music():
    try:
        webms = get_music_webms()
        webm = choice(webms)
    except IndexError:
        abort(404, 'You need to shunt some videos!')
    token = generate_webm_token(webm)
    return render_template(
        'display.html',
        webm=webm,
        queue='music',
        token=token,
        history=get_log(webm),
     count=len(webms))


@app.route('/', subdomain='index')
def serve_best_index():
    webms = get_best_webms()
    return render_template('index.html', webms=webms)


@app.route('/', subdomain='bad')
def serve_bad():
    try:
        webms = get_bad_webms()
        webm = choice(webms)
    except IndexError:
        abort(404, 'No webms have been marked bad.')
    return render_template(
        'display.html',
        webm=webm,
        token=generate_webm_token(webm),
        queue='bad',
        count=len(webms),
     stats=get_stats())


def mark_good(webm):
    global delta
    add_log(webm, 'marked good')
    delta += 1
    os.symlink('webms/all/' + webm, 'webms/good/' + webm)


def mark_bad(webm):
    global delta
    if random() > 0.8:
        # For a small percentage of "bad" moves, don't actually do it
        # That way, some webms get a second chance
        add_log(webm, 'marked bad (placebo)')
    else:
        delta -= 1
        add_log(webm, 'marked bad')
        os.symlink('webms/all/' + webm, 'webms/bad/' + webm)


def mark_ugly(webm):
    global delta
    delta -= 5
    add_log(webm, 'reported')
    os.symlink('webms/all/' + webm, 'webms/trash/' + webm)


def mark_veto(webm):
    add_log(webm, 'vetoed')
    os.symlink('webms/all/' + webm, 'webms/veto/' + webm)


def mark_hold(webm):
    add_log(webm, 'held')
    os.symlink('webms/all/' + webm, 'webms/held/' + webm)


def unmark_good(webm):
    global delta
    delta -= 1
    add_log(webm, 'demoted')
    os.unlink('webms/good/' + webm)


def unmark_bad(webm):
    global delta
    delta += 1
    add_log(webm, 'forgiven')
    os.unlink('webms/bad/' + webm)


def mark_music(webm):
    global delta
    delta += 3
    os.unlink('webms/good/' + webm)
    os.symlink('webms/all/' + webm, 'webms/music/' + webm)
    add_log(webm, 'shunted')


def unmark_music(webm):
    global delta
    delta -= 3
    os.unlink('webms/music/' + webm)
    os.symlink('webms/all/' + webm, 'webms/good/' + webm)
    add_log(webm, 'unshunted')


def mark_best(webm):
    global delta
    delta += 5
    add_log(webm, 'featured ****')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(('http://best.webm.website/' + webm +
                 ' has been marked as "best" by ' + get_user()).encode(),
                ('saraneth.lon.fluv.net', 41337))
    os.symlink('webms/all/' + webm, 'webms/best/' + webm)


@app.route('/settings/change-nick', methods=['POST'])
def change_nick():
    nick = request.form['nick']
    user = get_user()

    ips = get_ips()
    if nick in ips.values():
        abort(400, 'duplicate nickname')

    if user in ips:
        abort(403, 'you have already set a nickname')

    if set_user(get_ip(), nick):
        flash('Set nickname to ' + get_user())
        return redirect('/')
    else:
        abort(400, 'unacceptable nickname')


@app.route('/moderate', methods=['POST'])
@app.route('/moderate', methods=['POST'], subdomain='<domain>')
def moderate_webm(domain=None):
    webm = request.form['webm']
    token = request.form['token'].split(':')
    if not (token[0] + ':' + token[1] == generate_webm_token(webm, token[1])):
        abort(400, 'token mismatch')

    verdict = request.form['verdict']

    status = None
    try:
        if verdict == 'good':
            status = mark_good(webm)
        elif verdict == 'bad':
            status = mark_bad(webm)
        elif verdict == 'shunt':
            if webm in get_good_webms():
                status = mark_music(webm)
            else:
                abort(400, 'can only shunt good webms')
        elif verdict == 'unshunt':
            if webm in get_music_webms():
                status = unmark_music(webm)
            else:
                abort(400, 'can only unshunt if shunted!')
        elif verdict == 'report':
            status = mark_ugly(webm)
        elif verdict == 'demote':
            if webm in get_good_webms():
                unmark_good(webm)
                flash('Demoted ' + webm)
                return redirect('/', 303)
            else:
                abort(400, 'can only demote good webms')
        elif verdict == 'feature':
            if is_unpromotable(webm):
                abort(400, 'not allowed to feature')
            if webm in get_good_webms():
                mark_best(webm)
                flash('Promoted ' + webm)
                return redirect('/', 303)
            else:
                abort(400, 'can only feature good webms')
        elif verdict == 'forgive':
            if webm in get_bad_webms():
                unmark_bad(webm)
                flash('Forgave ' + webm)
                return redirect('/', 303)
            else:
                abort(400, 'can only forgive bad webms')
        elif verdict == 'keep' or verdict == 'hold':
            if webm in get_unheld_good_webms():
                mark_hold(webm)
            return redirect('/')
        elif verdict == 'veto' or verdict == 'nsfw':
            if webm in get_good_webms():
                if webm not in get_best_webms():
                    mark_veto(webm)
                    return redirect('/', 303)
                else:
                    abort(400, 'cannot veto things already in best')
            else:
                abort(400, 'can only veto good webms')
        elif verdict == 'unsure':
            # placebo
            add_log(webm, 'skipped')
            return redirect('/')
        elif verdict == 'affirm' or verdict == 'censure':
            if not is_votable(webm):
                if webm in get_best_webms():
                    add_log(webm, verdict)
            else:
                abort(400, is_votable(webm))
        else:
            abort(400, 'invalid verdict')

        flash('Marked ' + webm + ' as ' + verdict)
        return redirect('/', '303')
    except OSError:  # file exists
        flash('Unable to mark ' + webm + ' as ' + verdict)
    return redirect('/')


@app.route('/stats.json', subdomain='api')
def api():
    return jsonify(get_stats())


@app.errorhandler(404)
@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(410)
def page_not_found(e):
    return render_template('error.html', e=e), e.code


@app.errorhandler(500)
def server_error(e):
    return render_template(
        'error.html', e=e, sentry=g.sentry_event_id,
        dsn=sentry.client.get_public_dsn('https')), 500

if __name__ == '__main__':

    required_dirs = [
        'webms',
        'webms/all',
        'webms/bad',
        'webms/best',
        'webms/good',
        'webms/held',
        'webms/metadata',
        'webms/music',
        'webms/trash',
        'webms/veto',
    ]
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # probably should make this persist
    app.config.update(
        SECRET_KEY=uuid4().hex,
        SERVER_NAME='webm.website',
        TEMPLATES_AUTO_RELOAD=True,
        SENTRY_CONFIG={
            'release': git_version
        }
    )

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.INFO)

    app.run(host='0.0.0.0', port=3000)
