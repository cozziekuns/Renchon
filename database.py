#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# ** Database
#------------------------------------------------------------------------------
# Clears old databases and makes new ones.
#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=

import os
from renchon import db, Manga, Chapter, Page

file_path = 'tmp/reader.db'

# Create tmp folder if it doesn't exist
if not os.path.exists('tmp'):
    os.mkdir('tmp')

# Clear old database if file exists
if os.path.exists(file_path):
    os.remove(file_path)

# Make new database
file = open(file_path, 'w+')
file.close()

db.create_all()
