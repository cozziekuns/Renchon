#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# ** Database
#------------------------------------------------------------------------------
# Clears old databases and makes new ones.
#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=

import os
from renchon import db, Manga, Chapter, Page

file_path = 'tmp/reader.db'
# Clear old database if file exists
if os.path.exists(file_path):
    os.remove(file_path)
  
# Make new database
file = open('reader.db', 'w+')
file.close()
  
db.create_all()