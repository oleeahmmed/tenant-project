(function () {
  function parseNum(v) {
    if (v == null) return 0;
    var n = parseFloat(String(v).replace(/,/g, "").trim());
    return Number.isFinite(n) ? n : 0;
  }

  function fmt4(n) {
    return (Math.round((n + Number.EPSILON) * 10000) / 10000).toFixed(4);
  }

  function isAllocationForm(form) {
    return !!form.querySelector("select[name$='-invoice']");
  }

  function ensureSummaryNode(form) {
    var existing = form.querySelector("[data-fin-allocation-summary]");
    if (existing) return existing;
    var footer = form.querySelector(".border-t.border-border.pt-4");
    if (!footer) return null;
    var box = document.createElement("div");
    box.setAttribute("data-fin-allocation-summary", "1");
    box.className = "mr-auto rounded-lg border border-border bg-muted/20 px-3 py-2 text-xs text-muted-foreground";
    box.innerHTML =
      "<span>Allocated: <strong data-fin-allocated class='text-foreground'>0.0000</strong></span> · " +
      "<span>Remaining: <strong data-fin-remaining class='text-foreground'>0.0000</strong></span>";
    footer.prepend(box);
    return box;
  }

  function recalc(form) {
    if (!isAllocationForm(form)) return;
    var totalEl = form.querySelector("#id_amount");
    if (!totalEl) return;
    var total = parseNum(totalEl.value);
    var allocated = 0;
    form.querySelectorAll("input[name$='-amount']").forEach(function (inp) {
      if (inp.id === "id_amount") return;
      allocated += parseNum(inp.value);
    });
    var remaining = total - allocated;
    var box = ensureSummaryNode(form);
    if (!box) return;
    var a = box.querySelector("[data-fin-allocated]");
    var r = box.querySelector("[data-fin-remaining]");
    if (a) a.textContent = fmt4(allocated);
    if (r) {
      r.textContent = fmt4(remaining);
      r.classList.toggle("text-destructive", remaining < 0);
      r.classList.toggle("text-foreground", remaining >= 0);
    }
  }

  document.addEventListener("input", function (ev) {
    var target = ev.target;
    if (!target || !target.closest) return;
    var form = target.closest("form");
    if (!form) return;
    if (target.id === "id_amount" || /-amount$/.test(target.name || "")) {
      recalc(form);
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form").forEach(function (form) {
      recalc(form);
    });
  });
})();

