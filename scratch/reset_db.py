import os
db_path = '/home/srikanish/Documents/edusync_phase1/edusync/edusync.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted {db_path}")
else:
    print(f"{db_path} does not exist")
