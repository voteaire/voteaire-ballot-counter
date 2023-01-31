#  a queue provider should implement 2 methods, next() and ack()
# next will provide the next record to process, or None if there are none
# records are {tx_hash, metadata}


def next():
    pass


def ack():
    pass
