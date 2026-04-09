(function () {
  function pick(row, selectors) {
    for (var i = 0; i < selectors.length; i += 1) {
      var el = row.querySelector(selectors[i]);
      if (el) return el;
    }
    return null;
  }

  function parseNum(v) {
    if (v == null) return 0;
    var n = parseFloat(String(v).replace(/,/g, "").trim());
    return Number.isFinite(n) ? n : 0;
  }

  function fmt4(n) {
    return (Math.round((n + Number.EPSILON) * 10000) / 10000).toFixed(4);
  }

  function recalcRow(row) {
    var q = pick(row, [".fin-line-qty", "input[name$='-quantity']"]);
    var u = pick(row, [".fin-line-unit-price", "input[name$='-unit_price']"]);
    var t = pick(row, [".fin-line-total", "input[name$='-line_total']"]);
    if (!q || !u || !t) return 0;
    var total = parseNum(q.value) * parseNum(u.value);
    t.value = fmt4(total);
    return total;
  }

  function recalcDoc(form) {
    var rows = form.querySelectorAll("tbody tr");
    var subtotal = 0;
    rows.forEach(function (row) {
      subtotal += recalcRow(row);
    });
    var subtotalEl = form.querySelector("#id_subtotal");
    var taxEl = form.querySelector("#id_tax_amount");
    var shippingEl = form.querySelector("#id_shipping_charge");
    var totalEl = form.querySelector("#id_total_amount");
    if (subtotalEl) subtotalEl.value = fmt4(subtotal);
    var tax = taxEl ? parseNum(taxEl.value) : 0;
    var ship = shippingEl ? parseNum(shippingEl.value) : 0;
    if (totalEl) totalEl.value = fmt4(subtotal + tax + ship);
  }

  document.addEventListener("input", function (ev) {
    var target = ev.target;
    if (
      target.classList.contains("fin-line-qty") ||
      target.classList.contains("fin-line-unit-price") ||
      /-quantity$/.test(target.name || "") ||
      /-unit_price$/.test(target.name || "") ||
      target.id === "id_tax_amount" ||
      target.id === "id_shipping_charge"
    ) {
      var form = target.closest("form");
      if (form) recalcDoc(form);
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form").forEach(function (f) {
      if (
        (f.querySelector(".fin-line-qty") && f.querySelector(".fin-line-unit-price")) ||
        (f.querySelector("input[name$='-quantity']") && f.querySelector("input[name$='-unit_price']"))
      ) {
        recalcDoc(f);
      }
    });
  });
})();

