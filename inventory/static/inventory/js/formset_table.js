/**
 * SAP-style inline formset: table rows + add row / remove line (DELETE checkbox).
 * Expects: [data-inv-formset="PREFIX"], #inv-tpl-PREFIX (template with one <tr>),
 * [data-inv-body="PREFIX"], [name="PREFIX-TOTAL_FORMS"], [data-inv-add="PREFIX"].
 */
(function () {
  function qs(sel, root) {
    return (root || document).querySelector(sel);
  }

  function init(prefix) {
    var totalInput = qs('[name="' + prefix + '-TOTAL_FORMS"]');
    var tbody = qs('[data-inv-body="' + prefix + '"]');
    var tpl = document.getElementById("inv-tpl-" + prefix);
    var addBtn = qs('[data-inv-add="' + prefix + '"]');
    if (!totalInput || !tbody || !tpl || !addBtn) return;

    function renumber() {
      var rows = tbody.querySelectorAll("tr.inv-line-row:not(.inv-line-removed)");
      rows.forEach(function (tr, i) {
        var num = tr.querySelector(".inv-line-num");
        if (num) num.textContent = String(i + 1);
      });
    }

    addBtn.addEventListener("click", function () {
      var idx = parseInt(totalInput.value, 10);
      if (isNaN(idx)) idx = 0;
      var html = tpl.innerHTML.replace(/__prefix__/g, String(idx));
      var wrap = document.createElement("tbody");
      wrap.innerHTML = html.trim();
      var tr = wrap.querySelector("tr");
      if (!tr) return;
      tbody.appendChild(tr);
      totalInput.value = String(idx + 1);
      renumber();
      if (window.lucide && typeof lucide.createIcons === "function") lucide.createIcons();
      if (window.initFoundationTomSelects && typeof window.initFoundationTomSelects === "function") {
        window.initFoundationTomSelects(tr);
      }
      if (window.initInvStockAdjustmentRows && typeof window.initInvStockAdjustmentRows === "function") {
        window.initInvStockAdjustmentRows(tr);
      }
      if (window.initInvDocumentRows && typeof window.initInvDocumentRows === "function") {
        window.initInvDocumentRows(tr);
      }
    });

    tbody.addEventListener("click", function (e) {
      var btn = e.target.closest(".inv-remove-row");
      if (!btn) return;
      var tr = btn.closest("tr");
      if (!tr) return;
      var del = tr.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (del) {
        del.checked = true;
      }
      tr.classList.add("inv-line-removed", "opacity-35", "pointer-events-none");
      tr.style.display = "none";
      renumber();
      if (window.initInvStockAdjustmentRows && typeof window.initInvStockAdjustmentRows === "function") {
        window.initInvStockAdjustmentRows();
      }
      if (window.initInvDocumentRows && typeof window.initInvDocumentRows === "function") {
        window.initInvDocumentRows();
      }
    });

    renumber();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-inv-formset]").forEach(function (el) {
      init(el.getAttribute("data-inv-formset"));
    });
  });
})();
