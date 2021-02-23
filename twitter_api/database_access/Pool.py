import psycopg2
from psycopg2 import pool
from database_config import config
import asyncio
from database_config import config


"""Object for a pool connection, """
class poolObject:
    def __init__(self, min_conn = 5,max_conn = 50):
        """Initialize the connection pool with max and min, default 50 and 5"""
        # try catch wrap, ask saumya how config is working
        self.min_conn = min_conn
        self.max_conn = max_conn
        try:
            params = config()
            self.MainPool = psycopg2.pool.SimpleConnectionPool(min_conn, max_conn,**params)
        except:
            print("FAILED to create object, critical error.")
                                                              """user = "postgres",
                                                  password = "pass@#29",
                                                  host = "127.0.0.1",
                                                  port = "5432",
                                                  database = "postgres_db")"""


    async def get_conn(self, key=None):
        """Get a free connection."""
        try:
            self.getconn()
            return True
        except:
            return False
         # Simple, not sure if the rest is needed, maybe our own await function? special async.time. to wait for a connection if full.
       """ if self._disposed:
            raise PoolError('Connection pool is disposed')

        if self._disable_pooling:
            return self._connect(key)

        if key is None:
            key = self._get_key()
        if key in self._used:
            return self._used[key]

        if self._pool:
            self._used[key] = conn = self._pool.pop()
            self._rused[id(conn)] = key
            self._tused[id(conn)] = time.time()
            return conn
        else:
            if len(self._used) == self.max_conn:
                raise PoolError('Connection pool exhausted')
            return self._connect(key) """

    def close_conn(self,open_connection):
        """This should close the connection in the pool without deleting it."""
        try:
            self.putconn(open_connection,key=None,close=False)
            return True
        except:
            return False
        


"""
    ps_connection  = postgreSQL_pool.getconn()

    if(ps_connection):
        print("successfully recived connection from connection pool ")
        ps_cursor = ps_connection.cursor()
        ps_cursor.execute("select * from mobile")
        mobile_records = ps_cursor.fetchall()

        print ("Displaying rows from mobile table")
        for row in mobile_records:
            print (row)

        ps_cursor.close()

        #Use this method to release the connection object and send back to connection pool
        postgreSQL_pool.putconn(ps_connection)
        print("Put away a PostgreSQL connection")

except (Exception, psycopg2.DatabaseError) as error :
    print ("Error while connecting to PostgreSQL", error)
"""