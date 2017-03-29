# yakc

# Overview

This website displays a random webm from a large collection, and asks
users if they are good or bad, and moves them to various different
subdomains according to their answers.

For example, a new webm is placed in "pending", and is available at `webm.website`. A user can tell us it is "bad", which moves the video to `bad.webm.website`. Alternatively, they can say it is "good", which
moves the video to `decent.webm.website`, where further routes are available,
such as moving the video to a dedicated music queue, holding it temporarily
immune from further movements, or featuring it as one of the best videos on the
site.

Users can also report particularly bad webms, which will immediately
remove them from rotation and prevent them from being served.


# Usage
Run as *e.g.* `WEBM_CONFIG=settings.cfg python3 app.py`.

Example settings file:
```python
# vim:ft=python
SERVER_NAME="webm.website"
PORT=3000
DEBUG=False
NO_ANONYMIZE=False  # non-true values cause usernames in API to be hidden
```

Dependencies are `flask`, `flask_cors`, `raven`, and `blinker`.

If you are getting a 404 on `/`, ensure `SERVER_NAME` is set.
It's required to get subdomains to work. For local development,
I set lines like `127.0.0.1 webm.local best.webm.local` in my `/etc/hosts/`
and set `webm.local` as my `SERVER_NAME`. You can't use `localhost` as it
doesn't support subdomains.

Required directories are created on first run.
You can seed some webms by doing `cd webms && ./api.py` for a few moments.

For MD5 lookup to work, you need to precompute the hashes.
To do so, run `md5sum all/*.webm | tee md5.txt`. This isn't an often
used feature, and most of the app will run fine without it.

# Contributing
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/609f8fbe1f6944c097f9fbb9eec852ac)](https://www.codacy.com/app/douglas/yakc?utm_source=github.com&utm_medium=referral&utm_content=zuzak/yakc&utm_campaign=badger)
Pull requests and filed issues are welcomed.
Code is available under the ISC licence, which is similar to the MIT licence.
