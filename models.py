from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

#===============================================================================
# ** Manga
#===============================================================================

class Manga(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, index=True, unique=True)
    url = db.Column(db.String, unique=True)
    author = db.Column(db.String, index=True)
    artist = db.Column(db.String, index=True)
    status = db.Column(db.String)
    cover = db.Column(db.String)
    description = db.Column(db.String)
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
    name = db.Column(db.String)
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
    image = db.Column(db.String)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"))
    chapter = db.relationship("Chapter",
                              backref=db.backref("pages", lazy="dynamic"))

    def __init__(self, num, image, chapter):
        self.num = num
        self.image = image
        self.chapter = chapter

    def __repr__(self):
        return "<Page %r>" % (self.num)
