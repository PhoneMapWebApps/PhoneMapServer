from werkzeug.utils import secure_filename


def get_todo_by_id(cursor, id_val):
    if isinstance(id_val, int):
        cursor.execute("""SELECT todo from test where id=%d;""".format(id_val))
        rows = cursor.fetchall()
        print(rows)
        return rows
    else:
        print("not of type string, possible SQL injection attack")
        return None

# doesnt do conn.commit() so wont publish changes
def test_db(cursor):
    try:
        cursor.execute("""CREATE TABLE test_table (name char(40));""")
        cursor.execute("""SELECT * FROM test_table;""")
        rows = cursor.fetchall()
        print(rows)

    except Exception as e:
        print("You made a mistake somewhere")
        print(e)


def add_to_db(conn, cursor, id_val, js_file, zip_file):

    js_filename = secure_filename(js_file.filename)
    zip_filename = secure_filename(zip_file.filename)

    if isinstance(id_val, int) and isinstance(js_filename, str) and isinstance(zip_filename, str):
        cursor.execute("""INSERT INTO test VALUES ({0}, '{1}', '{2}', False, '{{}}');""".format(str(id_val), js_filename, zip_filename))
        conn.commit()
    else:
        print("not of type string, possible SQL injection attack")
