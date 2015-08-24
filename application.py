#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=
# ** Renchon
#------------------------------------------------------------------------------
# Main module that creates the views and runs the app.
#=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=

import os
import re
import shutil
import tweepy

from datetime import datetime
from functools import wraps

from flask import Flask, request, session, render_template, redirect, \
    url_for, escape
from werkzeug import secure_filename
from models import db, Manga, Chapter, Page
from admin import ADMIN_USERNAME, ADMIN_PASSWORD, SECRET_KEY, SEND_TWEETS, \
    TWITTER_WIDGET_ID, TWITTER_LINK, CONSUMER_KEY, CONSUMER_SECRET, \
    ACCESS_TOKEN, ACCESS_TOKEN_SECRET

UPLOAD_FOLDER = "static/"
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])

application = Flask(__name__)
application.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tmp/reader.db"
application.secret_key = SECRET_KEY

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
twitter_api = tweepy.API(auth)

db.init_app(application)

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
    directory = application.config['UPLOAD_FOLDER'] + url + "/"
    # Make the directory in case it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    complete_url = os.path.join(directory, filename)
    # Then save the file to that directory
    file.save(complete_url)
    return complete_url

def delete_directory(url):
    shutil.rmtree(application.config['UPLOAD_FOLDER'] + url)

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

def add_chapter(manga, chapter_name, chapter_num, pages):
    # Ensure that chapter_num is a float
    chapter_num = float(chapter_num)
    # Ensure that the manga does not have a chapter with the same number
    if manga.chapters.filter_by(num=chapter_num).first():
        return
    new_chapter = Chapter(chapter_name, chapter_num, manga)
    # Representation is different if its an integer
    num_string = chapter_to_string(chapter_num)
    # Make a new folder for the chapter
    url = new_chapter.manga.url + "/Chapter_" + num_string
    # Rename and add all the chapter pages
    curr_page = 1
    for page in pages:
        # Skip resource forks
        if "__MACOSX" in page.filename:
            continue
        filename = rename(page, "%03d" % curr_page)
        # Make sure nothing that isn't an image file doesn't get through.
        if not allowed_file(page.filename):
            continue
        new_page = Page(curr_page, save_file(page, url, filename), new_chapter)
        db.session.add(new_page)
        # Remember to increment curr_page
        curr_page += 1
    zip_directory(manga, num_string, url)
    # Manga has been updated, so update the last updated date
    manga.last_updated = datetime.utcnow()
    # Add and commit to the database
    db.session.add(new_chapter)
    db.session.commit()

def make_zip_filename(manga, chapter_num):
    return manga.name.replace(" ", "_").lower() + "-chapter" + chapter_num

def zip_directory(manga, chapter_num, url):
    directory = application.config['UPLOAD_FOLDER'] + url + "/"
    filename = make_zip_filename(manga, chapter_num)
    # To make sure there is no recursive compression
    shutil.make_archive(directory + "../" + filename, "zip", directory)
    shutil.move(directory + "../" + filename + ".zip",
            directory + filename + ".zip")

def get_chapter_from_url(url):
    url_list = str.split(url, "/")
    return float(re.search(r"(\d+)\Z", url_list[-2]).group(1))

def init_chapter_hash(chapter_hash, form):
    for key in form.keys():
        if key == "manga_name":
            continue
        chapter_num_key = str.split(key, "_")[-1]
        if not chapter_num_key in chapter_hash:
            chapter_hash[chapter_num_key] = {}
        if "chapter_name_" in key:
            inner_key = "name"
        elif "chapter_num_" in key:
            inner_key = "num"
        chapter_hash[chapter_num_key][inner_key] = form[key]

def store_files_into_hash(chapter_hash, files):
    def key_func(f):
        name = ".".join(str.split(f.filename, ".")[:-1])
        try:
            return float(name)
        except ValueError:
            return float("inf")
    for key in files.keys():
        chapter_hash[key]["pages"] = []
        for f in sorted(files.getlist(key), key=key_func):
            chapter_hash[key]["pages"].append(f)

def add_all_chapters(manga, chapter_hash):
    best_index = 0
    key_func = lambda index: float(chapter_hash[index]["num"])
    for index in sorted(chapter_hash.keys(), key=key_func):
        add_chapter(manga, chapter_hash[index]["name"],
            chapter_hash[index]["num"],
            chapter_hash[index]["pages"])
        best_index = index
    # Send a tweet saying that the manga has been updated
    if SEND_TWEETS:
        latest_chapter = str(chapter_hash[best_index]["num"])
        url = request.url_root[:-1]
        url += url_for("view_page", manga=manga.url, chapter=latest_chapter)
        text = manga.name + " has been updated! Chapter "
        text += latest_chapter + " - " + url
        twitter_api.update_status(status=text)

def requires_admin(func):
    @wraps(func)
    def wrapped_func(*args, **kwargs):
        if not session.get("logged_in"):
            return render_template("login.html", failed=False)
        return func(*args, **kwargs)
    return wrapped_func

#===============================================================================
# ** Views
#===============================================================================

# Admin
@application.route("/admin")
def admin():
    if session.get("logged_in"):
        manga = Manga.query.order_by("last_updated desc").all()
        manga_list = list(map(lambda x: x.name, manga))
        chapter_list = list(map(lambda x: list(map(lambda y: [y.name, y.num],
            x.chapters.order_by("num desc").all())), manga))
        return render_template("admin.html", manga=manga_list,
            chapter_list=chapter_list)
    else:
        return render_template("login.html", failed=False)

# Admin login
@application.route("/admin/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["logged_in"] = True
        return redirect(url_for("admin"))
    else:
        return render_template("login.html", failed=True)

# Admin Logout
@application.route("/reader/admin/logout")
@requires_admin
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

# Add Manga
@application.route("/add_manga", methods=["POST"])
@requires_admin
def add_manga():
    name = request.form["manga_name"]
    url = request.form["manga_url"]
    file = request.files["manga_cover"]

    # Handle the case where there are conflicting manga names
    if Manga.query.filter_by(name=name).first():
        error_text = "Manga title already exists."
        return render_template('admin.html', error=error_text)

    # Handle the case where there are conflicting manga urls
    if os.path.exists(application.config['UPLOAD_FOLDER'] + url):
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
    # Escape to avoid being pwnd by ATRAN
    description = str(escape(request.form["manga_description"]))
    description = description.replace("\n", "<br>")
    new_manga = Manga(name, url, author, artist, status, cover_url,
        description)

    # Add and commit the new manga into the database
    db.session.add(new_manga)
    db.session.commit()

    # Send a tweet saying that the manga has been created
    if SEND_TWEETS:
        full_url = request.url_root[:-1]
        full_url += url_for("view_manga", manga=url)
        text = 'A new manga "' + name + '" has been released! Check it'
        text += ' out at ' + full_url
        twitter_api.update_status(status=text)

    return redirect(url_for("view_manga", manga=url))

# Edit Manga
@application.route("/edit_manga", methods=["POST"])
@requires_admin
def edit_manga():
    # Find the manga using the old name
    old_name = request.form["manga_oldname"]
    manga = Manga.query.filter_by(name=old_name).first()
    # Overwrite all the fields of the manga
    manga.name = request.form["manga_name"]
    manga.author = request.form["manga_author"]
    manga.artist = request.form["manga_artist"]
    # Temporarily replace <br> with newlines
    manga.description = request.form["manga_description"].replace("<br>", "\n")
    # Escape the rest of the description, and convert it back to a string
    manga.description = str(escape(manga.description))
    # Now replace the newlines with <br> tags again
    manga.description = manga.description.replace("\n", "<br>")
    # Ovewrite the cover file if necessary
    cover_file = request.files["manga_cover"]
    if cover_file.filename:
        cover_filename = rename(cover_file, "cover")
        manga.cover = save_file(cover_file, manga.url, cover_filename)
    # Update and redirect to the original page
    db.session.commit()
    return redirect(url_for("view_manga", manga=manga.url))

# Delete Manga
@application.route("/delete_manga", methods=["POST"])
@requires_admin
def delete_manga():
    # Find the manga using the old name
    old_name = request.form["delete_manga_name"]
    manga = Manga.query.filter_by(name=old_name).first()
    # Delete the contents of the manga directory
    delete_directory(manga.url)
    # Delete all chapters that map to this manga
    for chapter in manga.chapters.all():
        db.session.delete(chapter)
    # Update and redirect to the original page
    db.session.delete(manga)
    db.session.commit()

    return redirect(url_for("admin"))

# Add Chapter
@application.route("/add_chapter", methods=["POST"])
@requires_admin
def add_chapter_bulk():
    chapter_hash = {}
    manga_name = request.form["manga_name"]
    manga = Manga.query.filter_by(name=manga_name).first()
    init_chapter_hash(chapter_hash, request.form)
    store_files_into_hash(chapter_hash, request.files)
    add_all_chapters(manga, chapter_hash)
    # Return back to the original page
    return redirect(url_for("view_manga", manga=manga.url))

# Delete Chapter
@application.route("/delete_chapter", methods=["POST"])
@requires_admin
def delete_chapter():
    manga_name = request.form["chapter_delete_manga"]
    chapter_num = request.form["chapter_delete_chapter"]
    manga = Manga.query.filter_by(name=manga_name).first()
    chapter = manga.chapters.filter_by(num=chapter_num).first()

    num_string = chapter_to_string(chapter.num)
    url = chapter.manga.url + "/Chapter_" + num_string
    delete_directory(url)

    db.session.delete(chapter)
    db.session.commit()

    return redirect(url_for("view_manga", manga=manga.url))

# Index
@application.route("/")
def index():
    # Get all of the things to be displayed in this view
    manga_list = []
    manga_urls = []
    cover_urls = []
    chapters = []
    chapter_urls = []
    date_str = []
    # Iterate through the first 9 manga in the database
    for manga in Manga.query.order_by("last_updated desc").limit(9):
        newest_chapter = manga.chapters.order_by("date_added desc").first()
        if not newest_chapter:
            continue
        manga_list.append(manga.name)
        manga_urls.append(url_for("view_manga", manga=manga.url))
        cover_urls.append("/" + manga.cover)

        update_chapter_list(newest_chapter, manga, chapters, chapter_urls)
        update_date_list(manga, date_str)

    return render_template("index.html", manga_list=manga_list,
                            cover_urls=cover_urls, chapters=chapters,
                            manga_urls=manga_urls, chapter_urls=chapter_urls,
                            date_str=date_str, twitter_link=TWITTER_LINK,
                            twitter_widget_id=TWITTER_WIDGET_ID)

# Manga Summary Page
@application.route("/<manga>")
def view_manga(manga=None):
    chapter_list = []
    chapter_urls = []
    date_str = []

    # Redirect to the index
    if not manga:
        redirect(url_for("index"))

    # Make sure that a manga with that url exists
    manga = Manga.query.filter_by(url=manga).first()
    if manga is None:
        return render_template("404.html"), 404

    cover_url = "/" + manga.cover
    for chapter in manga.chapters.order_by("num desc"):
        chapter_num = chapter_to_string(float(chapter.num))
        chapter_list.append("Chapter %s: %s" % (chapter_num, chapter.name))
        chapter_urls.append(url_for("view_page", manga=manga.url,
            chapter=chapter_num))
        date = chapter.date_added.date()
        date_str.append("%02d.%02d.%02d" % (date.day, date.month,
            date.year % 100))

    return render_template("manga.html", manga=manga.name, author=manga.author,
            artist=manga.artist, cover_url=cover_url,
            description=manga.description, chapter_list=chapter_list,
            chapter_urls=chapter_urls, date_str=date_str)

# Search
@application.route("/search", methods=["POST"])
def search():
    query = request.form["search"]
    manga_list = Manga.query.filter(Manga.name.contains(query) |
            Manga.author.contains(query) |
            Manga.artist.contains(query)).order_by("name")
    # Create a list of all manga that fits the search
    kwargs = create_manga_list(manga_list)
    return render_template("search.html", **kwargs)

# Manga List
@application.route("/manga_list")
def manga_list():
    # Create a list of all manga ordered by their name
    kwargs = create_manga_list(Manga.query.order_by("name"))
    return render_template("manga_list.html", **kwargs)

# Reader
@application.route("/<manga>/<chapter>")
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

    download_url = re.search(r"(.+\/).*?\Z", urls[0]).group(1)
    download_url += make_zip_filename(manga, num_string) + ".zip"

    return render_template("reader.html", manga=manga.name, manga_url=manga.url,
                          chapter_name=chapter.name, chapter_num=num_string,
                          urls=urls, last_page=last_page.num,
                          chapters=chapter_list,
                          next_chapter=next_chapter, download_url=download_url)

# Page Not Found
@application.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Database Initialisation
@application.before_first_request
def setup_database(*args, **kwargs):
    file_path = 'tmp/reader.db'
    # Create tmp folder if it doesn't exist
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
    # If an old database does not exist
    if not os.path.exists(file_path):
        # Make new database
        file = open(file_path, 'w+')
        file.close()
        db.create_all()

if __name__ == "__main__":
    application.run(debug=True)
