from flask import flash

def flashprint(s):
    flash(s)
    print(s)
