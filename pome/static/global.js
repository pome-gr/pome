Element.prototype.remove = function () {
  this.parentElement.removeChild(this);
};
NodeList.prototype.remove = HTMLCollection.prototype.remove = function () {
  for (var i = this.length - 1; i >= 0; i--) {
    if (this[i] && this[i].parentElement) {
      this[i].parentElement.removeChild(this[i]);
    }
  }
};

function getBase64File(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });
}

function getLang() {
  if (navigator.languages != undefined) return navigator.languages[0];
  return navigator.language;
}

function mountDates() {
  let elems = document.querySelectorAll("[data-date]");
  let options = { year: "numeric", month: "long", day: "numeric" };
  for (elem of elems) {
    let theDate = new Date(elem.getAttribute("data-date"));
    let theText = theDate.toLocaleDateString(getLang(), options);

    if (theText !== "Invalid Date") elem.innerText = theText;
  }

  elems = document.querySelectorAll("[data-date-ISO8601]");
  options = {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "numeric",
    second: "numeric",
  };
  for (elem of elems) {
    let theDate = new Date(elem.getAttribute("data-date-ISO8601"));
    console.log(elem.getAttribute("data-date-ISO8601"));
    let theText = theDate.toLocaleString(getLang(), options);

    if (theText !== "Invalid Date") elem.innerText = theText;
  }
}
