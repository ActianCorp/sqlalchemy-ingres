Ingres dialect for SQLAlchemy.

Originally developed to work against SQLAlchemy 0.6 and Ingres 9.2

Current work-in-progress with:

  * SQLAlchemy 1.3.16
  * Ingres 11.1 and Vector 5.1 - via ODBC


## Development instructions

Right now this is for dev purposes so install SQLAlchemy as per normal, for example:

    pip install sqlalchemy

Ingres dialect only tested with pyodbc so far:

    pip install pyodbc

Download Ingres dialect for SQLAlchemy:

    git clone https://github.com/clach04/ingres_sa_dialect.git

Setup for dev use:

    cd ingres_sa_dialect
    pip install -e .

Test:

    import sqlalchemy
    print(sqlalchemy.__version__)
    con_str = 'ingres:///demodb'  # local demodb
    con_str = 'ingres://dbuser:PASSWORD@HOSTNAME:27832/db'  # remote database called "db"
    engine = sqlalchemy.create_engine(con_str)
    connection = engine.connect()
    query = 'SELECT * FROM iidbconstants'
    for row in connection.execute(query):
        print(row)


NOTE Ensure correct ODBC Driver name is "Ingres" and is the same bit-age as the Python interpreter.
For example for 64-bit Python, ensure ODBC Driver called "Ingres" is also 64-bit.
