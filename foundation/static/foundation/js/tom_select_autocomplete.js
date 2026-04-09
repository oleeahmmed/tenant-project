/**
 * Remote Tom Select for <select class="inv-ts-autocomplete" data-autocomplete-url="...">.
 * JSON: { "results": [ { "id": number, "label": string }, ... ] }
 * — Blank default (no "---"), 5 suggestions on open, full search when typing.
 */
(function () {
  var INITIAL_LIMIT = 5;
  var SEARCH_LIMIT = 40;

  function stripDashEmptyLabels(sel) {
    if (!sel || !sel.options) return;
    for (var i = 0; i < sel.options.length; i++) {
      var opt = sel.options[i];
      if (opt.value !== "") continue;
      var txt = (opt.textContent || "").replace(/\u00a0/g, " ").trim();
      if (/^[-–—\s]+$/.test(txt)) opt.textContent = "";
    }
  }

  function initOne(sel) {
    if (!sel || sel.tomselect) return;
    var url = sel.getAttribute("data-autocomplete-url");
    if (!url) return;

    stripDashEmptyLabels(sel);

    var hasBlank =
      sel.querySelector && sel.querySelector('option[value=""]');

    new TomSelect(sel, {
      allowEmptyOption: !!hasBlank,
      maxOptions: null,
      // Must be the string "body", not document.body — Tom Select only runs
      // positionDropdown() when dropdownParent === "body"; otherwise the menu
      // is not positioned and can appear at the bottom of the page.
      dropdownParent: "body",
      wrapperClass: "ts-wrapper inv-ts-premium",
      plugins: ["dropdown_input", "clear_button"],
      preload: false,
      openOnFocus: true,
      placeholder: "",
      hidePlaceholder: true,
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
            callback(
              rows.map(function (x) {
                return { value: String(x.id), text: x.label };
              })
            );
          })
          .catch(function () {
            callback();
          });
      },
      onDropdownOpen: function () {
        var self = this;
        var dd = self.dropdown_content;
        if (dd) {
          var inp = dd.querySelector(".dropdown-input");
          if (inp && !inp.getAttribute("placeholder")) {
            inp.setAttribute("placeholder", "Type to search…");
          }
        }
        if (self._invScrollParent && self._invOnScroll) {
          self._invScrollParent.removeEventListener("scroll", self._invOnScroll);
          self._invScrollParent = null;
          self._invOnScroll = null;
        }
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
        requestAnimationFrame(function () {
          if (self.isOpen) self.positionDropdown();
        });
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

  function initTomSelects(root) {
    var scope = root || document;
    scope.querySelectorAll("select.inv-ts-autocomplete").forEach(initOne);
  }

  window.initFoundationTomSelects = initTomSelects;

  document.addEventListener("DOMContentLoaded", function () {
    initTomSelects(document);
  });
})();
