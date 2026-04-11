(function () {
  function initLocalSelect(sel) {
    if (!sel || sel.tomselect || typeof TomSelect === "undefined") return;
    new TomSelect(sel, {
      allowEmptyOption: true,
      dropdownParent: "body",
      wrapperClass: "ts-wrapper inv-ts-premium",
      maxOptions: 200,
      plugins: ["dropdown_input", "clear_button"],
      create: false,
      persist: false,
      openOnFocus: true,
    });
  }

  function initAll(root) {
    var scope = root || document;
    scope.querySelectorAll("select.inv-ts-local").forEach(initLocalSelect);
  }

  window.initFoundationLocalTomSelects = initAll;
  document.addEventListener("DOMContentLoaded", function () {
    initAll(document);
  });
})();
