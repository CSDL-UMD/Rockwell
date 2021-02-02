import psycopg2
from database_config import config
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

    def insert_user(self,worker_id,assignment_id,hit_id,exp_condition) -> None:
        """ insert a new vendor into the vendors table """
        sql = """INSERT INTO truman_user(worker_id,assignment_id,Hit_id,exp_condition)
             VALUES(%s,%s,%s,%s) RETURNING worker_id;"""
        try:
            cur = self.connector.cursor() # SPEED UP: Possibly move this to a datamember also to share across add functions.
            # execute the INSERT statement
            cur.execute(sql, (worker_id,assignment_id,hit_id,exp_condition,))
            # commit the changes to the database
            self.connector.commit()
            # close communication with the database
            cur.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print("ERROR!!!!",error)