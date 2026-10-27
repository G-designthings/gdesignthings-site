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
  var pixelRatio = Math.min(w.devicePixelRatio || 1, isMobile ? 1 : 2);

  /* ---------- works, read from the grid so the two stay in sync ---------- */
  var works = [];
  d.querySelectorAll(".portfolio .gallery .items").forEach(function (item) {
    var img = item.querySelector("img");
    if (!img) return;
    works.push({
      large: img.getAttribute("src"),
      small: img.getAttribute("data-small") || img.getAttribute("src"),
      tiny: (img.getAttribute("data-small") || "").replace("/3d/", "/3d/s/") || img.getAttribute("src"),
      alt: img.getAttribute("alt") || "",
      cat: item.classList.contains("mono") ? "mono" : "color"
    });
  });
  if (!works.length) return;

  function makeRenderer(canvas) {
    try {
      var r = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true, powerPreference: "low-power" });
      /* software WebGL (SwiftShader, llvmpipe, lab tools) would burn the main thread: skip the 3D layer there */
      var gl = r.getContext(), dbg = gl.getExtension("WEBGL_debug_renderer_info");
      var name = dbg ? String(gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL)) : "";
      if (/swiftshader|llvmpipe|software/i.test(name)) { r.dispose(); return null; }
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
    var R = isMobile ? 4.6 : 6.2;
    var size = isMobile ? 2.2 : 2.4;
    /* desktop: the whole ring sits behind the title plane, so the text always reads first */
    ring.position.z = -1.5;
    /* on phones the ring sits below the social icons instead of behind the title */
    ring.position.y = 0;

    var loader = new THREE.TextureLoader();

    var cards = works.map(function (wk, i) {
      var mat = new THREE.MeshBasicMaterial({ alphaMap: maskTex, transparent: true, opacity: 0, side: THREE.DoubleSide });
      mat.map = loader.load(isMobile ? wk.tiny : wk.small, function (tex) {
        tex.encoding = THREE.sRGBEncoding; tex.anisotropy = 4; mat.needsUpdate = true;
        mat.userData.ready = true;                       /* card fades in on its own, see frame() */
        host.classList.add("hero-3d-ready");              /* layer appears with the first texture, not the last */
      });
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
      camera.position.set(0, 0.4, isMobile ? 13 : 12);
      camera.lookAt(0, 0, 0);
      camera.updateProjectionMatrix();
      renderer.setSize(wdt, hgt, false);
    }
    fit();
    w.addEventListener("resize", fit);

    var kMin = 0.08, kMax = 0.85;
    var baseVel = reduced ? 0 : (isMobile ? 0.0016 : 0.0013);
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

    var last = 0;
    function frame(now) {
      if (!running) return;
      w.requestAnimationFrame(frame);
      var dt = Math.min(((now || 0) - last) / 16.7, 3); last = now || 0; if (!dt || dt < 0) dt = 1;
      if (!drag) { ring.rotation.y += vel * dt; vel = lerp(vel, baseVel, 0.02 * dt); }
      ring.rotation.x = lerp(ring.rotation.x, 0.1 + tilt, 0.05);
      for (var i = 0; i < cards.length; i++) {
        var z = Math.cos(cards[i].rotation.y + ring.rotation.y); /* 1 = nearest the viewer */
        var k = kMin + (kMax - kMin) * (1 - (z + 1) / 2);      /* linear space: front cards dim so the lime title stays readable */
        cards[i].material.color.setScalar(k);
        if (cards[i].material.userData.ready && cards[i].material.opacity < 1) cards[i].material.opacity = Math.min(1, cards[i].material.opacity + 0.04 * dt);
      }
      renderer.render(scene, camera);
    }
    frame();
    watch(host, function (on) { if (on && !running) { running = true; frame(); } else if (!on) { running = false; } });
  })();

  /* =========================================================================
     2. COVERFLOWS (portfolio logos + brand systems)
     ========================================================================= */
  function makeMask(aspect) {
    var cw = 512, chh = Math.round(512 / aspect), rad = 26 / aspect >= 26 ? 26 : Math.round(26 * Math.min(1, 1 / aspect) + 10);
    rad = aspect > 1 ? 18 : 26;
    var c = d.createElement("canvas"); c.width = cw; c.height = chh;
    var g = c.getContext("2d");
    g.fillStyle = "#000"; g.fillRect(0, 0, cw, chh);
    g.fillStyle = "#fff"; g.beginPath();
    g.moveTo(rad, 0); g.lineTo(cw - rad, 0); g.quadraticCurveTo(cw, 0, cw, rad);
    g.lineTo(cw, chh - rad); g.quadraticCurveTo(cw, chh, cw - rad, chh);
    g.lineTo(rad, chh); g.quadraticCurveTo(0, chh, 0, chh - rad);
    g.lineTo(0, rad); g.quadraticCurveTo(0, 0, rad, 0); g.closePath(); g.fill();
    return new THREE.CanvasTexture(c);
  }

  function buildFlow(cfg) {
    var section = cfg.section, stage = cfg.stage, dotsEl = cfg.dotsEl, items = cfg.items;
    if (!section || !stage || !items.length) return false;

    var canvas = d.createElement("canvas");
    canvas.setAttribute("aria-hidden", "true");
    stage.appendChild(canvas);
    var renderer = makeRenderer(canvas);
    if (!renderer) { canvas.remove(); return false; }
    if (cfg.readyClass) section.classList.add(cfg.readyClass);

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
    var loader = new THREE.TextureLoader();

    var SP = cfg.sp;                 /* spacing between cards, world units */
    var mask = cfg.mask || maskTex;
    var cards = items.map(function (wk, i) {
      var mat = new THREE.MeshBasicMaterial({ map: loadTexture(loader, isMobile ? wk.small : wk.large), alphaMap: mask, transparent: true, opacity: 1 });
      var m = new THREE.Mesh(new THREE.PlaneGeometry(cfg.planeW, cfg.planeH), mat);
      m.userData = { i: i, cat: wk.cat, alt: wk.alt, url: wk.url, on: true, s: 1 };
      scene.add(m);
      return m;
    });

    var order = cards.slice();   /* cards currently shown, in layout order */
    var start = Math.floor((cards.length - 1) / 2);
    if (cfg.startAt != null) start = cfg.startAt;
    var dir = 1, idleAt = Date.now() + 5000, hover = false;   /* slow self-browsing while nobody touches it */
    var startOffset = start;
    var offset = start, target = start, drag = false, moved = 0, lastX = 0, vel = 0, pxPerUnit = 200, running = true;

    function fit() {
      var wdt = stage.clientWidth, hgt = stage.clientHeight;
      camera.aspect = wdt / hgt;
      camera.position.set(0, 0, isMobile ? cfg.camZMobile : cfg.camZ);
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
        b.addEventListener("click", function () { target = k; touched(); });
        dotsEl.appendChild(b);
      });
    }
    function updateDots() {
      if (!dotsEl) return;
      var k = Math.round(target);
      var ds = dotsEl.children;
      for (var i = 0; i < ds.length; i++) ds[i].classList.toggle("active", i === k);
    }

    /* ---------- filters (logos only): reuse the existing filter buttons ---------- */
    function applyFilter(val) {
      var cat = val === "*" ? null : val.replace(".", "");
      order = cards.filter(function (c) {
        c.userData.on = !cat || c.userData.cat === cat;
        return c.userData.on;
      });
      target = Math.min(Math.round(target), Math.max(order.length - 1, 0));
      renderDots();
    }
    if (cfg.filterButtons) {
      cfg.filterButtons.forEach(function (sp) {
        sp.addEventListener("click", function () {
          applyFilter(sp.getAttribute("data-filter") || "*");
          sp.classList.add("active");
          Array.prototype.forEach.call(sp.parentNode.children, function (s) { if (s !== sp) s.classList.remove("active"); });
        });
      });
    }
    renderDots();

    /* ---------- input ---------- */
    function touched() { idleAt = Date.now() + 9000; }
    stage.addEventListener("pointerenter", function () { hover = true; });
    stage.addEventListener("pointerleave", function () { hover = false; touched(); });
    stage.addEventListener("pointerdown", function (e) {
      touched(); drag = true; moved = 0; lastX = e.clientX; vel = 0; startOffset = offset;
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
        /* a tap: open the centred card, or bring the tapped one to the centre */
        var rect = stage.getBoundingClientRect();
        var u = ((e.clientX - rect.left) - rect.width / 2) / pxPerUnit / SP;
        var idx = Math.round(offset + u);
        idx = Math.max(0, Math.min(order.length - 1, idx));
        if (cfg.tapOpens && idx === Math.round(offset) && order[idx] && order[idx].userData.url) {
          w.location.href = order[idx].userData.url;
          return;
        }
        target = idx;
      } else if (e.pointerType === "touch") {
        /* phone: one swipe moves one card in the swipe direction */
        target = Math.round(startOffset) + (offset > startOffset ? 1 : -1);
      } else {
        target = Math.round(offset + vel * 6);
      }
      target = Math.max(0, Math.min(order.length - 1, target));
    }
    stage.addEventListener("pointerup", release);
    stage.addEventListener("pointercancel", release);
    stage.addEventListener("keydown", function (e) {
      touched();
      if (e.key === "ArrowRight") { target = Math.min(order.length - 1, Math.round(target) + 1); e.preventDefault(); }
      if (e.key === "ArrowLeft") { target = Math.max(0, Math.round(target) - 1); e.preventDefault(); }
      if (cfg.tapOpens && (e.key === "Enter" || e.key === " ")) {
        var c = order[Math.round(target)];
        if (c && c.userData.url) { e.preventDefault(); w.location.href = c.userData.url; }
      }
    });
    stage.addEventListener("wheel", function (e) {
      /* horizontal wheel or trackpad swipe browses, vertical wheel keeps scrolling the page */
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        e.preventDefault(); touched();
        target = Math.max(0, Math.min(order.length - 1, target + e.deltaX / 120));
      }
    }, { passive: false });

    /* ---------- frame ---------- */
    var last = 0;
    function frame(now) {
      if (!running) return;
      w.requestAnimationFrame(frame);
      var dt = Math.min(((now || 0) - last) / 16.7, 3); last = now || 0; if (!dt || dt < 0) dt = 1;
      var eo = 1 - Math.pow(0.9, dt), ec = 1 - Math.pow(0.88, dt);
      if (!drag && !hover && !reduced && order.length > 1 && Math.abs(offset - target) < 0.01 && Date.now() > idleAt) {
        var cur = Math.round(target);
        if (cur >= order.length - 1) dir = -1; else if (cur <= 0) dir = 1;
        target = cur + dir; idleAt = Date.now() + 4000;
      }
      if (!drag) {
        target = Math.max(0, Math.min(order.length - 1, target));
        offset = lerp(offset, target, reduced ? 1 : eo);
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
        var e = reduced ? 1 : ec;
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
    return true;
  }

  function coverflow() {
    var section = d.querySelector(".portfolio");
    buildFlow({
      section: section,
      stage: d.getElementById("gallery-3d"),
      dotsEl: d.querySelector(".gallery-3d-wrap .gallery-3d-dots"),
      items: works,
      planeW: 3.6, planeH: 3.6, sp: 4.0,
      camZ: 11, camZMobile: 9.4,
      readyClass: "is-3d",
      filterButtons: section ? section.querySelectorAll(".filtering span[data-tab=\"logos\"]") : null,
      tapOpens: false
    });
  }

  /* Brand Systems tab: the brand book covers in the same draggable coverflow.
     Built on the first visit to the tab, from the cards already in the grid. */
  var systemsBuilt = false;
  function systemsFlow() {
    if (systemsBuilt) return;
    var section = d.querySelector(".portfolio");
    var stage = d.getElementById("systems-3d");
    var grid = d.getElementById("brand-systems");
    if (!section || !stage || !grid) return;
    var items = [];
    grid.querySelectorAll(".cs-card").forEach(function (a) {
      var img = a.querySelector("img");
      if (!img) return;
      var flow = img.getAttribute("data-flow") || img.getAttribute("src");
      items.push({ large: flow, small: flow, alt: img.getAttribute("alt") || "", url: a.getAttribute("href"), cat: "sys" });
    });
    systemsBuilt = buildFlow({
      section: section,
      stage: stage,
      dotsEl: d.querySelector("#systems-3d-wrap .gallery-3d-dots"),
      items: items,
      planeW: 4.8, planeH: 2.7, sp: 5.2,
      camZ: 12, camZMobile: 10.4,
      readyClass: "is-3d-sys",
      mask: makeMask(16 / 9),
      startAt: 0,
      tapOpens: true
    });
  }
  d.querySelectorAll(".portfolio .filtering span[data-tab=\"systems\"]").forEach(function (sp) {
    sp.addEventListener("click", function () { systemsFlow(); });
  });

  /* The coverflow is built only when the portfolio section gets close to the viewport,
     so the hero never pays for it and the main thread stays free right after load. */
  (function () {
    var section = d.querySelector(".portfolio");
    if (!section) return;
    var started = false;
    function start() { if (started) return; started = true; w.requestAnimationFrame(function () { coverflow(); if (section.classList.contains("show-systems")) systemsFlow(); }); }
    if ("IntersectionObserver" in w) {
      var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { io.disconnect(); start(); } }, { rootMargin: "900px 0px" });
      io.observe(section);
    } else { start(); }
  })();
})(window, document);
