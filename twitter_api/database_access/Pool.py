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


    async def get_conn(self, key=None) -> bool:
        """Get a free connection."""
        try:
            conn = self.getconn()
            return conn
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

    def close_conn(self,open_connection) -> bool:
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


"""
FROM DR. GIOVANNI
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import TRANSACTION_STATUS_UNKNOWN, TRANSACTION_STATUS_IDLE
from flask import g
import threading
import tenacity
import uuid
import pwd
import os


# we want to set up a separate logger
logger = logging.getLogger(__name__)


class PoolError(psycopg2.Error):
    pass


class ConnectionPool:
    def __init__(self, minconn, maxconn, *args, **kwargs):
        self.minconn = int(minconn)
        self.maxconn = int(maxconn)

        self._args = args
        self._kwargs = kwargs

        self._pool = []   # connections that are available
        self._used = {}   # connections currently in use

        # control access to the thread pool
        self._lock = threading.RLock()

    def getconn(self, key):
        with self._lock:
            # this key already has a connection so return it
            if (key in self._used):
                return self._used[key]

            # our pool is currently empty
            if (len(self._pool) == 0):
                # we've given out all of the connections that we want to
                if (len(self._used) == self.maxconn):
                    raise PoolError("connection pool exhausted")

                # get a connection but do it with a retry
                conn = self._connect()

                # add to the list of available connections
                self._pool.append(conn)

            # take a connection out of the pool and give it away
            self._used[key] = conn = self._pool.pop()
            return conn

    def putconn(self, key, close=False):
        with self._lock:
            conn = self.getconn(key)
            if (conn is None):
                raise PoolError("no connection with that key")

            if (len(self._pool) < self.minconn and not close):
                # Return the connection into a consistent state before putting
                # it back into the pool
                status = conn.info.transaction_status
                if (status == TRANSACTION_STATUS_UNKNOWN):
                    # server connection lost
                    conn.close()
                elif (status != TRANSACTION_STATUS_IDLE):
                    # connection in error or in transaction
                    conn.rollback()
                    self._pool.append(conn)
                else:
                    # regular idle connection
                    self._pool.append(conn)
            else:
                conn.close()

            # here we check for the presence of key because it can happen that
            # a thread tries to put back a connection after a call to close
            if (key in self._used):
                del self._used[key]

    # retry with a random value between every 0.5 and 1.5 seconds
    @tenacity.retry(wait=tenacity.wait_fixed(0.5) + tenacity.wait_random(0, 1.5), before=tenacity.before_log(logger, logging.DEBUG))
    def _connect(self):
        # connect to the database with the arguments provided when the pool was
        # initialized. enable autocommit for consistency. this will retry using
        # the "tenacity" library.
        conn = psycopg2.connect(*self._args, **self._kwargs)
        conn.autocommit = True
        return conn


class DatabaseClient:
    def __init__(self, app=None, **kwargs):
        if (app is not None):
            self.init_app(app, **kwargs)
        else:
            self.app = None

    def init_app(self, app, key="default", minconn=2, maxconn=32, **kwargs):
        """
        """
        The key is a name for the connection. This allows you to build pools
        for multiple databases. If you don't provide one then you can only
        pool one database.
        """
        """
        self.app = app

        # this is how we will find the database connection client identifier
        # for this request. this lets the library ensure that it is handing out
        # the same connection for the duration of the request.
        self.key = "db_client_key[{}]".format(key)

        # initialize the connection pool
        self.pool = ConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            cursor_factory=RealDictCursor,
            **kwargs,
        )

        # this will clean up the connection when it is done
        self.app.teardown_request(self.close)

    def conn(self):
        """
        """
        This function should be used by your Flask views to get a connection
        to the database. It will always return a valid connection and will
        always return the same connection to the same request. It will only
        throw an exception if the pool is full.
        """
        """
        # loop until we have a database connection
        db_client = None
        while (db_client is None):
            # see if we have a database client identifier for this request
            # already. if we have a client identifier then get the connection
            # associated with that identifier and test if it is still alive. if
            # it is alive then return it. if it is not alive then raise an
            # exception because we want to return the same connection through
            # an entire request. if we do NOT have a client identifier then
            # get a connection and test it until we get a connection that is
            # alive.
            db_client_id = None
            if (hasattr(g, self.key)):
                # try to get a connection with this client id
                db_client_id = str(getattr(g, self.key))
                db_client = self._get_connection(db_client_id)

                # no connection returned for the request's client identifier so
                # the connection is dead and we can't do anything.
                if (db_client is None):
                    delattr(g, self.key)  # remove client identifier
                    raise PoolError("request connection lost")

                # actually the client identifier returned a valid connection
                return db_client

            # try to get a connection with a new identifier
            db_client_id = str(uuid.uuid4())
            db_client = self._get_connection(db_client_id)

            # the connection that we got was valid so let's save the identifier
            # and return the connection. (if it wasn't valid then we'll just
            # repeate the loop which is a-ok.)
            if (db_client is not None):
                # do anything with a new connection here. for example, maybe
                # you want to set a configuration value that use the person's
                # username in it. i don't know.
                # TODO

                # then attach the connection to the request global
                setattr(g, self.key, db_client_id)
                return db_client

    def close(self, exception):
        # this gets called when a request is finished, regardless of the state
        # of the request (e.g. success [2xx] or failure [4xx, 5xx])
        if (hasattr(g, self.key)):
            try:
                db_client_id = getattr(g, self.key)
                self.pool.putconn(db_client_id)
                logger.debug("returned connection {} to pool named {}".format(db_client_id, self.key))
            except (PoolError, KeyError) as e:
                logger.error("could not return connection to pool: {}".format(repr(e)))

    def _get_connection(self, db_client_id):
        db_client = self.pool.getconn(db_client_id)

        try:
            logger.debug("testing connection {} from pool named {}".format(db_client_id, self.key))

            # test the connection before giving it back to ensure it works.
            # if it doesn't work then we're going to close it and try to
            # get a different connection until we find one that works.
            cur = db_client.cursor()
            cur.execute("SELECT pg_backend_pid()")
            cur.close()
        except Exception as e:
            logger.warning("connection {} from pool named {} failed: {}".format(db_client_id, self.key, e))

            # we do not have a valid connection so put it back and close it
            # and set our current db_client to None so that our next time
            # around the loop will attempt to get a new connection.
            self.pool.putconn(db_client_id, close=True)

            # the connection was bad
            return
        else:
            logger.debug("using connection {} from pool named {}".format(db_client_id, self.key))

            # the connection was good
            return db_client

            """