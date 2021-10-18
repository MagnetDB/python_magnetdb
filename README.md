= Magnet Database

Tools for creating and manipulating a database designed for Magnet simulations.
Data may be partly retreived from **Lncmi control and monitoringwebsite**.
See `python_magnetrun` for more details

== Structure

Viewing the database: ``sqlitebrowser`

To generate a diagram:

```
java -jar schemaspy-6.1.0.jar -debug -t sqlite -o tutut -sso -cat magnets -s magnets -db magnets.db
```

== Python

Running the app to create the database

```
python3 -m python_magnetdb.app --createdb
``` 

To populate the database with an exemple msite

```
python3 -m python_magnetdb.app --createsite
```

To see more

```
python3 -m python_magnetdb.app --help
```

== API

Running the FastAPI Application:

```
uvicorn python_magnetdb.main:app --reload
``` 

To view the API interface

```
firefox http://localhost:8000/docs
```

== Requirements

* sqlmodel
* fastapi
* uvicorn
* sqlitebrowser

```
python -m pip install sqlmodel
python -m pip install fastapi "uvicorn[standard]"
export PATH=$PATH:$HOME/.local/bin
```

== References

(sqlmodel)[https://sqlmodel.tiangolo.com/tutorial]