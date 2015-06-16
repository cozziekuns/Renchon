#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# ** Renchon
#------------------------------------------------------------------------------
# Main module that creates the views, runs the database, and runs the app. Ok, 
# it basically does it all.
#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=

import os
from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug import secure_filename

UPLOAD_FOLDER = 'static/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tmp/reader.db"

db = SQLAlchemy(app)

#===============================================================================
# ** Manga
#===============================================================================

class Manga(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, unique=True)
    url = db.Column(db.String(100), unique=True)
    author = db.Column(db.String(50), index=True)
    artist = db.Column(db.String(50), index=True)
    status = db.Column(db.String(20))
    cover = db.Column(db.String(150))
    description = db.Column(db.String(1000))
    last_updated = db.Column(db.DateTime)
    
    def __init__(self, name, url, author, artist, status, cover, description):
        self.name = name
        self.url = url
        self.author = author
        self.artist = artist
        self.status = status
        self.cover = cover
        self.description = description
        self.last_updated = datetime.utcnow()
        
    def __repr__(self):
        return "<User %r>" % (self.name)
        
#===============================================================================
# ** Chapter
#===============================================================================
    
class Chapter(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    num = db.Column(db.Float)
    date_added = db.Column(db.DateTime)
    manga_id = db.Column(db.Integer, db.ForeignKey("manga.id"))
    manga = db.relationship("Manga", 
                            backref=db.backref("chapters", lazy="dynamic"))
    
    def __init__(self, name, num, manga):
        self.name = name
        self.num = num
        self.manga = manga
        self.date_added = datetime.utcnow()
        
    def __repr__(self):
        return "<Chapter %r>" % (self.name)
    
#===============================================================================
# ** Page
#===============================================================================
    
class Page(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer)
    image = db.Column(db.String(150))
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"))
    chapter = db.relationship("Chapter", 
                              backref=db.backref("pages", lazy="dynamic"))
    
    def __init__(self, num, image, chapter):
        self.num = num
        self.image = image
        self.chapter = chapter
        
    def __repr__(self):
        return "<Page %r>" % (self.num)
        
#===============================================================================
# ** Helper Methods
#===============================================================================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS
    
def rename(file, new_filename):
    return "".join([new_filename, ".", file.filename.split(".")[-1]])
    
def chapter_to_string(chapter_num):
    if int(chapter_num) == float(chapter_num):
        num_string = str(int(chapter_num))
    else:
        num_string = str(chapter_num)
    return num_string
    
def save_file(file, url, filename=None):
  if filename is None:
      filename = file.filename
  filename = secure_filename(filename)
  directory = app.config['UPLOAD_FOLDER'] + url + "/"
  # Make the directory in case it doesn't exist
  if not os.path.exists(directory):
      os.makedirs(directory)
  complete_url = os.path.join(directory, filename)
  # Then save the file to that directory
  file.save(complete_url)
  return complete_url
        
#===============================================================================
# ** Views
#===============================================================================
        
# Index
@app.route("/reader/")
def index():
    # Get all of the things to be displayed in this view
    manga_list = []
    cover_urls = {}
    chapters = {}
    # Iterate through all the manga in the database (eventually this will be 
    # shortened to the first 50 chapters or so...)
    for manga in Manga.query.all():
        # Filler
        manga_list.append(manga.name)
        cover_urls[manga.name] = manga.cover
        newest_chapter = manga.chapters.order_by("-id").first()
        if newest_chapter:
            chapters[manga.name] = newest_chapter.name
        else:
            chapters[manga.name] = ""
    return render_template("index.html", manga_list=manga_list, 
                            cover_urls=cover_urls, chapters=chapters)

# Admin
@app.route("/reader/admin")
def admin():
    manga_list = map(lambda x: x.name, Manga.query.all())
    return render_template("admin.html", manga=manga_list)
                                    
# Add Manga
@app.route("/reader/add_manga", methods=["POST"])
def add_manga():
    name = request.form["manga_name"]
    url = request.form["manga_url"]
    file = request.files["manga_cover"]
    
    # Handle the case where there are conflicting manga names
    if Manga.query.filter_by(name=name).first():
        error_text = "Manga title already exists."
        return render_template('admin.html', error=error_text)
    
    # Handle the case where there are conflicting manga urls
    if os.path.exists(app.config['UPLOAD_FOLDER'] + url):
        return render_template('admin.html', error="Manga URL already exists.")
    
    # Handle the case where the file is not sent
    if not (file and allowed_file(file.filename)):
        return render_template('admin.html', error="Invalid Cover File.")
    
    # Save the file to the server
    cover_filename = rename(file, "cover")
    cover_url = save_file(file, url, cover_filename)
    
    # Then, just dump the contents into the database
    author = request.form["manga_author"]
    artist = request.form["manga_artist"]
    status = request.form["manga_status"]
    description = request.form["manga_description"]
    new_manga = Manga(name, url, author, artist, status, cover_url, 
        description)
    
    # Add and commit the new manga into the database
    db.session.add(new_manga)
    db.session.commit()

    return redirect(url_for("admin"))
    
# Add Chapter
@app.route("/reader/add_chapter", methods=["POST"])
def add_chapter():
  
    name = request.form["chapter_name"]
    num = 0
    
    # Convert the chapter number to a float (we need a float for stuff like 
    # omakes)
    try:
        num = float(request.form["chapter_num"])
    except ValueError:
        return render_template('admin.html', error="Invalid Chapter Number.")
      
    manga = Manga.query.filter_by(name=request.form["chapter_manga"]).first()
    new_chapter = Chapter(name, float(num), manga)
    
    # Rename and add all the chapter pages
    curr_page = 1
    
    # Representation is different if its a number
    num_string = chapter_to_string(num)
        
    # Make a new folder for the chapter
    url = new_chapter.manga.url + "/Chapter_" + num_string
    pages = request.files.getlist("chapter_pages")
    for page in pages:
        filename = rename(page, "%03d" % curr_page)
        # Make sure nothing that isn't an image file doesn't get through.
        if not allowed_file(page.filename):
            continue
        new_page = Page(curr_page, save_file(page, url, filename), new_chapter)
        db.session.add(new_page)
        # Remember to increment curr_page
        curr_page += 1
    
    db.session.add(new_chapter)
    db.session.commit()
    
    return redirect(url_for("admin"))
    
# Manga Summary Page
@app.route("/reader/<manga>")
def view_manga(manga=None):
    # Redirect to the index
    if not manga:
        redirect(url_for("index"))
        
    # Make sure that a manga with that url exists
    manga = Manga.query.filter_by(url=manga).first()
    if manga is None:
        return render_template("404.html"), 404
        
    return render_template("manga.html", manga=manga)
    
# Reader
@app.route("/reader/<manga>/<chapter>")
def view_page(manga=None, chapter=None):
    # Redirect to the summary page
    if not chapter:
        redirect(url_for("view_manga", manga))
        
    # Make sure that a manga with that url exists
    manga = Manga.query.filter_by(url=manga).first()
    if manga is None:
        return render_template("404.html"), 404
        
    # Make sure that the manga has a chapter with that number
    try:
        chapter_num = float(chapter)
    except ValueError:
        return render_template("404.html"), 404
        
    results = manga.chapters.filter_by(num=chapter_num)
    chapter = results.first()
    if chapter is None:
        return render_template("404.html"), 404
        
    last_page = chapter.pages.order_by("-num").first()
        
    # Not going to do this in JS
    num_string = chapter_to_string(chapter_num)
    urls = list(map(lambda x: "/" + x.image, chapter.pages.all()))
    
    return render_template("reader.html", manga=manga.name, 
                          chapter_name=chapter.name, chapter_num=chapter.num, 
                          urls=urls, last_page=last_page.num)

# Page Not Found
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
        
# Manga Upload Failed
    
if __name__ == "__main__":
    app.run(debug=True)