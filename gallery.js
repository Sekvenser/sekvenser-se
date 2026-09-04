(function () {
  const triggers = document.querySelectorAll(".gallery-trigger");
  if (!triggers.length) return;

  const modal = document.createElement("div");
  modal.className = "gallery-modal";
  modal.hidden = true;
  modal.innerHTML =
    '<div class="gallery-modal-backdrop"></div>' +
    '<div class="gallery-modal-content" role="dialog" aria-modal="true">' +
    '<button type="button" class="gallery-modal-close" aria-label="Stäng">&times;</button>' +
    '<button type="button" class="gallery-modal-prev" aria-label="Föregående bild">&larr;</button>' +
    '<img class="gallery-modal-img" alt="">' +
    '<button type="button" class="gallery-modal-next" aria-label="Nästa bild">&rarr;</button>' +
    '<p class="gallery-modal-caption"></p>' +
    "</div>";
  document.body.appendChild(modal);

  const img = modal.querySelector(".gallery-modal-img");
  const caption = modal.querySelector(".gallery-modal-caption");
  let images = [];
  let index = 0;
  let lastFocused = null;

  function show() {
    img.src = images[index].src;
    caption.textContent = images[index].alt;
  }

  function open(imgs, startIndex) {
    images = imgs;
    index = startIndex;
    lastFocused = document.activeElement;
    show();
    modal.hidden = false;
    modal.querySelector(".gallery-modal-close").focus();
    document.addEventListener("keydown", onKeydown);
  }

  function close() {
    modal.hidden = true;
    document.removeEventListener("keydown", onKeydown);
    if (lastFocused) lastFocused.focus();
  }

  function prev() {
    index = (index - 1 + images.length) % images.length;
    show();
  }

  function next() {
    index = (index + 1) % images.length;
    show();
  }

  function onKeydown(e) {
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") prev();
    else if (e.key === "ArrowRight") next();
  }

  modal.querySelector(".gallery-modal-close").addEventListener("click", close);
  modal.querySelector(".gallery-modal-backdrop").addEventListener("click", close);
  modal.querySelector(".gallery-modal-prev").addEventListener("click", prev);
  modal.querySelector(".gallery-modal-next").addEventListener("click", next);

  triggers.forEach((btn) => {
    btn.addEventListener("click", () => {
      open(Array.from(btn.closest(".gallery").querySelectorAll("img")), 0);
    });
  });
})();
