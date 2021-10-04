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

const PDFErrorDiv = document.getElementById("pdf-error");
function PDFError(error) {
  console.log(error);
  if (error === "") {
    PDFErrorDiv.classList.add("hidden");
    return;
  }
  PDFErrorDiv.classList.remove("hidden");
  PDFErrorDiv.innerText = "PDF Doc Filler Error: " + error;
}

async function generateInvoicePayload(ev) {
  toReturn = {};
  toReturn.status = $('input[name="invoice-status"]:checked').val();
  toReturn.client = $('input[name="invoice-client"]').val();
  toReturn.invoice_number = $('input[name="invoice-number"]').val();
  toReturn.tags = $('input[name="invoice-tags"]').val().split(",");
  toReturn.invoice_counter_increment = document.getElementById(
    "invoice-counter-increment"
  ).checked;
  toReturn.transactions = {};
  toReturn.metadata = {};
  if (document.getElementById("meta-invoice-payload").value.trim() == "") {
    toReturn.metadata.invoice_payload = JSON.parse("{}");
  } else {
    toReturn.metadata.invoice_payload = JSON.parse(
      document.getElementById("meta-invoice-payload").value
    );
  }

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

async function generateInvoicePaymentPayload(ev) {
  toReturn = {};
  toReturn.transactions = {};

  toReturn.transactions.payment = JSON.parse(
    document.getElementById("tx-payment").value
  );

  return toReturn;
}

async function postInvoicePaymentPayload(ev) {
  // if (!runTxValidation()) {
  //   return;
  // }

  var bill_id = window.location.href.substring(
    window.location.href.lastIndexOf("/") + 1
  );
  console.log(bill_id);
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/invoices/pay/" + bill_id, true);
  xhr.setRequestHeader("Content-Type", "application/json");

  xhr.send(JSON.stringify(await generateInvoicePaymentPayload()));
  //btnBillRecord.classList.add("disabled");
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) return;

    if (this.status !== 200) {
      txError(this.responseText);
    } else {
      txError("");
      window.location = "/invoices/recorded/" + bill_id;
    }
  };
}

const btnBillRecord = document.getElementById("btn-bill-record");
async function postInvoicePayload(ev) {
  // if (!runTxValidation()) {
  //   return;
  // }

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/invoices/record", true);
  xhr.setRequestHeader("Content-Type", "application/json");

  xhr.send(JSON.stringify(await generateInvoicePayload()));
  //btnBillRecord.classList.add("disabled");
  xhr.onreadystatechange = function () {
    if (this.readyState != 4) return;

    if (this.status !== 200) {
      txError(this.responseText);
    } else {
      txError("");
      window.location = "/invoices";
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

function postPDFInvoicePayload(ev, doc_filler_URL) {
  if (doc_filler_URL === "") return;

  var xhr = new XMLHttpRequest();
  xhr.open("POST", doc_filler_URL, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.responseType = "blob";
  xhr.send($("#meta-invoice-payload").val());
  //btnBillRecord.classList.add("disabled");

  $("#spinner-PDF").removeClass("hidden");
  $("#pdf-button").addClass("disabled");

  xhr.onreadystatechange = function () {
    if (this.readyState != 4) return;

    $("#spinner-PDF").addClass("hidden");
    $("#pdf-button").removeClass("disabled");

    if (this.status !== 200) {
      const reader = new FileReader();

      // This fires after the blob has been read/loaded.
      reader.addEventListener("loadend", (e) => {
        const text = e.target.result;
        console.log(text);
        PDFError(text);
      });

      // Start reading the blob as text.
      reader.readAsText(this.response);
    } else {
      PDFError("");
      var blob = new Blob([this.response], { type: "application/pdf" });
      var link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download =
        "Invoice_" + $('input[name="invoice-number"]').val() + ".pdf";
      link.click();
    }
  };
}
