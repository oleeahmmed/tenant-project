(function () {
  function fmt(n) {
    if (n === null || n === undefined || isNaN(n)) return "0.00";
    return Number(n).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 8,
    });
  }

  function parseNum(v) {
    var n = parseFloat(String(v || "").replace(/,/g, "").trim());
    return isNaN(n) ? 0 : n;
  }

  function setLineTotal(tr) {
    var qtyEl = tr.querySelector(".inv-line-qty");
    var unitEl = tr.querySelector(".inv-line-unit-cost");
    var totalEl = tr.querySelector(".inv-line-total");
    if (!qtyEl || !unitEl || !totalEl) return;
    var total = parseNum(qtyEl.value) * parseNum(unitEl.value);
    totalEl.value = fmt(total);
  }

  function recalcDocTotals(form) {
    var sum = 0;
    form.querySelectorAll("tr.inv-line-row:not(.inv-line-removed) .inv-line-total").forEach(function (el) {
      sum += parseNum(el.value);
    });
    var subtotalEl = form.querySelector("#inv-doc-subtotal");
    if (subtotalEl) subtotalEl.textContent = fmt(sum);
    var taxEl = form.querySelector("#inv-doc-tax");
    var tax = taxEl ? parseNum(taxEl.textContent) : 0;
    var totalEl = form.querySelector("#inv-doc-total-amount");
    if (totalEl) totalEl.textContent = fmt(sum + tax);
  }

  function getWarehouseId(form) {
    var fieldId = form.getAttribute("data-warehouse-field-id");
    if (!fieldId) return "";
    var el = document.getElementById(fieldId);
    return el && el.value ? String(el.value).trim() : "";
  }

  function fetchDefaultCost(form, tr, productId) {
    var base = form.getAttribute("data-product-context-url");
    if (!base || !productId) return Promise.resolve();
    var u = new URL(base, window.location.origin);
    u.searchParams.set("product_id", productId);
    var wh = getWarehouseId(form);
    if (wh) u.searchParams.set("warehouse_id", wh);
    return fetch(u.toString(), {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    })
      .then(function (r) {
        if (!r.ok) throw new Error("context fetch failed");
        return r.json();
      })
      .then(function (data) {
        var unitEl = tr.querySelector(".inv-line-unit-cost");
        if (unitEl && data.default_unit_cost != null && data.default_unit_cost !== "") {
          unitEl.value = String(data.default_unit_cost);
        }
        setLineTotal(tr);
        recalcDocTotals(form);
      })
      .catch(function () {
        setLineTotal(tr);
        recalcDocTotals(form);
      });
  }

  function bindProductChange(form, tr) {
    var productEl = tr.querySelector(".inv-line-product");
    if (!productEl || productEl._invCostBound) return;
    productEl._invCostBound = true;

    function onChange(val) {
      var productId = String(val || productEl.value || "").trim();
      if (!productId) {
        setLineTotal(tr);
        recalcDocTotals(form);
        return;
      }
      fetchDefaultCost(form, tr, productId);
    }

    if (productEl.tomselect) {
      productEl.tomselect.on("change", onChange);
    } else {
      productEl.addEventListener("change", function () {
        onChange(productEl.value);
      });
    }
  }

  function bindRow(form, tr) {
    if (!tr || tr._invLineBound) return;
    tr._invLineBound = true;
    var qtyEl = tr.querySelector(".inv-line-qty");
    var unitEl = tr.querySelector(".inv-line-unit-cost");
    if (qtyEl) qtyEl.addEventListener("input", function () { setLineTotal(tr); recalcDocTotals(form); });
    if (unitEl) unitEl.addEventListener("input", function () { setLineTotal(tr); recalcDocTotals(form); });
    bindProductChange(form, tr);
    setLineTotal(tr);
    recalcDocTotals(form);
  }

  function bindAll(form, root) {
    var scope = root || form;
    scope.querySelectorAll("tr.inv-line-row").forEach(function (tr) {
      if (!tr.classList.contains("inv-line-removed")) bindRow(form, tr);
    });
  }

  window.initInvDocumentRows = function (root) {
    document.querySelectorAll("form[data-product-context-url][data-warehouse-field-id]").forEach(function (form) {
      bindAll(form, root && form.contains(root) ? root : form);
      recalcDocTotals(form);
    });
  };

  document.addEventListener("DOMContentLoaded", function () {
    window.initInvDocumentRows();

    document.querySelectorAll("form[data-product-context-url][data-warehouse-field-id]").forEach(function (form) {
      var whId = form.getAttribute("data-warehouse-field-id");
      var wh = whId ? document.getElementById(whId) : null;
      if (!wh) return;
      wh.addEventListener("change", function () {
        form.querySelectorAll("tr.inv-line-row .inv-line-product").forEach(function (pSel) {
          var tr = pSel.closest("tr.inv-line-row");
          if (!tr) return;
          var productId = String((pSel.tomselect ? pSel.tomselect.getValue() : pSel.value) || "").trim();
          if (productId) fetchDefaultCost(form, tr, productId);
          else setLineTotal(tr);
        });
        recalcDocTotals(form);
      });
    });
  });
})();
