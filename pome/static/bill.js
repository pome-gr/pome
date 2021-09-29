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

async function generateBillPayload(ev) {
  toReturn = {};
  toReturn.status = $('input[name="bill-status"]:checked').val();
  toReturn.provider = $('input[name="bill-provider"]').val();
  toReturn.transactions = {};

  if (document.getElementById("tx-bill").value.trim() == "") {
    toReturn.transactions.bill = JSON.parse("{}");
  } else {
    toReturn.transactions.bill = JSON.parse(
      document.getElementById("tx-bill").value
    );
  }

  if (toReturn.status == "paid") {
    if (document.getElementById("tx-payment").value.trim() == "") {
      toReturn.transactions.payment = JSON.parse("{}");
    } else {
      toReturn.transactions.payment = JSON.parse(
        document.getElementById("tx-payment").value
      );
    }
  } else
    toReturn.transactions.payment = document.getElementById("tx-payment").value;

  toReturn.transactions.bill.files = [];

  for (fileDiv of txAttachments.children) {
    if (
      !fileDiv.id.includes("div-tx-file-") ||
      fileDiv.classList.contains("hidden")
    )
      continue;

    let fileInput = fileDiv.children[1];

    if (fileInput.files[0] === undefined) continue;

    toReturn.transactions.bill.files.push({
      filename: fileInput.files[0].name,
      b64_content: await getBase64File(fileInput.files[0]),
    });
  }

  return toReturn;
}

async function generateBillPaymentPayload(ev) {
  toReturn = {};
  toReturn.transactions = {};

  toReturn.transactions.payment = JSON.parse(
    document.getElementById("tx-payment").value
  );

  return toReturn;
}

const btnBillRecord = document.getElementById("btn-bill-record");
async function postBillPayload(ev) {
  // if (!runTxValidation()) {
  //   return;
  // }

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/bills/record", true);
  xhr.setRequestHeader("Content-Type", "application/json");

  xhr.send(JSON.stringify(await generateBillPayload()));
  //btnBillRecord.classList.add("disabled");
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) return;

    if (this.status !== 200) {
      txError(this.responseText);
    } else {
      txError("");
      window.location = "/bills";
    }
  };
}

async function postBillPaymentPayload(ev) {
  // if (!runTxValidation()) {
  //   return;
  // }

  var bill_id = window.location.href.substring(
    window.location.href.lastIndexOf("/") + 1
  );
  console.log(bill_id);
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/bills/pay/" + bill_id, true);
  xhr.setRequestHeader("Content-Type", "application/json");

  xhr.send(JSON.stringify(await generateBillPaymentPayload()));
  //btnBillRecord.classList.add("disabled");
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) return;

    if (this.status !== 200) {
      txError(this.responseText);
    } else {
      txError("");
      window.location = "/bills/recorded/" + bill_id;
    }
  };
}
