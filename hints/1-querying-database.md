# Hint 1

A main part of this project involves interacting with a SQL database from Python. Let's take a look at how to do that.

## Connection

First thing you have to do is having an open connection to the database. This part is already implemented for you in the project, but in any case this is the way how you can do it.

```python
db = sqlite3.connect("/path/to/the/db/file.db")
```

As simple as that, just providing the proper path to the DB file. Note that the returned object (`db` in this case) is the connection handler. You will have to use this object to make further queries to the database. So, it's a good idea to keep reference to it. You will notice that in the project we store this connection handler in the global Flask object `g`, as `g.db`.

## Fetching data

The simplest action to perform in a database is a `SELECT` query. It will fetch data from certain table an return it to you. To perform `SELECT` queries (or any SQL query in general), you can use the `execute()` function of the connection object:

```python
cursor = d.db.execute('SELECT * FROM user;')

for row in cursor.fetchall():
    # do something
    pass
```

The result of the query, named as `cursor`, is an iterable object representing the fetched information from the database. Each element in the cursor will represent a row in the queried table.

When you are sure that the result of the query will bring one single result, for example when querying for one particular object id, you can use the `fetchone()` method instead.

```python
cursor = d.db.execute('SELECT * FROM user WHERE id=1;')
tweet = cursor.fetchone()
print(tweet)
# (1, 10, u'2017-04-13 23:14:31', u'Hello World!')
```

At some point you will need to filter you queries using the `WHERE` clause, using the parameters the user submitted (example: username and password during the login). To avoid [SQL injection](https://en.wikipedia.org/wiki/SQL_injection), there's a special syntax to send arguments to the `execute()` method.

```python
cursor = g.db.execute(
    'SELECT id, password FROM user WHERE username=:username;',
    {'username': username})
user = cursor.fetchone()
```

Note that `:username` placeholder in the SQL query will be replaced by the value provided in the dictionary of arguments also sent to the `execute()` function.

## Inserting data

In a similar way to the `SELECT` queries, but using the `INSERT` SQL clause, you can store new data in your tables like this:

```python
query = 'INSERT INTO tweet ("user_id", "content") VALUES (:user_id, :content);'
params = {'user_id': 1, 'content': "Hello world!"}
g.db.execute(query, params)
g.db.commit()  # this will actually write changes to the file
```

Note that we are also using the `:user_id` and `:content` placeholders to provide arguments. This is again related to security issues.

If something is wrong with the submitted data, an `sqlite3.IntegrityError` exception will be raised. You will probably want to take care of it properly.

## Updating data

To change data that is already saved in a table of the database we should use the `UPDATE` SQL clause. The Python syntax is again very similar to the previous ones.

```python
query = """
    UPDATE user
    SET first_name=:first_name, last_name=:last_name, birth_date=:birth_date
    WHERE username=:username;
"""
params = {
    'first_name': 'John',
    'last_name': 'Doe',
    'birth_date': '20-02-1985',
    'username': 'johndoe'
}
g.db.execute(query, params)
g.db.commit()
```

Again, `IntegrityError` exception will be raised if anything goes wrong.

Note that no changes will be applied to the database file until you execute the `commit()` function.
