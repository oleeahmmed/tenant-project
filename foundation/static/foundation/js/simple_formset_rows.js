(function () {
  function reindexRow(row, fromIdx, toIdx) {
    var fromToken = "-" + fromIdx + "-";
    var toToken = "-" + toIdx + "-";
    row.querySelectorAll("input, select, textarea, label").forEach(function (el) {
      ["name", "id", "for"].forEach(function (attr) {
        var v = el.getAttribute(attr);
        if (v && v.indexOf(fromToken) !== -1) {
          el.setAttribute(attr, v.replaceAll(fromToken, toToken));
        }
      });
    });
  }

  function clearRowValues(row) {
    row.querySelectorAll("input, select, textarea").forEach(function (el) {
      var type = (el.getAttribute("type") || "").toLowerCase();
      var name = el.getAttribute("name") || "";
      if (name.endsWith("-id")) {
        el.value = "";
        return;
      }
      if (type === "checkbox") {
        el.checked = false;
        return;
      }
      if (el.tagName === "SELECT") {
        el.selectedIndex = 0;
        if (el.tomselect) {
          el.tomselect.clear(true);
        }
        return;
      }
      if (el.readOnly) {
        el.value = "0.0000";
        return;
      }
      el.value = "";
    });
  }

  function initOne(container) {
    var prefix = container.getAttribute("data-simple-formset");
    if (!prefix) return;
    var totalInput = container.querySelector('input[name="' + prefix + '-TOTAL_FORMS"]');
    var tbody = container.querySelector('tbody[data-simple-formset-body="' + prefix + '"]');
    var addBtn = container.querySelector('[data-simple-formset-add="' + prefix + '"]');
    if (!totalInput || !tbody || !addBtn) return;

    addBtn.addEventListener("click", function () {
      var rows = tbody.querySelectorAll("tr");
      if (!rows.length) return;
      var lastRow = rows[rows.length - 1];
      var fromIdx = parseInt(totalInput.value, 10) - 1;
      var toIdx = parseInt(totalInput.value, 10);
      if (isNaN(fromIdx) || isNaN(toIdx) || fromIdx < 0) return;
      var newRow = lastRow.cloneNode(true);
      reindexRow(newRow, fromIdx, toIdx);
      clearRowValues(newRow);
      tbody.appendChild(newRow);
      totalInput.value = String(toIdx + 1);
      if (window.initFoundationTomSelects) window.initFoundationTomSelects(newRow);
      if (window.initFoundationLocalTomSelects) window.initFoundationLocalTomSelects(newRow);
      if (window.lucide && typeof lucide.createIcons === "function") lucide.createIcons();
    });

    tbody.addEventListener("click", function (e) {
      var btn = e.target.closest(".js-formset-remove-row");
      if (!btn) return;
      var row = btn.closest("tr");
      if (!row) return;
      var del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (del) del.checked = true;
      row.style.display = "none";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-simple-formset]").forEach(initOne);
  });
})();

