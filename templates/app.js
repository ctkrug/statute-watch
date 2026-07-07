/* Statute Watch — client-side filtering over the server-rendered cards.
 *
 * The cards are already in the DOM (progressive enhancement: the page is
 * useful with JS off). This script populates the filter selects from the
 * embedded dataset and shows/hides cards to match. No dependencies.
 */
(function () {
  "use strict";

  var data = (window.__STATUTE_DATA__ && window.__STATUTE_DATA__.statutes) || [];
  var CATEGORY_LABELS = window.__CATEGORY_LABELS__ || {};
  var STAGE_LABELS = window.__STAGE_LABELS__ || {};

  var stateSel = document.getElementById("f-state");
  var catSel = document.getElementById("f-category");
  var stageSel = document.getElementById("f-stage");
  var grid = document.getElementById("grid");
  var empty = document.getElementById("empty");
  var countEl = document.getElementById("result-count");
  var form = document.querySelector(".filters");

  if (!grid) return;

  // --- Populate filter options from the data (distinct, sorted) -----------
  function distinct(values) {
    return Object.keys(
      values.reduce(function (acc, v) {
        acc[v] = true;
        return acc;
      }, {})
    ).sort();
  }

  // Order values present in the data by a canonical label order (e.g. the
  // lifecycle order of stages), falling back to alphabetical for anything the
  // label map does not know about. States have no canonical order -> alphabetical.
  function orderedBy(values, labels) {
    var present = {};
    values.forEach(function (v) { present[v] = true; });
    var known = Object.keys(labels).filter(function (v) { return present[v]; });
    var extra = distinct(values).filter(function (v) { return !(v in labels); });
    return known.concat(extra);
  }

  var states = distinct(data.map(function (s) { return s.state; }));
  var categories = orderedBy(
    data.reduce(function (acc, s) { return acc.concat(s.categories || []); }, []),
    CATEGORY_LABELS
  );
  var stages = orderedBy(data.map(function (s) { return s.stage; }), STAGE_LABELS);

  function addOptions(select, values, labels) {
    values.forEach(function (v) {
      var opt = document.createElement("option");
      opt.value = v;
      opt.textContent = (labels && labels[v]) || v;
      select.appendChild(opt);
    });
  }

  if (stateSel) addOptions(stateSel, states, null);
  if (catSel) addOptions(catSel, categories, CATEGORY_LABELS);
  if (stageSel) addOptions(stageSel, stages, STAGE_LABELS);

  // --- Filtering ----------------------------------------------------------
  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));

  function apply() {
    var state = stateSel ? stateSel.value : "";
    var category = catSel ? catSel.value : "";
    var stage = stageSel ? stageSel.value : "";
    var shown = 0;

    cards.forEach(function (card) {
      var cats = (card.getAttribute("data-categories") || "").split(/\s+/);
      var match =
        (!state || card.getAttribute("data-state") === state) &&
        (!category || cats.indexOf(category) !== -1) &&
        (!stage || card.getAttribute("data-stage") === stage);
      card.hidden = !match;
      if (match) shown += 1;
    });

    if (countEl) countEl.textContent = String(shown);
    if (empty) empty.hidden = shown !== 0;
  }

  [stateSel, catSel, stageSel].forEach(function (sel) {
    if (sel) sel.addEventListener("change", apply);
  });

  if (form) {
    form.addEventListener("reset", function () {
      // Let the native reset land first, then re-apply (now empty) filters.
      window.setTimeout(apply, 0);
    });
  }
})();
