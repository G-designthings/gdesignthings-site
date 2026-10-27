#!/usr/bin/env python3
"""Build case-studies.html and case-studies/<slug>.html from case-studies/case-studies.json.

Head, nav, footer and the loader scripts are copied from process.html at build time,
so the pages always match the rest of the site. Run from the repo root:

    python3 tools/build_case_studies.py

To add a brand book: put its pages (WebP, 1600px wide) in img/case-studies/<slug>/
plus a cover.webp, add an entry to case-studies.json, run this script.
"""
import html
import json
import os
import re

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


def img_size(rel, default=(1200, 900)):
    if Image is None:
        return default
    try:
        with Image.open(os.path.join(ROOT, rel)) as im:
            return im.size
    except Exception:
        return default

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = open(os.path.join(ROOT, "process.html"), encoding="utf-8").read()
DATA = json.load(open(os.path.join(ROOT, "case-studies", "case-studies.json"), encoding="utf-8"))


def slice_between(text, start, end, include_end=True):
    i = text.index(start)
    j = text.index(end, i) + (len(end) if include_end else 0)
    return text[i:j]


HEAD_TOP = TPL[: TPL.index("    <title>")]  # doctype .. GTM loader
HEAD_LINKS = slice_between(TPL, '    <link rel="icon" href="img/favicon.ico', '<link rel="stylesheet" href="css/style1.min.css?v=')
HEAD_LINKS = TPL[TPL.index(HEAD_LINKS): TPL.index(" />", TPL.index(HEAD_LINKS) + len(HEAD_LINKS)) + 3]
SHARED_CSS = slice_between(TPL, "    /* One CTA style for the whole site */", "    </style>")
BODY_TOP = slice_between(TPL, "  <body>", "    </nav>")
FOOTER = slice_between(TPL, '    <footer class="site-footer">', "  </footer>")
SCRIPTS = slice_between(TPL, "    <script>\n    /* Mobile menu", "  </body>\n</html>")


def fix_paths(s, depth):
    """Rewrite relative asset/page links for a page that lives one folder deeper."""
    if depth == 0:
        return s
    s = re.sub(r'(href|src)="(?!https?:|#|mailto:|tel:)([^"]+)"', r'\1="../\2"', s)
    return s


def nav(active, depth):
    s = BODY_TOP
    # add Case Studies to the menu, after process (if the template does not have it yet)
    if 'href="case-studies.html"' not in s:
      s = s.replace(
        '<li class="nav-item"><a class="nav-link" href="process.html">process</a></li>',
        '<li class="nav-item"><a class="nav-link" href="process.html">process</a></li>\n'
        '            <li class="nav-item"><a class="nav-link" href="case-studies.html">case studies</a></li>',
    )
    s = fix_paths(s, depth)
    return s


CSS = """
      /* Case studies */
      .cs-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
      @media (max-width: 991px) { .cs-grid { grid-template-columns: repeat(2, 1fr); } }
      @media (max-width: 575px) { .cs-grid { grid-template-columns: 1fr; } }
      .cs-card { position: relative; display: flex; flex-direction: column; background: #151921; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; overflow: hidden; color: #fff; transition: border-color .25s ease, transform .25s ease; min-width: 0; }
      .cs-card:hover, .cs-card:focus-visible { border-color: rgba(186,255,41,.5); transform: translateY(-4px); color: #fff; text-decoration: none; outline: none; }
      .cs-card.is-wide { grid-column: span 2; }
      @media (max-width: 575px) { .cs-card.is-wide { grid-column: span 1; } }
      .cs-cover { aspect-ratio: 16 / 9; overflow: hidden; background: #11141b; max-width: 100%; }
      .cs-card.is-wide .cs-cover { aspect-ratio: 16 / 9; }
      @media (min-width: 576px) { .cs-card.is-wide + .cs-card .cs-cover { aspect-ratio: auto; flex: 1; min-height: 0; } }
      .cs-cover img { width: 100%; height: 100%; object-fit: cover; transition: transform .6s ease; }
      .cs-card:hover .cs-cover img { transform: scale(1.04); }
      .cs-tag { position: absolute; top: 14px; left: 14px; background: rgba(12,15,22,.8); border: 1px solid rgba(255,255,255,0.1); border-radius: 30px; padding: 4px 12px; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #BAFF29; }
      .cs-meta { padding: 18px 20px 20px; display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; }
      .cs-meta h3 { margin: 0; font-size: 18px; font-weight: 500; color: #fff; line-height: 1.3; }
      .cs-meta h3 sup { font-size: .55em; font-weight: 300; }
      .cs-meta p { margin: 4px 0 0; color: #9a9a9a; font-size: 13px; }
      .cs-meta .arrow { color: #BAFF29; font-size: 22px; line-height: 1; flex: none; transition: transform .25s ease; }
      .cs-card:hover .arrow { transform: translateX(4px); }
      .cs-archive { margin-top: 60px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 32px; }
      .cs-archive p.eyebrow { margin-bottom: 14px; }
      .cs-archive ul { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 8px; }
      .cs-archive li { border: 1px solid rgba(255,255,255,0.1); border-radius: 30px; padding: 6px 14px; font-size: 12px; letter-spacing: 1px; text-transform: uppercase; color: #9a9a9a; }
      /* reveal on scroll */
      .reveal { opacity: 0; transform: translateY(18px); transition: opacity .7s ease, transform .7s cubic-bezier(.2,.7,.2,1); }
      .reveal.in { opacity: 1; transform: none; }
      @media (prefers-reduced-motion: reduce) { .reveal, .cs-book figure, .cs-hero img, .cs-hero-btn i { transition: none !important; transform: none !important; opacity: 1 !important; } }
      /* single case study */
      .cs-page { padding-top: 110px; }
      .cs-hero { position: relative; display: block; border-radius: 6px; overflow: hidden; background: #151921; margin: 0 0 48px; color: #fff; opacity: 0; transform: translateY(14px); transition: opacity .8s ease, transform .8s cubic-bezier(.2,.7,.2,1); }
      .cs-hero.in { opacity: 1; transform: none; }
      .cs-hero:hover, .cs-hero:focus-visible { color: #fff; text-decoration: none; outline: none; }
      .cs-hero img { width: 100%; height: auto; aspect-ratio: 21 / 9; object-fit: cover; object-position: center; display: block; transition: transform 1.2s cubic-bezier(.2,.7,.2,1); }
      .cs-hero.is-tall img, .cs-cover.is-tall img { object-position: center top; }
      .cs-book.is-single .cs-pages { max-width: 760px; margin: 0 auto; }
      .cs-zoom { display: block; width: 100%; padding: 0; border: 0; background: transparent; cursor: zoom-in; font: inherit; }
      .cs-zoom:focus-visible { outline: 2px solid #BAFF29; outline-offset: -2px; }
      .cs-lightbox { position: fixed; inset: 0; z-index: 9999; background: rgba(8,10,14,.96); display: flex; align-items: center; justify-content: center; padding: 56px 64px; cursor: zoom-out; }
      .cs-lightbox[hidden] { display: none; }
      .cs-lightbox img { max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain; border-radius: 4px; cursor: default; box-shadow: 0 20px 60px rgba(0,0,0,.5); }
      .cs-lightbox button { position: absolute; border: 1px solid rgba(255,255,255,.2); background: rgba(12,15,22,.7); color: #fff; width: 44px; height: 44px; border-radius: 50%; font-size: 26px; line-height: 1; cursor: pointer; display: grid; place-items: center; transition: border-color .2s, color .2s; font-family: inherit; }
      .cs-lightbox button:hover, .cs-lightbox button:focus-visible { border-color: #BAFF29; color: #BAFF29; outline: none; }
      .cs-lb-close { top: 16px; right: 16px; }
      .cs-lb-prev { left: 12px; top: 50%; transform: translateY(-50%); }
      .cs-lb-next { right: 12px; top: 50%; transform: translateY(-50%); }
      .cs-lb-count { position: absolute; bottom: 14px; left: 0; right: 0; text-align: center; margin: 0; font-size: 12px; letter-spacing: 2px; color: #9a9a9a; }
      @media (max-width: 767px) { .cs-lightbox { padding: 60px 8px; } .cs-lb-prev, .cs-lb-next { display: none; } }
      body.cs-lb-open { overflow: hidden; }
      @media (max-width: 767px) { .cs-hero img { aspect-ratio: 3 / 4; } .cs-hero::after { background: linear-gradient(to top, rgba(12,15,22,.96) 0%, rgba(12,15,22,.6) 45%, rgba(12,15,22,.05) 75%); } }
      .cs-hero:hover img { transform: scale(1.03); }
      .cs-hero::after { content: ""; position: absolute; inset: 0; background: linear-gradient(to top, rgba(12,15,22,.92) 0%, rgba(12,15,22,.35) 45%, rgba(12,15,22,0) 75%); }
      .cs-hero-cap { position: absolute; left: 0; right: 0; bottom: 0; z-index: 1; padding: 36px 40px; }
      @media (max-width: 767px) { .cs-hero-cap { padding: 22px 20px; } }
      .cs-hero-cap p.eyebrow { margin-bottom: 8px; }
      .cs-hero-cap h1 { font-size: clamp(36px, 6vw, 64px); font-weight: 500; letter-spacing: -1px; line-height: 1.05; margin: 0 0 6px; color: #fff; }
      .cs-hero-cap h1 sup { font-size: .35em; font-weight: 300; color: #BAFF29; vertical-align: top; line-height: 1; }
      .cs-hero-ind { color: #c8c8c8; font-size: 15px; margin: 0 0 18px; }
      .cs-hero-btn, .cs-open { display: inline-flex; align-items: center; gap: 12px; border: 1px solid #fff; border-radius: 30px; padding: 12px 26px; font-size: 13px; letter-spacing: 2px; text-transform: uppercase; font-weight: 500; color: #fff; background: transparent; font-family: inherit; cursor: pointer; transition: background .25s ease, color .25s ease, border-color .25s ease; }
      .cs-hero-btn i, .cs-open i { font-style: normal; transition: transform .4s ease; }
      .cs-hero:hover .cs-hero-btn, .cs-open:hover, .cs-open:focus-visible { background: #BAFF29; border-color: #BAFF29; color: #0c0f16; outline: none; }
      .cs-hero:hover .cs-hero-btn i, .cs-open:hover i { transform: translateY(3px); }
      .cs-book { position: relative; scroll-margin-top: 24px; }
      .cs-pages { display: grid; gap: 6px; }
      .cs-book figure { margin: 0; background: #151921; border-radius: 4px; overflow: hidden; opacity: 0; transform: translateY(24px); transition: opacity .7s ease, transform .7s cubic-bezier(.2,.7,.2,1); }
      .cs-book figure.in { opacity: 1; transform: none; }
      .cs-book.is-closed .cs-pages { max-height: 520px; overflow: hidden; }
      @media (max-width: 767px) { .cs-book.is-closed .cs-pages { max-height: 300px; } }
      .cs-book.is-closed figure { opacity: 1; transform: none; }
      .cs-book-veil { position: absolute; left: 0; right: 0; bottom: 0; height: 320px; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 12px; padding-bottom: 28px; background: linear-gradient(to bottom, rgba(12,15,22,0) 0%, rgba(12,15,22,.85) 55%, #0c0f16 100%); transition: opacity .5s ease; }
      .cs-book-veil p { margin: 0; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: #9a9a9a; }
      .cs-book:not(.is-closed) .cs-book-veil { opacity: 0; pointer-events: none; }

      .cs-top { display: flex; justify-content: space-between; align-items: center; gap: 16px; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; color: #9a9a9a; margin-bottom: 40px; }
      .cs-top a { color: #9a9a9a; } .cs-top a:hover { color: #BAFF29; text-decoration: none; }
      .cs-facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px 32px; border-top: 1px solid rgba(255,255,255,0.08); border-bottom: 1px solid rgba(255,255,255,0.08); padding: 24px 0; margin: 36px 0; }
      @media (max-width: 767px) { .cs-facts { grid-template-columns: 1fr 1fr; } }
      .cs-facts dt { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #9a9a9a; font-weight: 400; }
      .cs-facts dd { margin: 4px 0 0; color: #fff; font-weight: 500; font-size: 15px; }
      .cs-facts dd a { color: #BAFF29; }
      .cs-story { max-width: 720px; font-size: 17px; line-height: 1.75; color: #d6d6d6; margin: 0 0 48px; }
      .cs-book img { width: 100%; height: auto; display: block; }
      .cs-pager { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 36px; margin-top: 56px; }
      .cs-pager a { display: block; color: #fff; } .cs-pager a:hover { text-decoration: none; }
      .cs-pager .lab { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #9a9a9a; }
      .cs-pager .nm { font-size: 22px; font-weight: 500; margin-top: 6px; }
      .cs-pager .next { text-align: right; }
      .cs-pager a:hover .nm { color: #BAFF29; }
"""


def page(title, desc, canonical, body, depth, active, og=None):
    head = HEAD_TOP + f"    <title>{html.escape(title)}</title>\n" + HEAD_LINKS + "\n\n    <style>\n" + SHARED_CSS.replace("    </style>", "") + CSS + "    </style>\n  </head>\n\n"
    head = head.replace(
        'content="How a G.designthings project moves from first message to finished brand: Brief, Sketch, Digital, Delivery."',
        f'content="{html.escape(desc, quote=True)}"',
    ).replace('href="https://www.gdesignthings.com/process.html"', f'href="{canonical}"')
    head = fix_paths(head, depth)
    if og:
        head = head.replace('content="./img/goran-og-cover.webp"', f'content="https://www.gdesignthings.com/{og}"').replace('content="630"', 'content="840"')
    out = head + nav(active, depth) + "\n\n" + fix_paths(body, depth) + "\n\n" + fix_paths(FOOTER, depth) + "\n\n" + fix_paths(SCRIPTS, depth) + "  </body>\n</html>\n"
    return out


def hero(title_html, sub, vh=60):
    return f"""    <header class="works-header valign" style="min-height: {vh}vh; padding: 110px 0 30px;">
      <div class="container">
        <div class="row justify-content-center">
          <div class="col-lg-9 col-md-11 static">
            <div class="capt mt-50">
              <div class="parlx">
                <h2 class="custom-font-wrong" style="font-weight: 500; font-size: clamp(36px, 9vw, 56px); text-transform: none; text-shadow: none; letter-spacing: -1px; margin-bottom: 5px; line-height: 1.2;">
                  {title_html}
                </h2>
                <p style="margin-top: 20px; max-width: 640px;">{html.escape(sub)}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
"""


def build_index():
    studies = DATA["studies"]
    cards = []
    for i, s in enumerate(studies):
        wide = " is-wide" if i == 0 else ""
        cw, ch = img_size(s["cover"])
        cards.append(f"""            <a class="cs-card reveal{wide}" href="case-studies/{s['slug']}.html" style="transition-delay: {min(i, 8) * 60}ms">
              <div class="cs-cover{' is-tall' if ch > cw else ''}"><img src="{s['cover']}" alt="{html.escape(s['name'])} brand book" loading="{'eager' if i == 0 else 'lazy'}" width="{cw}" height="{ch}" /></div>
              <span class="cs-tag">{html.escape(s['scope'])}</span>
              <div class="cs-meta"><div><h3>{html.escape(s['name'])}<sup>®</sup></h3><p>{html.escape(s['industry'])}</p></div><span class="arrow">→</span></div>
            </a>""")
    archive = "".join(f"<li>{html.escape(n)}</li>" for n in DATA.get("archive", []))
    archive_block = f"""          <div class="cs-archive reveal">
            <p class="eyebrow">More brand systems</p>
            <ul>{archive}</ul>
          </div>
""" if archive else ""
    body = hero('From Logo to<br /><span style="display: block; font-size: clamp(48px, 15vw, 88px); color: #BAFF29; font-weight: 300; text-transform: none; margin-top: 8px;">Full Brand System.</span>', DATA["intro"], vh=45) + f"""    <main>
    <div class="main-content">
      <section class="section-padding">
        <div class="container">
          <div class="cs-grid">
{chr(10).join(cards)}
          </div>
{archive_block}          <div class="lets text-center" style="margin-top: 60px;">
            <a href="contact.html" class="btn-curve btn-lit"><span>Start a project</span></a>
          </div>
        </div>
      </section>
    </div>
    </main>
    <script>
    (function () {{
      var items = document.querySelectorAll(".reveal");
      var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (reduce || !("IntersectionObserver" in window)) {{ items.forEach(function (el) {{ el.classList.add("in"); }}); return; }}
      var io = new IntersectionObserver(function (entries) {{
        entries.forEach(function (en) {{ if (en.isIntersecting) {{ en.target.classList.add("in"); io.unobserve(en.target); }} }});
      }}, {{ rootMargin: "0px 0px -8% 0px", threshold: 0.05 }});
      items.forEach(function (el) {{ io.observe(el); }});
    }})();
    </script>"""
    out = page("Brand Case Studies | G.designthings", "Brand books by G.designthings. Scroll through the brand identity systems built for clients worldwide, page by page.", "https://www.gdesignthings.com/case-studies.html", body, 0, "case-studies")
    open(os.path.join(ROOT, "case-studies.html"), "w", encoding="utf-8").write(out)


def build_study(s, prev, nxt):
    files = s.get("page_files") or [f"{s['pages_dir']}/{s['pages_prefix']}{n:02d}.webp" for n in range(1, s["pages"] + 1)]
    s["pages"] = len(files)
    pages = []
    for n, src in enumerate(files, 1):
        pw, ph = img_size(src, (s["page_width"], s["page_height"]))
        pages.append(f'            <figure><button type="button" class="cs-zoom" data-src="{src}" aria-label="Zoom page {n}"><img src="{src}" alt="{html.escape(s["name"])} brand guidelines, page {n}" loading="{"eager" if n <= 2 else "lazy"}" decoding="async" width="{pw}" height="{ph}" /></button></figure>')
    site = ""
    if s.get("url"):
        label = re.sub(r"^https?://(www\.)?", "", s["url"]).rstrip("/")
        site = f'<div><dt>Website</dt><dd><a href="{s["url"]}" target="_blank" rel="noopener">{html.escape(label)}</a></dd></div>'
    else:
        site = f'<div><dt>Year</dt><dd>{html.escape(s.get("year", ""))}</dd></div>'
    cw, ch = img_size(s["cover"])
    closed = s["pages"] > 3
    veil = f"""            <div class="cs-book-veil">
              <button type="button" class="cs-open" id="cs-open"><span>Open the brand book</span><i>↓</i></button>
              <p>{s['pages']} pages, page by page</p>
            </div>""" if closed else ""
    pager = "" if prev is s else f"""          <div class="cs-pager reveal">
            <a href="{prev['slug']}.html"><div class="lab">← Previous</div><div class="nm">{html.escape(prev['name'])}</div></a>
            <a class="next" href="{nxt['slug']}.html"><div class="lab">Next →</div><div class="nm">{html.escape(nxt['name'])}</div></a>
          </div>"""
    body = f"""    <main>
    <div class="main-content">
      <section class="section-padding cs-page">
        <div class="container">
          <div class="cs-top"><a href="case-studies.html">← All case studies</a><span>{str(s['pages']) + ' pages' if s['pages'] > 1 else html.escape(s['year'])}</span></div>
          <a class="cs-hero{' is-tall' if ch > cw else ''}" href="#book" id="cs-hero" aria-label="Open the {html.escape(s['name'])} brand book">
            <img src="{s['cover']}" alt="{html.escape(s['name'])} brand identity" width="{cw}" height="{ch}" fetchpriority="high" />
            <div class="cs-hero-cap">
              <p class="eyebrow">{html.escape(s['scope'])}</p>
              <h1>{html.escape(s['name'])}<sup>®</sup></h1>
              <p class="cs-hero-ind">{html.escape(s['industry'])}</p>
              <span class="cs-hero-btn"><span>{'Open the brand book' if closed else 'See the work'}</span><i>↓</i></span>
            </div>
          </a>
          <p class="cs-story reveal">{html.escape(s['description'])}</p>
          <dl class="cs-facts reveal">
            <div><dt>Client</dt><dd>{html.escape(s['name'])}</dd></div>
            <div><dt>Country</dt><dd>{html.escape(s['country'])}</dd></div>
            <div><dt>Scope</dt><dd>{html.escape(s['scope'])}</dd></div>
            {site}
          </dl>
          <div class="cs-book{' is-closed' if closed else ''}" id="book">
            <div class="cs-pages">
{chr(10).join(pages)}
            </div>
{veil}
          </div>
{pager}
          <div class="lets text-center reveal" style="margin-top: 60px;">
            <p style="color:#ccc; font-size:14px; margin-bottom:18px;">Your brand could be next.</p>
            <a href="contact.html" class="btn-curve btn-lit"><span>Start a project</span></a>
          </div>
        </div>
      </section>
    </div>
    </main>
    <div class="cs-lightbox" id="cs-lightbox" hidden>
      <button type="button" class="cs-lb-close" id="cs-lb-close" aria-label="Close">×</button>
      <button type="button" class="cs-lb-prev" id="cs-lb-prev" aria-label="Previous page">‹</button>
      <img id="cs-lb-img" src="" alt="" />
      <button type="button" class="cs-lb-next" id="cs-lb-next" aria-label="Next page">›</button>
      <p class="cs-lb-count" id="cs-lb-count"></p>
    </div>
    <script>
    /* Brand book: closed preview, opens on click (hero or button); pages and blocks fade up as they enter the viewport. */
    (function () {{
      var book = document.getElementById("book"), hero = document.getElementById("cs-hero"), btn = document.getElementById("cs-open");
      var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      function openBook(scroll) {{
        if (!book.classList.contains("is-closed")) {{ if (scroll) go(); return; }}
        book.classList.remove("is-closed");
        book.querySelectorAll("figure").forEach(function (f, i) {{ if (i < 6) f.style.transitionDelay = (i * 70) + "ms"; }});
        if (scroll) go();
        window.setTimeout(function () {{ book.querySelectorAll("figure").forEach(function (f) {{ f.style.transitionDelay = ""; }}); }}, 1200);
      }}
      function go() {{ var y = book.getBoundingClientRect().top + window.pageYOffset - 24; window.scrollTo({{ top: y, behavior: reduce ? "auto" : "smooth" }}); }}
      hero.addEventListener("click", function (e) {{ e.preventDefault(); openBook(true); }});
      if (btn) btn.addEventListener("click", function () {{ openBook(false); }});
      if (location.hash === "#book") openBook(true);
      /* reveal on scroll */
      var items = document.querySelectorAll(".reveal, .cs-book figure");
      if (reduce || !("IntersectionObserver" in window)) {{ items.forEach(function (el) {{ el.classList.add("in"); }}); return; }}
      var io = new IntersectionObserver(function (entries) {{
        entries.forEach(function (en) {{ if (en.isIntersecting) {{ en.target.classList.add("in"); io.unobserve(en.target); }} }});
      }}, {{ rootMargin: "0px 0px -8% 0px", threshold: 0.05 }});
      items.forEach(function (el) {{ io.observe(el); }});
      /* hero: show at once */
      window.requestAnimationFrame(function () {{ hero.classList.add("in"); }});
      /* zoom: click a page to open it full screen; arrows and keys move between pages */
      var lb = document.getElementById("cs-lightbox"), lbImg = document.getElementById("cs-lb-img"), lbCount = document.getElementById("cs-lb-count");
      var zooms = Array.prototype.slice.call(document.querySelectorAll(".cs-zoom")), cur = 0;
      function show(i) {{ cur = (i + zooms.length) % zooms.length; lbImg.src = zooms[cur].getAttribute("data-src"); lbImg.alt = zooms[cur].querySelector("img").alt; lbCount.textContent = (cur + 1) + " / " + zooms.length; }}
      function openLb(i) {{ show(i); lb.hidden = false; document.body.classList.add("cs-lb-open"); }}
      function closeLb() {{ lb.hidden = true; document.body.classList.remove("cs-lb-open"); }}
      zooms.forEach(function (z, i) {{ z.addEventListener("click", function () {{ openLb(i); }}); }});
      document.getElementById("cs-lb-close").addEventListener("click", closeLb);
      document.getElementById("cs-lb-prev").addEventListener("click", function () {{ show(cur - 1); }});
      document.getElementById("cs-lb-next").addEventListener("click", function () {{ show(cur + 1); }});
      lb.addEventListener("click", function (e) {{ if (e.target === lb) closeLb(); }});
      document.addEventListener("keydown", function (e) {{ if (lb.hidden) return; if (e.key === "Escape") closeLb(); if (e.key === "ArrowRight") show(cur + 1); if (e.key === "ArrowLeft") show(cur - 1); }});
      var tx = null; lb.addEventListener("touchstart", function (e) {{ tx = e.touches[0].clientX; }}, {{ passive: true }});
      lb.addEventListener("touchend", function (e) {{ if (tx === null) return; var dx = e.changedTouches[0].clientX - tx; tx = null; if (dx > 50) show(cur - 1); if (dx < -50) show(cur + 1); }});
    }})();
    </script>"""
    out = page(f"{s['name']} Brand Book | G.designthings", f"{s['name']} brand identity system by G.designthings. {s['description']}", f"https://www.gdesignthings.com/case-studies/{s['slug']}.html", body, 1, "case-studies", og=s["cover"])
    # inside the case page, Previous/Next links are siblings in the same folder: undo the ../ added by fix_paths
    out = out.replace(f'href="../{prev["slug"]}.html"', f'href="{prev["slug"]}.html"').replace(f'href="../{nxt["slug"]}.html"', f'href="{nxt["slug"]}.html"')
    open(os.path.join(ROOT, "case-studies", f"{s['slug']}.html"), "w", encoding="utf-8").write(out)


def build_home_grid():
    """Brand Systems tab on the home page portfolio: first six brand books + link to all."""
    idx = os.path.join(ROOT, "index.html")
    page_html = open(idx, encoding="utf-8").read()
    start, end = "<!-- cs-home-grid:start -->", "<!-- cs-home-grid:end -->"
    if start not in page_html or end not in page_html:
        return
    cards = []
    for s in DATA["studies"][:6]:
        cw, ch = img_size(s["cover"])
        cards.append(f"""          <a class="cs-card" href="case-studies/{s['slug']}.html">
            <div class="cs-cover{' is-tall' if ch > cw else ''}"><img src="{s['cover']}" alt="{html.escape(s['name'])} brand book" loading="lazy" width="{cw}" height="{ch}" /></div>
            <span class="cs-tag">{html.escape(s['scope'])}</span>
            <div class="cs-meta"><div><h3>{html.escape(s['name'])}<sup>®</sup></h3><p>{html.escape(s['industry'])}</p></div><span class="arrow">→</span></div>
          </a>""")
    block = f"""{start}
        <div class="cs-grid">
{chr(10).join(cards)}
        </div>
        <div class="text-center mt-40">
          <a href="case-studies.html" class="butn butn-md butn-bord radius-30" style="margin: 6px;"><span>See all {len(DATA['studies'])} brand books</span></a>
        </div>
        {end}"""
    i, j = page_html.index(start), page_html.index(end) + len(end)
    open(idx, "w", encoding="utf-8").write(page_html[:i] + block + page_html[j:])


if __name__ == "__main__":
    studies = DATA["studies"]
    build_index()
    build_home_grid()
    for i, s in enumerate(studies):
        build_study(s, studies[i - 1], studies[(i + 1) % len(studies)])
    print("built case-studies.html +", len(studies), "case pages")
