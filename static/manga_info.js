function update_hidden_input() {

  $(".hidden_input").each(
    function(index, element) {
      if (index > 0) {
        $(this).val($(".manga_info")[index - 1].innerHTML)
      }
    }
  )

}

function edit_text(e) {

  // Transform all the text fields into input fields
  $(".manga_info").each(
    function(index, element) {
      text = element.innerHTML.replace(/<br>/g, "\n");
      if (index == 3) {
        element.innerHTML = "<textarea cols='80' rows='10'" +
            "name='manga_description' required>" + text + "</textarea>";
      } else {
        element.innerHTML = "<input type='text' value='" + text +
            "' required  />";
      }
    }
  )

  $(this).replaceWith("<input id='manga_edit' type='button'" +
      "value='Save Manga Information'>")
  $("#manga_edit").click(save_text);

}

function save_text(e) {

  // Transform all the input fields back into text fields
  $(".manga_info").each(
    function(index, element) {
      text = $(this).children().val();
      element.innerHTML = text.replace(/\r\n|\r|\n/g, "<br>");
    }
  )

  update_hidden_input();

  $(this).replaceWith("<input id='manga_edit' type='button'" +
      "value='Edit Manga Information'>")
  $("#manga_edit").click(edit_text);

}

function read_url(input) {

  // If a file was added to the input
  if (input.files && input.files[0]) {
    reader = new FileReader();
    reader.onload = function(e) {
      $('#cover_photo').attr("src", e.target.result);
    }
    reader.readAsDataURL(input.files[0]);
  }

}

function edit_cover_photo() {
  document.getElementById("cover").click();
}

function delete_chapter(manga, chapter) {

  re = /^Chapter\s(\d+(?:\.\d+)?)/;
  chapter_num = re.exec(chapter)[1];
  json = {chapter_delete_manga: manga,
          chapter_delete_chapter: chapter_num}

  send_post_request(delete_chapter_path, json)

}

function send_post_request(path, params, method) {

    method = method || "post";

    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for(var key in params) {
        if(params.hasOwnProperty(key)) {
            hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);
            form.appendChild(hiddenField);
         }
    }

    document.body.appendChild(form);
    form.submit();
}
