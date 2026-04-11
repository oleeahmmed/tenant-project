(function () {
  function initFilterSelect(sel) {
    if (!sel || sel.tomselect || typeof TomSelect === "undefined") return;
    var url = sel.getAttribute("data-autocomplete-url");
    var valueKey = sel.getAttribute("data-value-key") || "id";
    if (!url) return;

    new TomSelect(sel, {
      allowEmptyOption: true,
      dropdownParent: "body",
      wrapperClass: "ts-wrapper inv-ts-premium",
      maxOptions: 40,
      plugins: ["dropdown_input", "clear_button"],
      preload: true,
      valueField: "value",
      labelField: "text",
      searchField: ["text"],
      load: function (query, callback) {
        var u;
        try {
          u = new URL(url, window.location.origin);
        } catch (e) {
          callback();
          return;
        }
        u.searchParams.set("q", (query || "").trim());
        u.searchParams.set("limit", "40");
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
              rows.map(function (row) {
                var v = row[valueKey];
                return { value: v == null ? "" : String(v), text: row.label || String(v || "") };
              })
            );
          })
          .catch(function () {
            callback();
          });
      },
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("select.inv-filter-autocomplete").forEach(initFilterSelect);
  });
})();

