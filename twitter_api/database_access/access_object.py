import psycopg2
from configparser import ConfigParser
# Class to open a pipeline to our database for metric modification.
class access_object:
    def __init__(self,session_id):
        self.connector = None
        try:
            params = config()
            self.connector = psycopg2.connect(**params)
        except (Exception, psycopg2.DatabaseError) as error:
          print(error)

        self.session_id = session_id

    def __del__(self): # Destructor to close the database connection on object going out of scope.
        try:
	        self.connector.close()
	    except (Exception, psycopg2.DatabaseError) as error:
		    print(error)
"""
    def connect(self):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        # create a cursor
        #cur = conn.cursor()
        #print('PostgreSQL database version:')
        #cur.execute('SELECT version()')
        # display the PostgreSQL database server version
        #db_version = cur.fetchone()
        #print(db_version) 
	# close the communication with the PostgreSQL
        #cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return conn
"""
    def insert_user(self,worker_id,assignment_id,hit_id,exp_condition) -> None:
    """ insert a new vendor into the vendors table """
    sql = """INSERT INTO user_table(worker_id,assignment_id,Hit_id,exp_condition)
             VALUES(%s,%s,%s,%s) RETURNING worker_id;"""
    try:
        cur = self.connector.cursor() # SPEED UP: Possibly move this to a datamember also to share across add functions.
        # execute the INSERT statement
        cur.execute(sql, (worker_id,assignment_id,hit_id,exp_condition,))
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("ERROR!!!!",error)