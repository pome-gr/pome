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
  document.getElementById(ev.id.replace("delete-", "div-")).remove();
}

const txErrorDiv = document.getElementById("tx-error");
function txError(error) {
  if (error === "") {
    txErrorDiv.classList.add("hidden");
    return;
  }
  txErrorDiv.classList.remove("hidden");
  txErrorDiv.innerText = error;
}

const txDate = document.getElementById("tx-date");
async function generateTxPayload(ev) {
  let theDate = new Date(txDate.value);

  let toReturn = { date: theDate.toISOString().substring(0, 10) };

  toReturn.lines = [];
  // Get lines
  for (line of tbodyTxLine.children) {
    if (
      line.classList.contains("hidden") ||
      !line.children[2].children[0].value
    )
      continue;
    toReturn.lines.push({
      account_dr: line.children[0].children[0].value,
      account_cr: line.children[1].children[0].value,
      raw_amount_in_main_currency: line.children[2].children[0].value,
    });
  }

  toReturn.narrative = document.getElementById("tx-narrative").value;
  toReturn.comments = document.getElementById("tx-comments").value;

  toReturn.files = [];

  for (fileDiv of txAttachments.children) {
    if (
      !fileDiv.id.includes("div-tx-file-") ||
      fileDiv.classList.contains("hidden")
    )
      continue;

    let fileInput = fileDiv.children[1];

    if (fileInput.files[0] === undefined) continue;

    toReturn.files.push({
      filename: fileInput.files[0].name,
      b64_content: await getBase64File(fileInput.files[0]),
    });
  }

  return toReturn;
}

function runTxValidation() {
  const txFirstAmount =
    document.getElementById("tx-line-1").children[2].children[0];
  if (!txDate.checkValidity()) {
    txError("Please select a date.");
    return false;
  }

  if (!txFirstAmount.value) {
    txError("Please enter at least one amount.");
    return false;
  }

  let i = 0;
  for (line of document.getElementById("tx-lines").children) {
    if (!line.children[2].children[0].checkValidity()) {
      txError(
        `Amount ${line.children[2].children[0].value} at line ${i} is invalid. Please use '.' to separate decimals, use at most the maximal number of decimals allowed in your currency (2 for EUR) and do not enter any currency symbol as amounts are set in your main currency.`
      );
      return false;
    }
    i += 1;
  }

  txError("");
  return true;
}

const bntTxRecord = document.getElementById("btn-tx-record");
async function postTxPayload(ev) {
  if (!runTxValidation()) {
    return;
  }

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/transactions/record", true);
  xhr.setRequestHeader("Content-Type", "application/json");

  xhr.send(JSON.stringify(await generateTxPayload()));
  bntTxRecord.classList.add("disabled");
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) return;

    if (this.status !== 200) {
      txError(this.responseText);
    } else {
      txError("");
      window.location = "/transactions/recorded/" + this.responseText;
    }
  };
}
