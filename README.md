# PhoneMapServer

An similar idea to Google's MapReduce, but for phones.

# Setup

To get dependencies run `sudo ./build.sh`

Also make sure the configuration in config.py is correct for your machine, or (once we've implemented it) make sure
you've set the appropriate environment variables.

To get postgresql, run:

`sudo apt install postgresql`

Then in a terminal write:

`sudo -su postgres`

And then:

`createuser -P -s -e YOUR_USER`

(set some password of your choosing, say, YOUR_PW)

followed by:

`createdb -O YOUR_USER YOUR_DB_NAME`

and finally, to test:

`psql YOUR_USER  -h YOUR_HOST OUR_DB_NAME`

(you'll get a port number at this point, say, YOUR_PORT)

That's it! You can quit with:

`\q`

followed by ctrl-D to stop being the postgres user.

From there you'll want to edit your config.py so it has a line such as:

SQLALCHEMY_DATABASE_URI = `postgresql://YOUR_PASS:YOUR_PW@YOUR_HOST:YOUR_PORT/YOUR_DB_NAME`

Mine for example is:

SQLALCHEMY_DATABASE_URI = `postgresql://rob:[topsecretpw]@127.0.0.1:5432/phonemap`

# Running tests

Go into the PhoneMapServer directory and in terminal run `python3 -m "nose"`