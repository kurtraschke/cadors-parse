from flask import g
import cryptacular.core
import cryptacular.bcrypt
import cryptacular.pbkdf2


def set_password(username, password):
    g.db.hset('users:' + username, 'password', get_delegator().encode(password))


def verify(username, password):
    if not g.db.hexists('users:' + username, 'password'):
        return False
    else:
        return get_delegator().check(g.db.hget('users:' + username, 'password'), password,
                                     setter=lambda hash: g.db.hset('users:' + username, 'password', hash))


def get_delegator():
    bcrypt = cryptacular.bcrypt.BCRYPTPasswordManager()
    pbkdf2 = cryptacular.pbkdf2.PBKDF2PasswordManager()
    delegator = cryptacular.core.DelegatingPasswordManager(preferred=bcrypt, fallbacks=(pbkdf2,))
    return delegator
