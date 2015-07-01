window.onresize = resize_images;

function resize_images() {
  images = document.getElementsByClassName("tile_cover");
  for (i = 0; i < images.length; i++) {
    new_height = window.innerWidth / 1304 * 480;
    images[i].style.height = new_height.toString() + "px";
  }
}

resize_images();
