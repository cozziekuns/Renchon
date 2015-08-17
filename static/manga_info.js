function update_hidden_input() {
  $(".hidden_input").each(function(index, element) {
    if (index > 0) {
      $(this).val($(".manga_info")[index - 1].innerHTML)
    }
  })
}

function edit_text(e) {
  // Remove the "Submit Changes" button from the form
  var form = document.getElementById("edit_manga");
  form.removeChild(form.lastChild);
  // Transform all the text fields into input fields
  $(".manga_info").each(
    function(index, element) {
      var text = element.innerHTML.replace(/<br>/g, "\n");
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
      var text = $(this).children().val();
      element.innerHTML = text.replace(/\r\n|\r|\n/g, "<br>");
    }
  )

  update_hidden_input();

  $(this).replaceWith("<input id='manga_edit' type='button'" +
      "value='Edit Manga Information'>")
  $("#manga_edit").click(edit_text);

  // Re-add the "Submit Changes" button to the form
  var button = document.createElement("input");
  button.setAttribute("type", "submit");
  button.setAttribute("value", "Submit Changes");

  var form = document.getElementById("edit_manga");
  form.appendChild(button);
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

/* Drag and Drop */

var form_data = null;
var chapter_data = {};
var total_pages = {};

function allow_drop(event) {
  event.preventDefault();
}

function drop_chapter(event) {
  event.preventDefault();
  var data_transfer = event.dataTransfer;
  if (data_transfer && data_transfer.items) {
    var items = data_transfer.items;
    for (var i = 0; i < items.length; i++) {
      var entry = items[i].webkitGetAsEntry();
      if (entry.isDirectory) {
        traverse_filesystem(entry);
      } else if (entry.isFile) {
        // Show an error message saying that it must be a directory that
        // is uploaded.
      }
    }
  }
  document.getElementById("chapter_dropzone").className = "";
}

function traverse_filesystem(entry) {
  var reader = entry.createReader();
  var chapter_num = get_chapter_from_url(entry.fullPath);
  if (chapter_num >= 0) {
    if (!chapter_data.hasOwnProperty(chapter_num)) {
      chapter_data[chapter_num] = [];
      total_pages[chapter_num] = 0;
    } else {
      // Disallow duplicate chapters
      return;
    }
  }
  reader.readEntries(function(entries) {
    var len = entries.length;
    if (chapter_num >= 0) {
      total_pages[chapter_num] += len;
    }
    for (var i = 0; i < len; i++) {
      if (entries[i].isFile && chapter_num >= 0) {
        enter_into_chapter_data(entries[i], chapter_num);
      } else if (entries[i].isDirectory) {
        traverse_filesystem(entries[i]);
      }
    }
  });
}

function enter_into_chapter_data(entry, chapter_num) {
  entry.file(function(file) {
    chapter_data[chapter_num].push(file);
    if (chapter_data[chapter_num].length == total_pages[chapter_num]) {
      console.log(chapter_num + " finished parsing.");
      add_chapter_element(chapter_num);
    }
    if (ready_to_submit()) {
      console.log("Ready to submit!");
      add_submit_element();
    }
  });
}

function add_submit_element() {
  var chapter_submit = document.getElementById("chapter_submit");
  if (!chapter_submit.innerHTML) {
    var submit_span = document.createElement("span");
    submit_span.id = "chapter_submit_button"
    submit_span.className = "chapter_submit";
    submit_span.onclick = upload_chapters;
    submit_span.innerHTML = "Submit All Chapters";
    chapter_submit.appendChild(submit_span);
  }
}

function add_chapter_element(chapter_num) {
  var chapter_list = document.getElementById("chapter_list");
  var list_element = document.createElement("li");
  var chapter_div = document.createElement("div");
  chapter_div.className = "chapter_admin_box";
  add_chapter_image_to_element(chapter_div, chapter_num);
  list_element.appendChild(chapter_div);
  chapter_list.appendChild(list_element);
}

function add_label_to_element(element, name, text) {
  label = document.createElement("label");
  label.setAttribute("for", name);
  label.innerHTML = text;
  element.appendChild(label);
}

function add_input_to_element(element, type, name, text, value) {
  text_input = document.createElement("input");
  text_input.setAttribute("type", type);
  text_input.setAttribute("name", name);
  if (value) {
    text_input.setAttribute("value", value);
  }
  text_input.setAttribute("required", true);
  add_label_to_element(element, name, text);
  element.appendChild(text_input);
  element.appendChild(document.createElement("br"));
}


function add_chapter_image_to_element(element, chapter_num) {
  var reader = new FileReader();
  reader.onload = function(event) {
    var image = new Image();
    image.src = event.target.result;
    image.className = "chapter_admin_box";
    element.appendChild(image);
    add_chapter_info_to_element(element, chapter_num);
  };
  for (var i = 0; i < chapter_data[chapter_num].length; i++) {
    var filename_ary = chapter_data[chapter_num][i].name.split(".");
    var ext = filename_ary[filename_ary.length - 1];
    if (ext == "jpg" || ext == "jpeg" || ext == "png") {
      reader.readAsDataURL(chapter_data[chapter_num][i]);
      break;
    }
  }
}

function add_chapter_info_to_element(element, chapter_num) {
  var display = document.createElement("div");
  var num_name = "chapter_num_" + chapter_num.toString();
  var num_string = "Chapter Number: ";
  var name_name = "chapter_name_" + chapter_num.toString();
  add_input_to_element(display, "number", num_name, num_string, chapter_num);
  add_input_to_element(display, "text", name_name, "Chapter Name: ");
  element.appendChild(display);
}

function ready_to_submit() {
  for (var chapter_num in total_pages) {
    if (chapter_data[chapter_num].length < total_pages[chapter_num]) {
      return false;
    }
  }
  return true;
}

/* Drag and Drop Helper Methods */

function init_dropzone() {
  document.getElementById("chapter_dropzone").ondragenter = function() {
    this.className = "dragover";
  }
  document.getElementById("chapter_dropzone").ondragleave = function() {
    this.className = "";
  }
}

function get_chapter_from_url(url) {
  var regex = /(\d+)$/
  var split_dir = url.split("/");
  var result = regex.exec(split_dir[split_dir.length - 1]);
  if (result) {
    return Number(result[1]);
  } else {
    return -1;
  }
}

function create_form_data() {
  form_data = new FormData();
  form_data.append("manga_name", manga_name);
  add_chapter_info_to_form();
}

function add_chapter_info_to_form() {
  for (var property in chapter_data) {
    var num = document.getElementsByName("chapter_num_" + property)[0].value;
    var name = document.getElementsByName("chapter_name_" + property)[0].value;
    form_data.append("chapter_num_" + property, num);
    form_data.append("chapter_name_" + property, name);
    for (var i = 0; i < chapter_data[property].length; i++) {
      form_data.append(property.toString(), chapter_data[property][i]);
    }
  }
}

function upload_chapters() {
  var dropzone = document.getElementById("chapter_dropzone");
  dropzone.parentNode.removeChild(dropzone);
  create_form_data();
  var request = new XMLHttpRequest();
  var submit_span = document.getElementById("chapter_submit_button");
  submit_span.className = "chapter_upload";
  request.open('POST', '/add_chapter');
  request.onload = function() {
    text = "Chapters have been updated!"
    text += " Please refresh the page to see the updates.";
    submit_span.innerHTML = text;
  };
  request.upload.onprogress = function(event) {
    if (event.lengthComputable) {
      var complete = (event.loaded / event.total * 100 | 0);
      if (complete == 100) {
        text = "Upload complete! Girls do their best now and are preparing.";
        text += " Please wait warmly until the server is ready...";
        submit_span.innerHTML = text;
      } else {
        submit_span.innerHTML = "Uploaded: " + complete + "%";
      }
    }
  }
  submit_span.innerHTML = "Uploaded: 0%";
  request.send(form_data);
}

/* General Helper Methods */

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

// Initialisation
init_dropzone();
