import pycassa
from pycassa.system_manager import *

def run_cassandra():
    sysman = SystemManager()

    # If there is already a FeedCraftDB keyspace, we have to ask the user
    # what they want to do with it.
    if 'FeedCraftDB' in sysman.list_keyspaces():
        msg = 'Looks like you already have a FeedCraftDB keyspace.\nDo you '
        msg += 'want to delete it and recreate it? All current data will '
        msg += 'be deleted! (y/n): '
        resp = raw_input(msg)
        if not resp or resp[0] != 'y':
            print "Ok, then we're done here."
            return
        sysman.drop_keyspace('FeedCraftDB')

    sysman.create_keyspace('FeedCraftDB', SIMPLE_STRATEGY, {'replication_factor': '1'})
    sysman.create_column_family('FeedCraftDB', 'User', comparator_type=UTF8_TYPE)
    sysman.create_column_family('FeedCraftDB', 'Friends', comparator_type=BYTES_TYPE)
    sysman.create_column_family('FeedCraftDB', 'Followers', comparator_type=BYTES_TYPE)
    sysman.create_column_family('FeedCraftDB', 'Peed', comparator_type=UTF8_TYPE)
    sysman.create_column_family('FeedCraftDB', 'Timeline', comparator_type=LONG_TYPE)
    sysman.create_column_family('FeedCraftDB', 'Userline', comparator_type=LONG_TYPE)
    print 'All done!'

run_cassandra()
