/* Product images inline: make "is primary" behave like a radio group —
   exactly one image can be the primary at a time. Each row keeps its own
   Django field name (images-N-is_primary) so submission is unchanged; we just
   render them as radios and uncheck the others when one is selected. */
(function () {
  var SEL = 'input[name^="images-"][name$="-is_primary"]';

  function toRadios(root) {
    (root || document).querySelectorAll(SEL).forEach(function (el) {
      if (el.type === 'checkbox') { el.type = 'radio'; }
    });
  }

  document.addEventListener('DOMContentLoaded', function () { toRadios(); });

  // Only one primary: clicking one unchecks the rest (delegation covers
  // dynamically added inline rows too).
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t && t.matches && t.matches(SEL) && t.checked) {
      document.querySelectorAll(SEL).forEach(function (other) {
        if (other !== t) { other.checked = false; }
      });
    }
  });

  // Convert the checkbox in a freshly added inline row.
  document.addEventListener('formset:added', function (e) { toRadios(e.target); });
})();
