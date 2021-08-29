const btnAddLine = document.getElementById("btn-add-tx-line");
const tbodyTxLine = document.getElementById("tx-lines");
btnAddLine.addEventListener("click", addTransactionLine);

function addTransactionLine(ev) {
  let newLine = tbodyTxLine.children[0].cloneNode(true);
  newLine.classList = [""];
  let newId =
    Number(
      tbodyTxLine.children[tbodyTxLine.children.length - 1].id.split("-")[2]
    ) + 1;
  newLine.id = "tx-line-" + newId;
  newLine.children[2].children[1].id = "delete-" + newLine.id;
  //console.log(newLine.children[2].children[1]);
  tbodyTxLine.appendChild(newLine);
}

function deleteTransactionLine(ev) {
  //console.log(ev.id);
  document.getElementById(ev.id.replace("delete-", "")).remove();
}

function updateFile(ev) {
  let inputFile = ev;
  ev.parentNode.children[2].children[0].innerHTML = "";
  ev.parentNode.children[2].children[0].insertAdjacentHTML(
    "beforeend",
    `<a href="${URL.createObjectURL(ev.files[0])}" target="_blank">${
      ev.files[0].name
    }</a>`
  );
  ev.parentNode.children[2].classList = "";
}

const txAttachments = document.getElementById("tx-attachments");
function addFile(ev) {
  let newFile = txAttachments.children[1].cloneNode(true);

  newFile.classList.remove("hidden");
  let newId =
    Number(
      txAttachments.children[
        txAttachments.children.length - 1
      ].children[1].id.split("-")[2]
    ) + 1;
  newFile.id = "div-tx-file-" + newId;
  newFile.children[0].setAttribute("for", "tx-file-" + newId);
  newFile.children[1].id = "tx-file-" + newId;
  newFile.children[2].children[1].id = "delete-" + newFile.children[1].id;
  //console.log(newFile);
  txAttachments.appendChild(newFile);
}

function deleteFile(ev) {
  console.log(ev);

  document.getElementById(ev.id.replace("delete-", "div-")).remove();
}
