(function () {
  "use strict";

  var form = document.getElementById("analyze-form");
  var fileInput = document.getElementById("file-input");
  var dropzone = document.getElementById("dropzone");
  var submitBtn = document.getElementById("submit-btn");
  var loading = document.getElementById("loading");
  var results = document.getElementById("results");
  var errorToast = document.getElementById("error-toast");

  var selectedFile = null;

  function showToast(message) {
    if (!errorToast) return;
    errorToast.textContent = message;
    errorToast.classList.remove("hidden");
    errorToast.classList.add("visible");
    setTimeout(function () {
      errorToast.classList.remove("visible");
    }, 4500);
  }

  function enableSubmit() {
    if (submitBtn) submitBtn.disabled = !selectedFile;
  }

  function setFile(file) {
    selectedFile = file;
    if (!dropzone) { enableSubmit(); return; }
    var textEl = dropzone.querySelector(".dropzone-text");
    var titleEl = dropzone.querySelector(".dropzone-title");
    var formWrap = document.querySelector(".styling-form");
    if (file) {
      dropzone.classList.add("has-file");
      if (textEl) textEl.innerHTML = "Selected: <strong>" + file.name + "</strong>";
      if (titleEl) titleEl.textContent = "Selected: " + file.name;
      if (formWrap) formWrap.classList.remove("hidden");
    } else {
      dropzone.classList.remove("has-file");
      if (textEl) textEl.innerHTML = 'Drag & drop your photo here, or <strong>click to browse</strong>';
      if (titleEl) titleEl.textContent = "Drag & Drop Your Photo";
      if (formWrap) formWrap.classList.add("hidden");
      if (fileInput) fileInput.value = "";
    }
    enableSubmit();
  }

  if (dropzone) {
    dropzone.addEventListener("click", function (e) {
      if (e.target.closest(".btn-choose")) return;
      fileInput.click();
    });
  }

  var choosePhotoBtn = document.getElementById("choose-photo-btn");
  if (choosePhotoBtn) {
    choosePhotoBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropzone) {
    dropzone.addEventListener("dragover", function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
    dropzone.addEventListener("drop", function (e) {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
      var files = e.dataTransfer && e.dataTransfer.files;
      if (files && files.length) {
        var f = files[0];
        var ext = (f.name.split(".").pop() || "").toLowerCase();
        if (["png", "jpg", "jpeg", "gif", "webp"].indexOf(ext) === -1) {
          showToast("Invalid file type. Use PNG, JPG, JPEG, GIF or WebP.");
          return;
        }
        if (f.size > 10 * 1024 * 1024) {
          showToast("File too large. Maximum size is 10MB.");
          return;
        }
        setFile(f);
        if (fileInput) fileInput.files = files;
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", function () {
      var files = fileInput.files;
      if (files && files.length) {
        setFile(files[0]);
      } else {
        setFile(null);
      }
    });
  }

  if (form) form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!selectedFile) return;

    var gender = form.querySelector('input[name="gender"]:checked');
    gender = gender ? gender.value : "Female";

    var fd = new FormData();
    fd.append("image", selectedFile);
    fd.append("gender", gender);

    if (loading) loading.classList.remove("hidden");
    if (results) results.classList.add("hidden");
    if (submitBtn) submitBtn.disabled = true;

    fetch("/analyze", {
      method: "POST",
      body: fd,
    })
      .then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) throw new Error(data.error || "Request failed");
          return data;
        });
      })
      .then(function (data) {
        if (loading) loading.classList.add("hidden");
        if (submitBtn) submitBtn.disabled = false;
        renderResults(data);
        if (results) { results.classList.remove("hidden"); results.scrollIntoView({ behavior: "smooth", block: "start" }); }
      })
      .catch(function (err) {
        if (loading) loading.classList.add("hidden");
        if (submitBtn) submitBtn.disabled = false;
        enableSubmit();
        if (errorToast) showToast(err.message || "Something went wrong. Please try again.");
      });
  });

  function renderResults(data) {
    var r = data.r;
    var g = data.g;
    var b = data.b;
    var rgb = data.rgb || [r, g, b];

    document.getElementById("skin-tone-badge").textContent = data.skin_tone || "—";
    document.getElementById("face-message").textContent = data.message || "";
    document.getElementById("rgb-values").textContent =
      "R " + (rgb[0] ?? r) + " · G " + (rgb[1] ?? g) + " · B " + (rgb[2] ?? b);
    document.getElementById("rgb-swatch").style.backgroundColor =
      "rgb(" + (rgb[0] ?? r) + "," + (rgb[1] ?? g) + "," + (rgb[2] ?? b) + ")";

    var rec = data.recommendations || {};
    document.getElementById("reasoning-text").textContent =
      rec.reasoning || "Recommendations are tailored to your skin tone and gender.";

    var palette = rec.color_palette || {};
    var paletteGrid = document.getElementById("palette-grid");
    paletteGrid.innerHTML = "";
    ["primary", "secondary", "accent"].forEach(function (key) {
      var label = key.charAt(0).toUpperCase() + key.slice(1);
      var value = palette[key] || "—";
      var div = document.createElement("div");
      div.className = "palette-item";
      div.innerHTML = "<strong>" + label + "</strong><span>" + value + "</span>";
      paletteGrid.appendChild(div);
    });

    var dressCodes = rec.dress_codes || {};
    var codes = ["formal", "business", "casual", "party"];
    var tabsEl = document.getElementById("outfit-tabs");
    var contentEl = document.getElementById("outfit-content");
    tabsEl.innerHTML = "";
    contentEl.innerHTML = "";

    codes.forEach(function (code, i) {
      var tab = document.createElement("button");
      tab.type = "button";
      tab.className = "outfit-tab" + (i === 0 ? " active" : "");
      tab.textContent = code.charAt(0).toUpperCase() + code.slice(1);
      tab.setAttribute("data-code", code);
      tabsEl.appendChild(tab);

      var panel = document.createElement("div");
      panel.className = "outfit-panel" + (i === 0 ? " active" : "");
      panel.setAttribute("data-code", code);
      var outfit = dressCodes[code] || {};
      panel.innerHTML =
        "<dl>" +
        "<dt>Tops</dt><dd>" + (outfit.tops || "—") + "</dd>" +
        "<dt>Bottoms</dt><dd>" + (outfit.bottoms || "—") + "</dd>" +
        "<dt>Shoes</dt><dd>" + (outfit.shoes || "—") + "</dd>" +
        "</dl>";
      contentEl.appendChild(panel);
    });

    tabsEl.addEventListener("click", function (e) {
      var t = e.target;
      if (!t.classList.contains("outfit-tab")) return;
      tabsEl.querySelectorAll(".outfit-tab").forEach(function (el) {
        el.classList.toggle("active", el === t);
      });
      contentEl.querySelectorAll(".outfit-panel").forEach(function (el) {
        el.classList.toggle("active", el.getAttribute("data-code") === t.getAttribute("data-code"));
      });
    });

    var hair = rec.hairstyle || {};
    document.getElementById("hairstyle-suggestion").textContent =
      hair.suggestion || "—";
    document.getElementById("maintenance-tips").textContent =
      hair.maintenance_tips || "—";

    var acc = rec.accessories || {};
    var accList = document.getElementById("accessories-list");
    accList.innerHTML =
      "<li><strong>Earrings:</strong> " + (acc.earrings || "—") + "</li>" +
      "<li><strong>Necklaces:</strong> " + (acc.necklaces || "—") + "</li>" +
      "<li><strong>Bracelets:</strong> " + (acc.bracelets || "—") + "</li>" +
      "<li><strong>Watches:</strong> " + (acc.watches || "—") + "</li>";

    var links = rec.shopping_links || {};
    var linksEl = document.getElementById("shopping-links");
    linksEl.innerHTML = "";
    Object.keys(links).forEach(function (name) {
      var a = document.createElement("a");
      a.className = "shopping-link";
      a.href = links[name] || "#";
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = name;
      linksEl.appendChild(a);
    });
  }
})();
