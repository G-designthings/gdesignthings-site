/* g.designthings 3D layer
   Two scenes built on three.js (js/three.min.js):
   1. hero ring: the portfolio logos circle slowly behind the hero title
   2. portfolio coverflow: draggable 3D row of logos, wired to the All / Monochrome / Colorful filters
   Loads only after first interaction or a few seconds after page load (see index.html).
   If WebGL is missing the page stays exactly as it was: the grid is still in the DOM. */
(function (w, d) {
  "use strict";
  if (!w.THREE) return;

  var THREE = w.THREE;
  var reduced = w.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var isMobile = w.innerWidth < 768;
  var pixelRatio = Math.min(w.devicePixelRatio || 1, isMobile ? 1.5 : 2);

  /* ---------- works, read from the grid so the two stay in sync ---------- */
  var works = [];
  d.querySelectorAll(".portfolio .gallery .items").forEach(function (item) {
    var img = item.querySelector("img");
    if (!img) return;
    works.push({
      large: img.getAttribute("src"),
      small: img.getAttribute("data-small") || img.getAttribute("src"),
      alt: img.getAttribute("alt") || "",
      cat: item.classList.contains("mono") ? "mono" : "color"
    });
  });
  if (!works.length) return;

  function makeRenderer(canvas) {
    try {
      var r = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true, powerPreference: "low-power" });
      r.setPixelRatio(pixelRatio);
      r.outputEncoding = THREE.sRGBEncoding;
      return r;
    } catch (e) { return null; }
  }

  /* rounded-corner alpha mask, matches the 8px radius of the grid cards */
  var maskTex = (function () {
    var s = 512, rad = 26, c = d.createElement("canvas"); c.width = c.height = s;
    var g = c.getContext("2d");
    g.fillStyle = "#000"; g.fillRect(0, 0, s, s);
    g.fillStyle = "#fff"; g.beginPath();
    g.moveTo(rad, 0); g.lineTo(s - rad, 0); g.quadraticCurveTo(s, 0, s, rad);
    g.lineTo(s, s - rad); g.quadraticCurveTo(s, s, s - rad, s);
    g.lineTo(rad, s); g.quadraticCurveTo(0, s, 0, s - rad);
    g.lineTo(0, rad); g.quadraticCurveTo(0, 0, rad, 0); g.closePath(); g.fill();
    var t = new THREE.CanvasTexture(c); return t;
  })();

  function loadTexture(loader, src) {
    var t = loader.load(src);
    t.encoding = THREE.sRGBEncoding;
    t.anisotropy = 4;
    return t;
  }

  function lerp(a, b, k) { return a + (b - a) * k; }

  /* visibility: a scene only renders while on screen and the tab is visible */
  function watch(el, onChange) {
    var visible = true;
    if ("IntersectionObserver" in w) {
      new IntersectionObserver(function (es) { visible = es[0].isIntersecting; onChange(visible && !d.hidden); }, { threshold: 0.02 }).observe(el);
    }
    d.addEventListener("visibilitychange", function () { onChange(visible && !d.hidden); });
  }

  /* =========================================================================
     1. HERO RING
     ========================================================================= */
  (function heroRing() {
    var host = d.querySelector(".mobile-screen");
    if (!host) return;

    var canvas = d.createElement("canvas");
    canvas.className = "hero-3d";
    canvas.setAttribute("aria-hidden", "true");
    host.insertBefore(canvas, host.firstChild);

    var renderer = makeRenderer(canvas);
    if (!renderer) { canvas.remove(); return; }

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    var ring = new THREE.Group();
    ring.rotation.x = 0.1;
    scene.add(ring);

    var n = works.length;
    var R = isMobile ? 3.0 : 6.0;
    var size = isMobile ? 1.25 : 2.2;
    /* on phones the ring sits below the social icons instead of behind the title */
    ring.position.y = isMobile ? -4.3 : 0;

    var manager = new THREE.LoadingManager();
    manager.onLoad = function () { host.classList.add("hero-3d-ready"); };
    var loader = new THREE.TextureLoader(manager);

    var cards = works.map(function (wk, i) {
      var mat = new THREE.MeshBasicMaterial({ map: loadTexture(loader, wk.small), alphaMap: maskTex, transparent: true, side: THREE.DoubleSide });
      var m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), mat);
      var a = (i / n) * Math.PI * 2;
      m.position.set(Math.sin(a) * R, 0, Math.cos(a) * R);
      m.rotation.y = a;
      ring.add(m);
      return m;
    });

    function fit() {
      var wdt = host.clientWidth, hgt = host.clientHeight;
      camera.aspect = wdt / hgt;
      /* phone: camera level with the ring, looking slightly up, so the ring hugs the bottom of the hero */
      camera.position.set(0, isMobile ? -4.3 : 0.4, isMobile ? 14 : 12);
      camera.lookAt(0, isMobile ? -1.1 : 0, 0);
      camera.updateProjectionMatrix();
      renderer.setSize(wdt, hgt, false);
    }
    fit();
    w.addEventListener("resize", fit);

    var kMin = isMobile ? 0.4 : 0.14;   /* on phones nothing sits behind the ring, so it can stay brighter */
    var baseVel = reduced ? 0 : 0.0022;
    var vel = baseVel, drag = false, lastX = 0, tilt = 0, running = true;

    host.addEventListener("pointerdown", function (e) {
      if (e.target.closest("a, button")) return;
      drag = true; lastX = e.clientX;
    });
    w.addEventListener("pointerup", function () { drag = false; });
    w.addEventListener("pointercancel", function () { drag = false; });
    w.addEventListener("pointermove", function (e) {
      if (drag) {
        var dx = e.clientX - lastX; lastX = e.clientX;
        ring.rotation.y += dx * 0.006; vel = dx * 0.0012;
      }
      if (e.pointerType !== "touch") tilt = (e.clientY / w.innerHeight - 0.5) * 0.3;
    }, { passive: true });

    function frame() {
      if (!running) return;
      w.requestAnimationFrame(frame);
      if (!drag) { ring.rotation.y += vel; vel = lerp(vel, baseVel, 0.02); }
      ring.rotation.x = lerp(ring.rotation.x, 0.1 + tilt, 0.05);
      for (var i = 0; i < cards.length; i++) {
        var z = Math.cos(cards[i].rotation.y + ring.rotation.y); /* 1 = nearest the viewer */
        var k = kMin + (1 - kMin) * (1 - (z + 1) / 2);         /* linear space: front cards dim so the lime title stays readable */
        cards[i].material.color.setScalar(k);
      }
      renderer.render(scene, camera);
    }
    frame();
    watch(host, function (on) { if (on && !running) { running = true; frame(); } else if (!on) { running = false; } });
  })();

  /* =========================================================================
     2. PORTFOLIO COVERFLOW
     ========================================================================= */
  (function coverflow() {
    var section = d.querySelector(".portfolio");
    var stage = d.getElementById("gallery-3d");
    var dotsEl = d.querySelector(".gallery-3d-dots");
    if (!section || !stage) return;

    var canvas = d.createElement("canvas");
    canvas.setAttribute("aria-hidden", "true");
    stage.appendChild(canvas);
    var renderer = makeRenderer(canvas);
    if (!renderer) { canvas.remove(); return; }
    section.classList.add("is-3d");

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
    var loader = new THREE.TextureLoader();

    var SP = 4.0;                 /* spacing between cards, world units */
    var cards = works.map(function (wk, i) {
      var mat = new THREE.MeshBasicMaterial({ map: loadTexture(loader, wk.large), alphaMap: maskTex, transparent: true, opacity: 1 });
      var m = new THREE.Mesh(new THREE.PlaneGeometry(3.6, 3.6), mat);
      m.userData = { i: i, cat: wk.cat, alt: wk.alt, on: true, s: 1 };
      scene.add(m);
      return m;
    });

    var order = cards.slice();   /* cards currently shown, in layout order */
    var start = Math.floor((cards.length - 1) / 2);
    var offset = start, target = start, drag = false, moved = 0, lastX = 0, vel = 0, pxPerUnit = 200, running = true;

    function fit() {
      var wdt = stage.clientWidth, hgt = stage.clientHeight;
      camera.aspect = wdt / hgt;
      /* far enough that one card plus two neighbours fit on desktop, about 1.4 cards on a phone */
      camera.position.set(0, 0, isMobile ? 8.6 : 11);
      camera.lookAt(0, 0, 0);
      camera.updateProjectionMatrix();
      renderer.setSize(wdt, hgt, false);
      var visH = 2 * camera.position.z * Math.tan(camera.fov * Math.PI / 360);
      pxPerUnit = hgt / visH;
    }
    fit();
    w.addEventListener("resize", fit);

    /* ---------- dots ---------- */
    function renderDots() {
      if (!dotsEl) return;
      dotsEl.innerHTML = "";
      order.forEach(function (c, k) {
        var b = d.createElement("button");
        b.type = "button"; b.className = "dot"; b.setAttribute("aria-label", c.userData.alt || ("Work " + (k + 1)));
        b.addEventListener("click", function () { target = k; });
        dotsEl.appendChild(b);
      });
    }
    function updateDots() {
      if (!dotsEl) return;
      var k = Math.round(target);
      var ds = dotsEl.children;
      for (var i = 0; i < ds.length; i++) ds[i].classList.toggle("active", i === k);
    }

    /* ---------- filters: reuse the existing All / Monochrome / Colorful buttons ---------- */
    function applyFilter(val) {
      var cat = val === "*" ? null : val.replace(".", "");
      order = cards.filter(function (c) {
        c.userData.on = !cat || c.userData.cat === cat;
        return c.userData.on;
      });
      target = Math.min(Math.round(target), Math.max(order.length - 1, 0));
      renderDots();
    }
    d.querySelectorAll(".portfolio .filtering span").forEach(function (sp) {
      sp.addEventListener("click", function () {
        applyFilter(sp.getAttribute("data-filter") || "*");
        sp.classList.add("active");
        Array.prototype.forEach.call(sp.parentNode.children, function (s) { if (s !== sp) s.classList.remove("active"); });
      });
    });
    renderDots();

    /* ---------- input ---------- */
    stage.addEventListener("pointerdown", function (e) {
      drag = true; moved = 0; lastX = e.clientX; vel = 0;
      stage.setPointerCapture && stage.setPointerCapture(e.pointerId);
    });
    stage.addEventListener("pointermove", function (e) {
      if (!drag) return;
      var dx = e.clientX - lastX; lastX = e.clientX; moved += Math.abs(dx);
      offset -= dx / pxPerUnit / SP;
      vel = -dx / pxPerUnit / SP;
      target = offset;
    });
    function release(e) {
      if (!drag) return;
      drag = false;
      if (moved < 6) {
        /* a tap: jump to the card under the pointer */
        var rect = stage.getBoundingClientRect();
        var u = ((e.clientX - rect.left) - rect.width / 2) / pxPerUnit / SP;
        target = Math.round(offset + u);
      } else {
        target = Math.round(offset + vel * 6);
      }
      target = Math.max(0, Math.min(order.length - 1, target));
    }
    stage.addEventListener("pointerup", release);
    stage.addEventListener("pointercancel", release);
    stage.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { target = Math.min(order.length - 1, Math.round(target) + 1); e.preventDefault(); }
      if (e.key === "ArrowLeft") { target = Math.max(0, Math.round(target) - 1); e.preventDefault(); }
    });
    stage.addEventListener("wheel", function (e) {
      /* horizontal wheel or trackpad swipe browses, vertical wheel keeps scrolling the page */
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        e.preventDefault();
        target = Math.max(0, Math.min(order.length - 1, target + e.deltaX / 120));
      }
    }, { passive: false });

    /* ---------- frame ---------- */
    function frame() {
      if (!running) return;
      w.requestAnimationFrame(frame);
      if (!drag) {
        target = Math.max(0, Math.min(order.length - 1, target));
        offset = lerp(offset, target, reduced ? 1 : 0.1);
        if (!reduced && Math.abs(offset - target) < 0.0005) offset = target;
      }
      var k = 0;
      cards.forEach(function (c) {
        var ud = c.userData, tx, tz, ry, s, op;
        if (ud.on) {
          var dx = k - offset; k++;
          var ad = Math.min(Math.abs(dx), 2.2);
          tx = dx * SP;
          tz = -ad * 1.4;
          ry = -Math.sign(dx) * Math.min(Math.abs(dx), 1) * 0.6;
          s = 1 - ad * 0.1;
          op = 1 - Math.min(ad, 2) * 0.32;
        } else { tx = c.position.x; tz = -6; ry = c.rotation.y; s = 0.001; op = 0; }
        var e = reduced ? 1 : 0.12;
        c.position.x = lerp(c.position.x, tx, e);
        c.position.z = lerp(c.position.z, tz, e);
        c.rotation.y = lerp(c.rotation.y, ry, e);
        ud.s = lerp(ud.s, s, e); c.scale.setScalar(ud.s);
        c.material.opacity = lerp(c.material.opacity, op, e);
        c.visible = c.material.opacity > 0.01;
      });
      updateDots();
      renderer.render(scene, camera);
    }
    frame();
    watch(stage, function (on) { if (on && !running) { running = true; frame(); } else if (!on) { running = false; } });
  })();
})(window, document);
