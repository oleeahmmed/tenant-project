(function () {
  var cart = [];
  var productSearch = document.getElementById("pos-product-search");
  var productResults = document.getElementById("pos-product-results");
  var cartBody = document.getElementById("pos-cart-body");
  var cartTotalEl = document.getElementById("pos-cart-subtotal");
  var taxEl = document.getElementById("pos-tax");
  var discEl = document.getElementById("pos-discount");
  var grandEl = document.getElementById("pos-grand");
  var payMethodEl = document.getElementById("pos-pay-method");
  var paySplitEl = document.getElementById("pos-pay-split");
  var checkoutBtn = document.getElementById("pos-checkout");
  var csrf = document.querySelector("[name=csrfmiddlewaretoken]");
  var csrfVal = csrf ? csrf.value : "";

  function money(n) {
    var x = parseFloat(n) || 0;
    return x.toFixed(2);
  }

  function recalc() {
    var sub = cart.reduce(function (s, l) {
      return s + parseFloat(l.qty) * parseFloat(l.unit_price);
    }, 0);
    if (cartTotalEl) cartTotalEl.textContent = money(sub);
    var tax = parseFloat(taxEl && taxEl.value ? taxEl.value : "0") || 0;
    var disc = parseFloat(discEl && discEl.value ? discEl.value : "0") || 0;
    var grand = sub + tax - disc;
    if (grandEl) grandEl.textContent = money(grand);
    if (grand < 0) grand = 0;
    return { sub: sub, tax: tax, disc: disc, grand: grand };
  }

  function renderCart() {
    if (!cartBody) return;
    cartBody.innerHTML = "";
    cart.forEach(function (line, idx) {
      var tr = document.createElement("tr");
      tr.className = "border-b border-border";
      tr.innerHTML =
        '<td class="px-2 py-2">' +
        line.name +
        '</td><td class="px-2 py-2"><input type="number" min="0.0001" step="any" class="inv-list-control w-24 pos-qty" data-i="' +
        idx +
        '" value="' +
        line.qty +
        '" /></td><td class="px-2 py-2"><input type="number" min="0" step="0.0001" class="inv-list-control w-28 pos-price" data-i="' +
        idx +
        '" value="' +
        line.unit_price +
        '" /></td><td class="px-2 py-2 text-right">' +
        money(line.qty * line.unit_price) +
        '</td><td class="px-2 py-2"><button type="button" class="text-destructive text-sm pos-remove" data-i="' +
        idx +
        '">Remove</button></td>';
      cartBody.appendChild(tr);
    });
    cartBody.querySelectorAll(".pos-qty").forEach(function (inp) {
      inp.addEventListener("change", function () {
        var i = parseInt(inp.getAttribute("data-i"), 10);
        cart[i].qty = parseFloat(inp.value) || 0;
        renderCart();
        recalc();
      });
    });
    cartBody.querySelectorAll(".pos-price").forEach(function (inp) {
      inp.addEventListener("change", function () {
        var i = parseInt(inp.getAttribute("data-i"), 10);
        cart[i].unit_price = parseFloat(inp.value) || 0;
        renderCart();
        recalc();
      });
    });
    cartBody.querySelectorAll(".pos-remove").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var i = parseInt(btn.getAttribute("data-i"), 10);
        cart.splice(i, 1);
        renderCart();
        recalc();
      });
    });
    recalc();
  }

  function addLine(p) {
    cart.push({
      product_id: p.id,
      name: p.label || p.name,
      qty: 1,
      unit_price: parseFloat(p.list_price) || 0,
    });
    renderCart();
  }

  var searchTimer;
  if (productSearch && productResults) {
    productSearch.addEventListener("input", function () {
      clearTimeout(searchTimer);
      var q = productSearch.value.trim();
      searchTimer = setTimeout(function () {
        if (q.length < 1) {
          productResults.innerHTML = "";
          productResults.classList.add("hidden");
          return;
        }
        fetch("/api/foundation/autocomplete/products/?q=" + encodeURIComponent(q), {
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            productResults.innerHTML = "";
            (data.results || []).forEach(function (p) {
              var a = document.createElement("button");
              a.type = "button";
              a.className =
                "block w-full text-left px-3 py-2 text-sm hover:bg-accent border-b border-border last:border-0";
              a.textContent = p.label + " — " + money(p.list_price);
              a.addEventListener("click", function () {
                addLine(p);
                productSearch.value = "";
                productResults.innerHTML = "";
                productResults.classList.add("hidden");
              });
              productResults.appendChild(a);
            });
            productResults.classList.toggle("hidden", (data.results || []).length === 0);
          })
          .catch(function () {});
      }, 200);
    });
  }

  if (taxEl) taxEl.addEventListener("input", recalc);
  if (discEl) discEl.addEventListener("input", recalc);

  if (checkoutBtn) {
    checkoutBtn.addEventListener("click", function () {
      var t = recalc();
      if (cart.length === 0) {
        alert("Add at least one line.");
        return;
      }
      var pm = payMethodEl ? parseInt(payMethodEl.value, 10) : 0;
      if (!pm) {
        alert("Select a payment method.");
        return;
      }
      var payments = [{ payment_method_id: pm, amount: money(t.grand) }];
      if (paySplitEl && paySplitEl.checked) {
        var secondId = document.getElementById("pos-pay-method-2");
        var secondAmt = document.getElementById("pos-pay-amount-2");
        var p2 = secondId ? parseInt(secondId.value, 10) : 0;
        var a2 = secondAmt ? parseFloat(secondAmt.value) : 0;
        if (p2 && a2 > 0) {
          var a1 = t.grand - a2;
          if (a1 <= 0) {
            alert("Split amounts invalid.");
            return;
          }
          payments = [
            { payment_method_id: pm, amount: money(a1) },
            { payment_method_id: p2, amount: money(a2) },
          ];
        }
      }
      var cust = document.getElementById("pos-customer");
      var customerId = cust && cust.value ? parseInt(cust.value, 10) : null;
      var payload = {
        lines: cart.map(function (l) {
          return {
            product_id: l.product_id,
            quantity: String(l.qty),
            unit_price: String(l.unit_price),
          };
        }),
        payments: payments,
        tax_amount: taxEl && taxEl.value ? taxEl.value : "0",
        discount_amount: discEl && discEl.value ? discEl.value : "0",
      };
      if (customerId) payload.customer_id = customerId;

      checkoutBtn.disabled = true;
      fetch(document.getElementById("pos-checkout-url").value, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfVal,
        },
        body: JSON.stringify(payload),
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          checkoutBtn.disabled = false;
          if (data.ok) {
            window.location.href = data.redirect;
          } else {
            alert(data.error || "Checkout failed.");
          }
        })
        .catch(function () {
          checkoutBtn.disabled = false;
          alert("Network error.");
        });
    });
  }

  renderCart();
})();
