import psycopg2
from configparser import ConfigParser

def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
		
        # create a cursor
        cur = conn.cursor()
        
	# execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
       
	# close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return conn

def close_connection(conn):
	try:
		conn.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)

def insert_user(conn,worker_id,assignment_id,hit_id,exp_condition):
    """ insert a new vendor into the vendors table """
    sql = """INSERT INTO user_table(worker_id,assignment_id,Hit_id,exp_condition)
             VALUES(%s,%s,%s,%s) RETURNING worker_id;"""
    try:
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, (worker_id,assignment_id,hit_id,exp_condition,))
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("ERROR!!!!",error)

if __name__ == '__main__':
	conn = connect()
	insert_user(conn,1,23,"ABC","XYZ")
	close_connection(conn)