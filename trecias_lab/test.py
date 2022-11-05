from cassandra.cluster import Cluster

if __name__ == "__main__":
    cluster = Cluster(['0.0.0.0'], port = 9042)
    session = cluster.connect()
    session.set_keyspace('fish_restoraunt_chain')
