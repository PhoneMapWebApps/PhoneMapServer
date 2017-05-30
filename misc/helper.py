from flask import flash

def flashprint(s):
    flash(s)
    print(s)

# TODO: actually get a real proper non-joke ID
def get_some_id():
    return 42
