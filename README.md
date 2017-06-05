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

SQLALCHEMY_DATABASE_URI = `postgresql://YOUR_USER:YOUR_PW@YOUR_HOST:YOUR_PORT/YOUR_DB_NAME`

Mine for example is:

SQLALCHEMY_DATABASE_URI = `postgresql://rob:[topsecretpw]@127.0.0.1:5432/phonemap`

# Running Tests

Go into the PhoneMapServer directory and in terminal run `python3 -m "nose"`

# Current API endpoints:

`connect`: The usual socketio call; required to initiate . Emits a `my_response` with `data` saying `CON_OK`.

`disconnect`: What is a connection without a disconnection?

`my_ping`: Used by the JS front end to calculate the response time. Responds with `my_pong`.

`my_event`: A standard call. Not used for anything, echos whatever you send it under `my_response`. Useful for the JS frontend.

`my_broadcast_event`: Similar to `my_event`, but echos the message over all devices. Still uses `my_response`.

`get_code`: Responds a `set_code` with some `code` and `data` as args, which consists of the JS code to be executed and the data to be crunched.
This will return the next data to be crunched for the oldest task.
May also respond with a `no_tasks` in the event that no more tasks are available.

`get_latest_code`: Responds in the same way as `get_code`, but will with the data for the latest newest task as opposed to the oldest.

`get_code_by_id`: Same response as `gget_code`. Must be sent with a `task_id` arg so as to specify which task is desired, instead of first/last which are obtained with `get_code` and `get_latest_code`.

`start_code`: Marks the code as started in the database. required for submission, and should follow a successful `get_code` call.
May respond with a `stop_executing` in unexpected scenarios; eg the code you have just started has already been 
completed, or if you haven't requested code to execute yet (which would be very confusing indeed).

`execution_failed`: Informs the server the currently running code has failed to execute.

`return`: Marks the completed crunching of a piece of data, updating the database appropriately. 
Also broadcasts the result under `my_response`, as usual.

`get_task_list`: Returns a `task_list` with arg `list` containing a list of JSON data for each task.

_Note_: In the event of an error, `error` may be emitted, which means the server has attempted to gracefully recover 
and tried to inform you of the error under the `error` argument.