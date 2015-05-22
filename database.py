from renchon import db, Manga, Chapter, Page

db.create_all()

#~ test_manga = Manga("Test Manga", "Test Author", "Test Artist", "In Progress", 
             #~ "Test Cover URL", "Test Description")
             
#~ test_chapter = Chapter("Test Chapter", 1, test_manga)
#~ test_chapter_2 = Chapter("Test Chapter 2", 2, test_manga)

#~ test_pages = [Page(1, "Test Image URL (1, 1)", test_chapter),
              #~ Page(2, "Test Image URL (1, 2)", test_chapter),
              #~ Page(3, "Test Image URL (1, 3)", test_chapter),
              #~ Page(4, "Test Image URL (1, 4)", test_chapter),
              #~ Page(5, "Test Image URL (1, 5)", test_chapter),
              #~ Page(1, "Test Image URL (2, 1)", test_chapter_2),
              #~ Page(2, "Test Image URL (2, 2)", test_chapter_2),
              #~ Page(3, "Test Image URL (2, 3)", test_chapter_2),
              #~ Page(4, "Test Image URL (2, 4)", test_chapter_2),
              #~ Page(5, "Test Image URL (2, 5)", test_chapter_2)]
             
#~ db.session.add(test_manga)
#~ db.session.add(test_chapter)
#~ db.session.add(test_chapter_2)

#~ for page in test_pages:
    #~ db.session.add(page)
    
#~ db.session.commit()

#~ print(test_manga.chapters.all())
#~ print(test_chapter.pages.all())