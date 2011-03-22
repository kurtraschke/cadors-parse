from cadorsfeed import db
from cadorsfeed.aerodb import lookup
from flask import current_app as app

def import_blacklist():
    with app.open_resource('aerodb/blacklist.txt') as blacklist:
        for line in blacklist:
            line = line.strip()
            if not line.startswith('#') and len(line) == 3:
                aerodrome = lookup(line)
                if aerodrome is not None:
                    aerodrome.blacklist = True
    db.session.commit()

