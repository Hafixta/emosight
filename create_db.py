import pymongo

def createDB():
    db_name='register_users'
    client = pymongo.MongoClient('mongodb+srv://Shana:poker4747@cluster0.pkmeyze.mongodb.net/?retryWrites=true&w=majority')
    shanadb = client[db_name]

    