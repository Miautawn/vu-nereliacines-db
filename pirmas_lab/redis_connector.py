import sys
import redis

class Redis():

    @staticmethod
    def connect(host: str, port: int):
        try:
            db = redis.Redis(host=host, port=port)
            db.ping()
            return db
        except Exception as e:
            print(f"Couldn't establish redis connection: {e}")
            sys.exit(0)



