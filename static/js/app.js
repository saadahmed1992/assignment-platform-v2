document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.getElementById("menuToggle");
  var sidebar = document.getElementById("sidebar");

  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });

    document.addEventListener("click", function (event) {
      if (!sidebar.contains(event.target) && !toggle.contains(event.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  // Role selector on the register page.
  var roleOptions = document.querySelectorAll(".role-option");
  roleOptions.forEach(function (label) {
    var input = label.querySelector("input");
    if (input && input.checked) {
      label.classList.add("checked");
    }
    label.addEventListener("click", function () {
      roleOptions.forEach(function (l) { l.classList.remove("checked"); });
      label.classList.add("checked");
    });
  });

  // Auto-dismiss flash messages after a few seconds.
  var flashes = document.querySelectorAll(".flash");
  flashes.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(function () { el.remove(); }, 400);
    }, 4500);
  });
});
