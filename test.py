import pickle

filename='db.json'

try:
    with open(filename,'rb') as fp:
        db=pickle.load(fp)
except:
    db={}

print(db)
# db[123]={"new":db}

# with open(filename, 'wb') as fp:
#     pickle.dump(db, fp)

# print(db)
