from flask import Flask, request, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
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
    num = db.Column(db.Integer)
    scangroup = db.Column(db.String(100))
    scangroup_url = db.Column(db.String(100))
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
# ** Views
#===============================================================================
        
# Index
@app.route("/")
def index():
    manga_list = map(lambda x: x.name, Manga.query.all())
    return render_template("index.html", manga=manga_list)

# Admin
@app.route("/admin")
def admin():
    manga_list = map(lambda x: x.name, Manga.query.all())
    return render_template("admin.html", manga=manga_list)
                                    
# Add Manga
@app.route("/add_manga", methods=["GET", "POST"])
def add_manga():
    
    if request.method == "POST":
        
        name = request.form["manga_name"]
        url = request.form["manga_url"]
        author = request.form["manga_author"]
        artist = request.form["manga_artist"]
        status = request.form["manga_status"]
        cover = request.form["manga_cover"]
        description = request.form["manga_description"]
        
        new_manga = Manga(name, url, author, artist, status, cover,
                          description)
                          
        db.session.add(new_manga)
        db.session.commit()

    return redirect(url_for("admin"))
    
# Add Chapter
@app.route("/add_chapter", methods=["GET", "POST"])
def add_chapter():
    
    if request.method == "POST":
        
        name = request.form["chapter_name"]
        num = request.form["chapter_num"]
        scangroup = request.form["chapter_scanalators"]
        scangroup_url = request.form["chapter_scangroup_url"]
        
        manga = request.form["chapter_manga"]
        
        new_chapter = Chapter(name, num, scangroup, scangroup_url, manga)
        
        db.session.add(new_chapter)
        db.session.commit()
        
    return redirect(url_for("admin"))
        
        
    
if __name__ == "__main__":
    app.run(debug=True)