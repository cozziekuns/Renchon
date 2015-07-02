#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# ** Renchon
#------------------------------------------------------------------------------
# Main module that creates the views, runs the database, and runs the app. Ok,
# it basically does it all.
#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=

import os
import shutil

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

def delete_directory(url):
    shutil.rmtree(app.config['UPLOAD_FOLDER'] + url)

def recreate_chapter_list(chapter_list, chapter_before, latest_chapter):
    # If there is no chapter before, just insert an extra chapter at the top
    chapter_limit = 7
    if not chapter_before:
        chapter_limit += 1

    # Recreate the list based on the position of the chapter we're currently
    # on
    if len(chapter_list) > chapter_limit:
        temp = []
        chapter_list.reverse()
        for item in chapter_list:
            temp.insert(0, item)
            if len(temp) == chapter_limit:
                break
        chapter_list = temp

    # Add the latest chapter
    chapter_list.insert(0, [chapter_to_string(latest_chapter.num),
        latest_chapter.name + " (Latest)"])

    # Add the chapter before this chapter, unless this chapter is the earliest
    # chapter
    if chapter_before:
        info = [chapter_to_string(chapter_before.num), chapter_before.name]
        if not info in chapter_list:
            chapter_list.append(info)

    return chapter_list

def update_chapter_list(chapter, manga, chapters, chapter_urls):
    chapter_num = chapter_to_string(float(chapter.num))
    chapters.append("Chapter %s: %s" % (chapter_num, chapter.name))
    chapter_urls.append(url_for("view_page", manga=manga.url,
        chapter=chapter_num))

def dateifed_day(date):
    if date.day % 10 == 1:
        date_day = str(date.day) + "st"
    elif date.day % 10 == 2:
        date_day = str(date.day) + "nd"
    elif date.day % 10 == 3:
        date_day = str(date.day) + "rd"
    else:
        date_day = str(date.day) + "th"
    return date_day

def update_date_list(manga, date_str):
    date = manga.last_updated.date()
    date_str.append("%02d.%02d.%02d" % (date.day, date.month, date.year % 100))

def update_date_list_full(manga, date_str):
    months = ["January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December"]
    date = manga.last_updated.date()
    day = dateifed_day(date)

    date_str.append("%s %s, %d" % (months[date.month], day, date.year))

def create_manga_list(manga_query):
    result = {}
    result["chapters"] = []
    result["chapter_urls"] = []
    result["date_str"] = []
    for manga in manga_query:
        newest_chapter = manga.chapters.order_by("date_added desc").first()
        if not newest_chapter:
            continue
        manga_url = url_for("view_manga", manga=manga.url)
        result.setdefault("manga_list", []).append(manga.name)
        result.setdefault("manga_urls", []).append(manga_url)
        result.setdefault("authors", []).append(manga.author)
        result.setdefault("artists", []).append(manga.author)

        update_chapter_list(newest_chapter, manga, result["chapters"],
            result["chapter_urls"])
        update_date_list_full(manga, result["date_str"])

    return result

#===============================================================================
# ** Views
#===============================================================================

# Admin
@app.route("/reader/admin")
def admin():
    manga = Manga.query.order_by("last_updated desc").all()
    manga_list = list(map(lambda x: x.name, manga))
    chapter_list = list(map(lambda x: list(map(lambda y: [y.name, y.num],
        x.chapters.order_by("num desc").all())), manga))
    return render_template("admin.html", manga=manga_list,
        chapter_list=chapter_list)

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

    # Manga has been updated, so update the last updated date
    manga.last_updated = datetime.utcnow()

    db.session.add(new_chapter)
    db.session.commit()

    return redirect(url_for("admin"))

# Delete Chapter
@app.route("/reader/delete_chapter", methods=["POST"])
def delete_chapter():
    manga = Manga.query.filter_by(
        name=request.form["chapter_delete_manga"]).first()
    chapter = manga.chapters.filter_by(
      num=request.form["chapter_delete_chapter"]).first()

    num_string = chapter_to_string(chapter.num)
    url = chapter.manga.url + "/Chapter_" + num_string
    delete_directory(url)

    db.session.delete(chapter)
    db.session.commit()

    return redirect(url_for("admin"))

# Index
@app.route("/reader")
def index():
    # Get all of the things to be displayed in this view
    manga_list = []
    chapters = []
    manga_urls = []
    cover_urls = []
    chapter_urls = []
    date_str = []
    # Iterate through the first 9 manga in the database
    for manga in Manga.query.order_by("last_updated desc").limit(9):
        newest_chapter = manga.chapters.order_by("date_added desc").first()
        if not newest_chapter:
            continue
        manga_list.append(manga.name)
        manga_urls.append(url_for("view_manga", manga=manga.url))
        cover_urls.append(manga.cover)

        update_chapter_list(newest_chapter, manga, chapters, chapter_urls)
        update_date_list(manga, date_str)

    return render_template("index.html", manga_list=manga_list,
                            cover_urls=cover_urls, chapters=chapters,
                            manga_urls=manga_urls, chapter_urls=chapter_urls,
                            date_str=date_str)

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

# Search
@app.route("/reader/search", methods=["POST"])
def search():
    query = request.form["search"]
    manga_list = Manga.query.filter(Manga.name.contains(query))
    # Create a list of all manga that fits the search
    kwargs = create_manga_list(manga_list)
    return render_template("search.html", **kwargs)

# Manga List
@app.route("/reader/manga_list")
def manga_list():
    # Create a list of all manga ordered by their name
    kwargs = create_manga_list(Manga.query.order_by("name"))
    return render_template("manga_list.html", **kwargs)

# Reader
@app.route("/reader/<manga>/<chapter>")
def view_page(manga=None, chapter=None):
    # Redirect to the summary page
    if not chapter:
        redirect(url_for("view_manga", manga=manga))

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

    chapters = manga.chapters.order_by("-num").all()
    chapter_list = []
    latest_chapter = chapters[0]

    # Find the chapter before this one, unless this is the first chapter
    # Remember that chapters are ordered descendingly
    if chapters.index(chapter) == len(chapters) - 1:
        chapter_before = None
    else:
        chapter_before = chapters[chapters.index(chapter) + 1]

    # Find the chapter after this one, unless this is the last chapter
    if chapters.index(chapter) == 0:
        chapter_after = None
    else:
        chapter_after = chapters[chapters.index(chapter) - 1]

    # List automatically contains the most updated chapter
    contains_chapter = (chapter == latest_chapter)

    for item in chapters[1:]:
        chapter_list.append([chapter_to_string(item.num), item.name])
        # Set the flag to true if the list contains the chapter
        if item.num == chapter_num:
            contains_chapter = True
        if (len(chapter_list) >= 7 and contains_chapter):
            break

    chapter_list = recreate_chapter_list(chapter_list, chapter_before,
        latest_chapter)

    # Get the next chapter number for the reader
    if chapter_after:
        next_chapter = chapter_to_string(chapter_after.num)
    else:
        next_chapter = -1

    return render_template("reader.html", manga=manga.name,
                          chapter_name=chapter.name, chapter_num=num_string,
                          urls=urls, last_page=last_page.num,
                          chapters=chapter_list,
                          next_chapter=next_chapter)

# Page Not Found
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
