window.onresize = move_tiles;

function move_tiles() {
  wrapper_width = $("#main_wrapper").width();
  tiles = document.getElementsByClassName("manga_tile")
  columns = 1
  while ((columns + 1) * (tiles[0].offsetWidth + 64) - 64 < wrapper_width) {
    columns += 1
  }
  columns = Math.min(columns, tiles.length);
  total_margin = columns * (tiles[0].offsetWidth + 64) - 64;
  new_margin = (wrapper_width - total_margin) / 2 - 1;
  alert(total_margin)
  alert(new_margin)
  for (i = 0; i < tiles.length; i++) {
    if (i % columns == 0) {
      tiles[i].style.marginLeft = new_margin.toString() + "px"
      tiles[i].style.marginRight = "32px";
    } else if (i % columns == columns - 1) {
      tiles[i].style.marginLeft = "32px";
      tiles[i].style.marginRight = new_margin.toString() + "px"
    } else {
      tiles[i].style.marginLeft = "32px";
      tiles[i].style.marginRight = "32px";
    }
  }
}


move_tiles();
