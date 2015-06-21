var chapters = []

function create_chapter_select() {
  
  manga_id = document.getElementById("manga_delete").selectedIndex;
  
  chapter_select = document.getElementById("chapter_delete");
  chapter_select.innerHTML = "";
  
  for (i = 0; i < chapters[manga_id].length; i++) {
    chapter = chapters[manga_id][i];
    chapter_select.innerHTML += "<option value='" + chapter[1] + 
      "'>" + "Chapter " + chapter[1] + ": " + chapter[0] + "</option>";
  }    
  
}