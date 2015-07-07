/* Global Variables */

var curr_page = 1;
var cache = [];

// This will be overwritten by the reader html file
var last_page = 10;
var fullscreen_enabled = false;

var key_triggered = 0;
var page_urls = [];
var previous_chapter = -1;
var next_chapter = -1;

var pan_start_x = -1;
var pan_start_y = -1;

// This is the main image that is displayed by the reader
var manga_image = document.getElementById("manga");

document.body.style.backgroundColor = "rgba(160, 160, 160, 255)";

/* Preload Images */

function preload() {

  lower = Math.max(0, curr_page - 2);
  upper = Math.min(last_page, curr_page + 2);

  for (i = lower; i < upper; i++) {
    // Only preload images that haven't been cached
    if (cache[i]) {
      continue;
    }

    img = new Image();
    img.src = page_urls[i];
    cache[i] = img;
  }

}

/* Input Handling */

document.onkeydown = check_key_down;
document.onkeyup = check_key_up;

function check_key_down(e) {

  e = e || window.event;

  // Down
  if (e.keyCode == '40' && fullscreen_enabled) {
    scroll_down();
  // Left
  } else if (e.keyCode == '37') {
    // Don't do anything if the key has already been triggered
    if (key_triggered != 37) {
      previous_page();
    }
  // Right
  } else if (e.keyCode == '39') {
    // Don't do anything if the key has already been triggered
    if (key_triggered != 39) {
      next_page();
    }
  // Up
  } else if (e.keyCode == '38' && fullscreen_enabled) {
    scroll_up();
  }

  key_triggered = e.keyCode;

}

function check_key_up(e) {

  // Just refresh the key trigger
  e = e || window.event;
  if (e.keyCode == key_triggered) {
    key_triggered = 0;
  }

}

/* Fullscreen Handling */

$(document).on("webkitfullscreenchange mozfullscreenchange fullscreenchange",

  function() {

    fullscreen_enabled = document.fullscreenElement ||
        document.mozFullScreenElement || document.webkitFullscreenElement;
    fullscreen_enabled ? center_image() : revert_image();

  }

);

function launch_fullscreen() {

  element = document.getElementById("fullscreen");

  if (element.requestFullscreen) {
    element.requestFullscreen();
  } else if (element.mozRequestFullScreen) {
    element.mozRequestFullScreen();
  } else if (element.webkitRequestFullscreen) {
    element.webkitRequestFullscreen();
  } else if (element.msRequestFullscreen) {
    element.msRequestFullscreen();
  }

}

function center_image() {

  document.getElementById("fullscreen").style.padding = "0px";

  manga_image.onclick = next_page;
  manga_image.onmousedown = start_pan;
  manga_image.onmousemove = process_pan;
  manga_image.onmouseup = end_pan;
  manga_image.onmouseout = end_pan;
  manga_image.style.maxWidth = "initial";

  resize_image();

  center_width();
  center_height();

}

function revert_image() {

  document.getElementById("fullscreen").style.padding = "32px";

  manga_image.onclick = launch_fullscreen;
  manga_image.onmousedown = null;
  manga_image.onmousemove = null;
  manga_image.onmouseup = null;
  manga_image.onmouseout = null;

  manga_image.style.marginLeft = "auto";
  manga_image.style.marginTop = "auto";
  manga_image.style.height = "initial";
  manga_image.style.width = "initial";
  manga_image.style.maxWidth = "80%";

}

function resize_image() {

  if (cache[curr_page - 1].width > screen.width) {
    // Landscape (usually spreads)
    if (cache[curr_page - 1].width > cache[curr_page - 1].height) {
      // If the height of the original image is greater than the height of
      // the screen
      if (cache[curr_page - 1].height > screen.height) {
        // Clamp the height to the height of the screen, and resize the width
        // of the image to keep the ratio steady
        height_ratio = screen.height / cache[curr_page - 1].height;
        width_num = (cache[curr_page - 1].width * height_ratio);
        manga_image.style.width = width_num.toString() + "px";
        manga_image.style.height = screen.height.toString() + "px";
      } else {
        // Otherwise, do nothing.
        manga_image.style.width = cache[curr_page - 1].width.toString() + "px";
        manga_image.style.height = cache[curr_page - 1].height.toString() + "px";
      }
    } else {
      // Portrait
      width_ratio = screen.width / cache[curr_page].width;
      height_num = cache[curr_page - 1].height * width_ratio;
      manga_image.style.width = screen.width.toString() + "px";
      manga_image.style.height = height_num.toString() + "px";
    }
  } else {
    manga_image.style.width = cache[curr_page - 1].width.toString() + "px";
    manga_image.style.height = cache[curr_page - 1].height.toString() + "px";
  }

}

function center_width() {

  manga_image.style.marginLeft = "0px";

  if (parseInt(manga_image.style.width) < screen.width) {
    x_pos = (screen.width - parseInt(manga_image.style.width)) / 2;
    manga_image.style.marginLeft = x_pos.toString() + "px";
  }

}

function center_height() {

  manga_image.style.marginTop = "0px";

  if (parseInt(manga_image.style.height) < screen.height) {
    y_pos = (screen.height - parseInt(manga_image.style.height)) / 2;
    manga_image.style.marginTop = y_pos.toString() + "px";
  }

}

/* Fullscreen Controls */

function scroll_down() {

  manga_image = document.getElementById("manga");

  // Only scroll if the page is greater than the height of the screen
  if (parseInt(manga_image.style.height) > screen.height) {
    max_margin = screen.height - parseInt(manga_image.style.height);
    new_margin = Math.max(max_margin,
        parseInt(manga_image.style.marginTop) - 32)
    manga_image.style.marginTop = new_margin.toString() + "px";
  }

}

function scroll_up() {

  manga_image = document.getElementById("manga");

  // Only scroll if the page is greater than the height of the screen
  if (parseInt(manga_image.style.height) > screen.height) {
    new_margin = Math.min(0, parseInt(manga_image.style.marginTop) + 32)
    manga_image.style.marginTop = new_margin.toString() + "px";
  }

}

/* Mouse Scroll */

manga_image.addEventListener("mousewheel", scroll_mouse, false);
manga_image.addEventListener("DOMMouseScroll", scroll_mouse, false);

function scroll_mouse(event) {

	delta = Math.max(-1, Math.min(1, (event.wheelDelta || -event.detail)));

  if (delta == -1) {
    scroll_down();
  } else if (delta == 1) {
    scroll_up();
  }

}

/* Mouse Panning */

function start_pan(event) {

  pan_start_x = event.clientX;
  pan_start_y = event.clientY;

}

function process_pan(event) {

  if (pan_start_x >= 0 && pan_start_y >= 0) {
    x_diff = event.clientX - pan_start_x;
    y_diff = event.clientY - pan_start_y;

    dest_x = parseInt(manga_image.style.marginLeft) + x_diff
    dest_y = parseInt(manga_image.style.marginTop) + y_diff

    // Only pan horizontally if the width of the page is greater
    // than the width of the screen
    if (parseInt(manga_image.style.width) > screen.width) {
      max_margin = screen.width - parseInt(manga_image.style.width);
      new_margin = Math.max(Math.min(0, dest_x), max_margin);
      manga_image.style.marginLeft = new_margin.toString() + "px";
    }

    // Only scroll if the height of the page is greater than the
    // height of the screen
    if (parseInt(manga_image.style.height) > screen.height) {
      max_margin = screen.height - parseInt(manga_image.style.height);
      new_margin = Math.max(Math.min(0, dest_y), max_margin);
      manga_image.style.marginTop = new_margin.toString() + "px";
    }

    pan_start_x = event.clientX;
    pan_start_y = event.clientY;
  }

}

function end_pan() {

  pan_start_x = -1;
  pan_start_y = -1;

}

/* Chapter Handling */
function goto_chapter(chapter) {
  current_url = window.location.href;
  window.location.href = current_url.replace(/\d+$/, chapter);
}

/* Page Handling */

function goto_page(page) {

  curr_page = page;
  manga_image.src = page_urls[curr_page - 1];

  fullscreen_enabled ? center_image() : window.scrollTo(0, 0);
  preload();
  update_navbar_page();

}

function next_page() {

  if (curr_page < last_page) {
    goto_page(curr_page + 1);
  } else {
    if (parseInt(next_chapter) >= 0) {
      goto_chapter(next_chapter);
    }
  }

}

function previous_page() {

  if (curr_page > 1) {
    goto_page(curr_page - 1);
  }

}

function update_navbar_page() {

  dropdown = document.getElementById("dropdown_page")
  document.getElementById("page_num").innerHTML = curr_page.toString();

  start_page = Math.max(curr_page - 3, 2)

  if (start_page == 2) {
    end_page = Math.min(8, last_page - 1)
  } else {
    end_page = Math.min(curr_page + 3, last_page - 1)
  }

  if (end_page == last_page - 1) {
    start_page = Math.max(last_page - 1 - 6, 2);
  }

  dropdown.innerHTML = "";

  // First Page
  dropdown.innerHTML += "<a href='#' onclick='goto_page(1)'>" +
      "<li>Page 1 (First)</li></a>";

  for (i = start_page; i <= end_page; i++) {
    dropdown.innerHTML += "<a href='#' onclick='goto_page(" + i.toString() +
        ")'>" + "<li>Page " + i.toString() + "</li></a>";
  }

  // And Last Page
  dropdown.innerHTML +=
      "<a href='#' onclick='goto_page(" + last_page.toString() +
      ")'>" + "<li>Page " + last_page.toString() + " (Last)</li></a>";

}
