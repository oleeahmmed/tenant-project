/**
 * Stock adjustment: warehouse + product pickers use code/SKU (no FK on document);
 * API fills default unit cost & system qty; counted × unit → line total; sum → doc total.
 */
(function () {
  var INITIAL_LIMIT = 5;
  var SEARCH_LIMIT = 40;

  function fmt(n) {
    if (n === null || n === undefined || isNaN(n)) return "—";
    var x = Number(n);
    return x.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 8 });
  }

  function parseQty(txt) {
    if (txt == null || txt === "" || String(txt).trim() === "—") return null;
    var n = parseFloat(String(txt).replace(/,/g, ""));
    return isNaN(n) ? null : n;
  }

  function getForm() {
    return document.getElementById("inv-doc-form");
  }

  function getContextUrl() {
    var f = getForm();
    return f && f.getAttribute("data-product-context-url");
  }

  function getWarehouseCode() {
    var c = document.getElementById("id_warehouse_code");
    return c && c.value ? String(c.value).trim() : "";
  }

  function setLineTotal(el, value) {
    if (!el) return;
    if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
      el.value = value;
    } else {
      el.textContent = value;
    }
  }

  function recalcRow(tr) {
    if (!tr || tr.classList.contains("inv-line-removed")) return;
    var sysEl = tr.querySelector(".inv-line-system-qty");
    var countedEl = tr.querySelector(".inv-line-counted");
    var unitEl = tr.querySelector(".inv-line-unit-cost");
    var totalEl = tr.querySelector(".inv-line-total");
    if (!countedEl || !unitEl || !totalEl) return;
    var sys = sysEl ? parseQty(sysEl.textContent) : null;
    var counted = parseFloat(countedEl.value);
    if (isNaN(counted)) counted = 0;
    var unit = parseFloat(unitEl.value);
    if (isNaN(unit)) unit = 0;
    var sysN = sys === null ? 0 : sys;
    var diff = counted - sysN;
    var lt = Math.abs(diff) * unit;
    setLineTotal(totalEl, fmt(lt));
  }

  function recalcDocTotal() {
    var form = getForm();
    if (!form) return;
    var sum = 0;
    form.querySelectorAll("tbody tr.inv-line-row:not(.inv-line-removed) .inv-line-total").forEach(function (el) {
      var raw =
        el.tagName === "INPUT" || el.tagName === "TEXTAREA"
          ? el.value
          : el.textContent;
      var v = parseFloat(String(raw).replace(/,/g, ""));
      if (!isNaN(v)) sum += v;
    });
    var subtotalEl = document.getElementById("inv-doc-subtotal");
    if (subtotalEl) subtotalEl.textContent = fmt(sum);

    var taxEl = document.getElementById("inv-doc-tax");
    var tax = 0;
    if (taxEl) {
      var t = parseFloat(String(taxEl.textContent || "0").replace(/,/g, ""));
      if (!isNaN(t)) tax = t;
    }

    var out = document.getElementById("inv-doc-total-amount");
    if (out) out.textContent = fmt(sum + tax);
  }

  function fetchProductContext(tr, productSku) {
    var sysEl = tr.querySelector(".inv-line-system-qty");
    var unitEl = tr.querySelector(".inv-line-unit-cost");
    var base = getContextUrl();
    if (!base || !productSku) return Promise.resolve();

    var u = new URL(base, window.location.origin);
    u.searchParams.set("product_sku", productSku);
    var wc = getWarehouseCode();
    if (wc) u.searchParams.set("warehouse_code", wc);

    return fetch(u.toString(), { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (r) {
        if (!r.ok) throw new Error();
        return r.json();
      })
      .then(function (data) {
        if (sysEl) {
          if (data.qty_on_hand != null) sysEl.textContent = String(data.qty_on_hand);
          else sysEl.textContent = "—";
        }
        if (unitEl && data.default_unit_cost != null && data.default_unit_cost !== "") {
          unitEl.value = String(data.default_unit_cost);
        }
        var hint = [];
        if (data.min_quantity != null) hint.push("Min: " + data.min_quantity);
        if (data.max_quantity != null) hint.push("Max: " + data.max_quantity);
        if (sysEl && hint.length) sysEl.setAttribute("title", hint.join(" · "));
        else if (sysEl) sysEl.removeAttribute("title");
        recalcRow(tr);
        recalcDocTotal();
      })
      .catch(function () {
        if (sysEl) sysEl.textContent = "—";
        recalcRow(tr);
        recalcDocTotal();
      });
  }

  function onProductChange(tr) {
    var skuEl = tr.querySelector(".inv-sa-product-sku");
    var sysEl = tr.querySelector(".inv-line-system-qty");
    var sku = skuEl && skuEl.value ? String(skuEl.value).trim() : "";
    if (!sku) {
      if (sysEl) sysEl.textContent = "—";
      recalcRow(tr);
      recalcDocTotal();
      return;
    }
    fetchProductContext(tr, sku);
  }

  function onWarehouseChange() {
    var form = getForm();
    if (!form) return;
    form.querySelectorAll("tbody tr.inv-line-row:not(.inv-line-removed)").forEach(function (tr) {
      var skuEl = tr.querySelector(".inv-sa-product-sku");
      if (skuEl && skuEl.value && String(skuEl.value).trim()) onProductChange(tr);
      else recalcRow(tr);
    });
    recalcDocTotal();
  }

  function hookTomSelectWarehouse() {
    var wh = document.getElementById("id_warehouse_pick");
    if (!wh) return;
    var url = wh.getAttribute("data-autocomplete-url");
    if (!url || typeof TomSelect === "undefined") return;

    window.__invSaWhMeta = window.__invSaWhMeta || {};

    function applyWarehouse(val) {
      var c = document.getElementById("id_warehouse_code");
      var n = document.getElementById("id_warehouse_name");
      var meta = val && window.__invSaWhMeta ? window.__invSaWhMeta[val] : null;
      if (c) c.value = val || "";
      if (n) n.value = (meta && meta.name) || "";
      onWarehouseChange();
    }

    // If already initialized by generic autocomplete, just attach our behavior.
    if (wh.tomselect) {
      if (!wh._invWhBound) {
        wh._invWhBound = true;
        wh.tomselect.on("change", function (val) {
          applyWarehouse(val);
        });
      }
      return;
    }

    new TomSelect(wh, {
      allowEmptyOption: true,
      maxOptions: null,
      dropdownParent: "body",
      wrapperClass: "ts-wrapper inv-ts-premium",
      plugins: ["dropdown_input", "clear_button"],
      preload: false,
      openOnFocus: true,
      valueField: "value",
      labelField: "text",
      searchField: ["text"],
      shouldLoad: function () {
        return true;
      },
      load: function (query, callback) {
        try {
          var u = new URL(url, window.location.origin);
          var q = (query || "").trim();
          u.searchParams.set("q", q);
          u.searchParams.set("limit", q ? String(SEARCH_LIMIT) : String(INITIAL_LIMIT));
        } catch (e) {
          callback();
          return;
        }
        fetch(u.toString(), {
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            var rows = (data && data.results) || [];
            var opts = rows.map(function (x) {
              window.__invSaWhMeta[x.code] = { name: x.name, id: x.id };
              return { value: x.code, text: x.label };
            });
            callback(opts);
          })
          .catch(function () {
            callback();
          });
      },
      onChange: function (val) {
        applyWarehouse(val);
      },
      onDropdownOpen: function () {
        var self = this;
        var wrap =
          self.wrapper &&
          self.wrapper.closest &&
          self.wrapper.closest(".inv-formset-table-wrap");
        if (wrap) {
          self._invScrollParent = wrap;
          self._invOnScroll = function () {
            if (self.isOpen) self.positionDropdown();
          };
          wrap.addEventListener("scroll", self._invOnScroll, { passive: true });
        }
      },
      onDropdownClose: function () {
        var self = this;
        if (self._invScrollParent && self._invOnScroll) {
          self._invScrollParent.removeEventListener("scroll", self._invOnScroll);
          self._invScrollParent = null;
          self._invOnScroll = null;
        }
      },
    });
  }

  function hookTomSelectProduct(tr, productSel) {
    if (!productSel) return;
    var url = productSel.getAttribute("data-autocomplete-url");
    if (!url || typeof TomSelect === "undefined") return;

    window.__invSaProdMeta = window.__invSaProdMeta || {};

    function applyProduct(val) {
      var skuEl = tr.querySelector(".inv-sa-product-sku");
      var nameEl = tr.querySelector(".inv-sa-product-name");
      var meta = val && window.__invSaProdMeta ? window.__invSaProdMeta[val] : null;
      if (skuEl) skuEl.value = val || "";
      if (nameEl) nameEl.value = (meta && meta.name) || "";
      onProductChange(tr);
    }

    // If already initialized by generic autocomplete, attach our change handler.
    if (productSel.tomselect) {
      if (!productSel._invProdBound) {
        productSel._invProdBound = true;
        productSel.tomselect.on("change", function (val) {
          applyProduct(val);
        });
      }
      return;
    }

    new TomSelect(productSel, {
      allowEmptyOption: true,
      maxOptions: null,
      dropdownParent: "body",
      wrapperClass: "ts-wrapper inv-ts-premium",
      plugins: ["dropdown_input", "clear_button"],
      preload: false,
      openOnFocus: true,
      valueField: "value",
      labelField: "text",
      searchField: ["text"],
      shouldLoad: function () {
        return true;
      },
      load: function (query, callback) {
        try {
          var u = new URL(url, window.location.origin);
          var q = (query || "").trim();
          u.searchParams.set("q", q);
          u.searchParams.set("limit", q ? String(SEARCH_LIMIT) : String(INITIAL_LIMIT));
        } catch (e) {
          callback();
          return;
        }
        fetch(u.toString(), {
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            var rows = (data && data.results) || [];
            var opts = rows.map(function (x) {
              window.__invSaProdMeta[x.sku] = { name: x.name, id: x.id };
              return { value: x.sku, text: x.label };
            });
            callback(opts);
          })
          .catch(function () {
            callback();
          });
      },
      onChange: function (val) {
        applyProduct(val);
      },
      onDropdownOpen: function () {
        var self = this;
        var wrap =
          self.wrapper &&
          self.wrapper.closest &&
          self.wrapper.closest(".inv-formset-table-wrap");
        if (wrap) {
          self._invScrollParent = wrap;
          self._invOnScroll = function () {
            if (self.isOpen) self.positionDropdown();
          };
          wrap.addEventListener("scroll", self._invOnScroll, { passive: true });
        }
      },
      onDropdownClose: function () {
        var self = this;
        if (self._invScrollParent && self._invOnScroll) {
          self._invScrollParent.removeEventListener("scroll", self._invOnScroll);
          self._invScrollParent = null;
          self._invOnScroll = null;
        }
      },
    });
  }

  function bindRow(tr) {
    if (!tr || tr._invStockBound) return;
    tr._invStockBound = true;
    var counted = tr.querySelector(".inv-line-counted");
    var unit = tr.querySelector(".inv-line-unit-cost");
    var productSel = tr.querySelector("select.inv-sa-product-ts");
    function onNum() {
      recalcRow(tr);
      recalcDocTotal();
    }
    if (counted) counted.addEventListener("input", onNum);
    if (unit) unit.addEventListener("input", onNum);
    if (productSel) hookTomSelectProduct(tr, productSel);
  }

  function bindAll(root) {
    var scope = root || document;
    scope.querySelectorAll("tr.inv-line-row").forEach(bindRow);
    recalcDocTotal();
  }

  window.initInvStockAdjustmentRows = function (root) {
    if (root && root.matches && root.matches("tr.inv-line-row")) {
      bindRow(root);
      recalcDocTotal();
      return;
    }
    bindAll(root);
  };

  document.addEventListener("DOMContentLoaded", function () {
    var form = getForm();
    if (!form || !form.querySelector(".inv-line-total")) return;
    hookTomSelectWarehouse();
    bindAll(form);
  });
})();
