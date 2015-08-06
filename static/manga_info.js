var new_chapters = 0;
var total_chapters = 0;

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

function add_close_button(div, onclick) {

  button = document.createElement("input");
  button.className = "close_chapter";
  button.setAttribute("type", "button");
  button.setAttribute("value", "X");
  button.setAttribute("onclick", onclick);
  div.appendChild(button);

}

function add_label_to_element(element, name, text) {

  label = document.createElement("label");
  label.setAttribute("for", name);
  label.innerHTML = text;
  element.appendChild(label);

}

function add_input_to_div(div, type, name, text) {

  text_input = document.createElement("input");
  text_input.setAttribute("type", type);
  text_input.setAttribute("name", name);

  add_label_to_element(div, name, text);
  div.appendChild(text_input);
  div.appendChild(document.createElement("br"));

}

function add_file_upload(div, name, text) {

  label = document.createElement("label");
  label.setAttribute("for", name);
  label.innerHTML = text;

  file_input = document.createElement("input");
  file_input.setAttribute("type", "file");
  file_input.setAttribute("name", name);
  file_input.setAttribute("webkitdirectory", true);
  file_input.setAttribute("mozdirectory", true);
  file_input.setAttribute("accept", "image/*");
  file_input.setAttribute("required", true);

  div.appendChild(label);
  div.appendChild(file_input);
  div.appendChild(document.createElement("br"));

}

function create_chapter_dialog() {

  form = document.getElementById("add_chapter");
  mangle = new_chapters.toString();

  // Wrap everything in a div element
  div = document.createElement("div");
  div.setAttribute("id", "add_chapter_" + mangle);
  form.insertBefore(div, document.getElementById("add_chapter_button"));

  add_close_button(div, "delete_chapter_dialog(" + mangle + ")");
  add_input_to_div(div, "text", "chapter_name_" + mangle, "Chapter Name:");
  add_input_to_div(div, "number", "chapter_num_" + mangle, "Chapter Number:");
  add_file_upload(div, "chapter_pages_" + mangle, "Upload Folder:");
  div.appendChild(document.createElement("br"));

  // Create submit button if this is the first dialog
  if (total_chapters == 0) {
    submit_button = document.createElement("input");
    submit_button.setAttribute("type", "submit");
    submit_button.setAttribute("value", "Submit All Chapters");
    form.appendChild(submit_button);
  }

  new_chapters += 1;
  total_chapters += 1;

}

function delete_chapter_dialog(dialog_index) {

  mangle = dialog_index.toString()
  // Get the div that corresponds to this dialog_index, and remove it
  element = document.getElementById("add_chapter_" + mangle);
  element.parentNode.removeChild(element);
  total_chapters -= 1;

  // Remove submit button if this is the last dialog alive
  if (total_chapters == 0) {
    form.removeChild(form.lastChild);
  }

}

function send_post_request(path, params) {

  var form = document.createElement("form");
  form.setAttribute("method", "post");
  form.setAttribute("action", path);

  for (var key in params) {
    if (params.hasOwnProperty(key)) {
      hidden_field = document.createElement("input");
      hidden_field.setAttribute("type", "hidden");
      hidden_field.setAttribute("name", key);
      hidden_field.setAttribute("value", params[key]);
      form.appendChild(hidden_field);
    }
  }

  document.body.appendChild(form);
  form.submit();

}
