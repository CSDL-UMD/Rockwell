import psycopg2
from psycopg2 import pool
from database_config import config
import asyncio


"""Object for a pool connection, """
class poolObject:
    def __init__(self, min_conn = 5,max_conn = 50):
        """Initialize the connection pool with max and min, default 50 and 5"""
        # try catch wrap, ask saumya how config is working
        self.min_conn = min_conn
        self.max_conn = max_conn
        try:
            params = config()
            print("PARAMS : ")
            print(params)
            #self.MainPool = psycopg2.pool.SimpleConnectionPool(min_conn, max_conn,**params)

            self.MainPool = psycopg2.pool.SimpleConnectionPool(min_conn, max_conn,**params)
        except:
            print("FAILED to create object, critical error.")

    async def get_conn(self, key=None) -> bool:
        """Get a free connection."""
        try:
            conn = self.MainPool.getconn()
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