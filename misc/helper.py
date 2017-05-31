from flask import flash

def flashprint(s):
    #TODO this breaks the tests that should work without server on.. flash(s)
    print(s)

# TODO: actually get a real proper non-joke ID
def get_some_id():
    return 42
