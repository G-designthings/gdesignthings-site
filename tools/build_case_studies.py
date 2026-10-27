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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = open(os.path.join(ROOT, "process.html"), encoding="utf-8").read()
DATA = json.load(open(os.path.join(ROOT, "case-studies", "case-studies.json"), encoding="utf-8"))


def slice_between(text, start, end, include_end=True):
    i = text.index(start)
    j = text.index(end, i) + (len(end) if include_end else 0)
    return text[i:j]


HEAD_TOP = TPL[: TPL.index("    <title>")]  # doctype .. GTM loader
HEAD_LINKS = slice_between(TPL, '    <link rel="icon" href="img/favicon.ico', '<link rel="stylesheet" href="css/style1.min.css?v=20261026c" />')
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
      .cs-cover { aspect-ratio: 4 / 3; overflow: hidden; background: #11141b; max-width: 100%; }
      .cs-card.is-wide .cs-cover { aspect-ratio: 16 / 9; }
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
      /* single case study */
      .cs-top { display: flex; justify-content: space-between; align-items: center; gap: 16px; font-size: 13px; letter-spacing: 1px; text-transform: uppercase; color: #9a9a9a; margin-bottom: 40px; }
      .cs-top a { color: #9a9a9a; } .cs-top a:hover { color: #BAFF29; text-decoration: none; }
      .cs-facts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px 32px; border-top: 1px solid rgba(255,255,255,0.08); border-bottom: 1px solid rgba(255,255,255,0.08); padding: 24px 0; margin: 36px 0; }
      @media (max-width: 767px) { .cs-facts { grid-template-columns: 1fr 1fr; } }
      .cs-facts dt { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: #9a9a9a; font-weight: 400; }
      .cs-facts dd { margin: 4px 0 0; color: #fff; font-weight: 500; font-size: 15px; }
      .cs-facts dd a { color: #BAFF29; }
      .cs-story { max-width: 720px; font-size: 17px; line-height: 1.75; color: #d6d6d6; margin: 0 0 48px; }
      .cs-book { display: grid; gap: 6px; }
      .cs-book figure { margin: 0; background: #151921; border-radius: 4px; overflow: hidden; }
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
        cards.append(f"""            <a class="cs-card{wide}" href="case-studies/{s['slug']}.html">
              <div class="cs-cover"><img src="{s['cover']}" alt="{html.escape(s['name'])} brand book" loading="{'eager' if i == 0 else 'lazy'}" width="1200" height="{900 if i == 0 else 900}" /></div>
              <span class="cs-tag">{html.escape(s['scope'])}</span>
              <div class="cs-meta"><div><h3>{html.escape(s['name'])}<sup>®</sup></h3><p>{html.escape(s['industry'])}</p></div><span class="arrow">→</span></div>
            </a>""")
    archive = "".join(f"<li>{html.escape(n)}</li>" for n in DATA.get("archive", []))
    body = hero('From Logo to<br /><span style="display: block; font-size: clamp(48px, 15vw, 88px); color: #BAFF29; font-weight: 300; text-transform: none; margin-top: 8px;">Full Brand System.</span>', DATA["intro"], vh=45) + f"""    <main>
    <div class="main-content">
      <section class="section-padding">
        <div class="container">
          <div class="cs-grid">
{chr(10).join(cards)}
          </div>
          <div class="cs-archive">
            <p class="eyebrow">More brand systems</p>
            <ul>{archive}</ul>
          </div>
          <div class="lets text-center" style="margin-top: 60px;">
            <a href="contact.html" class="btn-curve btn-lit"><span>Start a project</span></a>
          </div>
        </div>
      </section>
    </div>
    </main>"""
    out = page("Brand Case Studies | G.designthings", "Brand books by G.designthings. Scroll through the brand identity systems built for clients worldwide, page by page.", "https://www.gdesignthings.com/case-studies.html", body, 0, "case-studies")
    open(os.path.join(ROOT, "case-studies.html"), "w", encoding="utf-8").write(out)


def build_study(s, prev, nxt):
    pages = []
    for n in range(1, s["pages"] + 1):
        src = f"{s['pages_dir']}/{s['pages_prefix']}{n:02d}.webp"
        pages.append(f'            <figure><img src="{src}" alt="{html.escape(s["name"])} brand guidelines, page {n}" loading="{"eager" if n <= 2 else "lazy"}" decoding="async" width="{s["page_width"]}" height="{s["page_height"]}" /></figure>')
    site = ""
    if s.get("url"):
        label = re.sub(r"^https?://(www\.)?", "", s["url"]).rstrip("/")
        site = f'<div><dt>Website</dt><dd><a href="{s["url"]}" target="_blank" rel="noopener">{html.escape(label)}</a></dd></div>'
    else:
        site = f'<div><dt>Year</dt><dd>{html.escape(s.get("year", ""))}</dd></div>'
    body = hero(f'{html.escape(s["name"])}<sup style="font-size:.4em;font-weight:300;color:#BAFF29;vertical-align:top;line-height:1">®</sup><br /><span style="display: block; font-size: clamp(28px, 6vw, 44px); color: #BAFF29; font-weight: 300; text-transform: none; margin-top: 8px;">{html.escape(s["scope"])}.</span>', s["industry"], vh=30) + f"""    <main>
    <div class="main-content">
      <section class="section-padding">
        <div class="container">
          <div class="cs-top"><a href="case-studies.html">← All case studies</a><span>{s['pages']} pages</span></div>
          <p class="cs-story">{html.escape(s['description'])}</p>
          <dl class="cs-facts">
            <div><dt>Client</dt><dd>{html.escape(s['name'])}</dd></div>
            <div><dt>Country</dt><dd>{html.escape(s['country'])}</dd></div>
            <div><dt>Scope</dt><dd>{html.escape(s['scope'])}</dd></div>
            {site}
          </dl>
          <div class="cs-book">
{chr(10).join(pages)}
          </div>
          <div class="cs-pager">
            <a href="{prev['slug']}.html"><div class="lab">← Previous</div><div class="nm">{html.escape(prev['name'])}</div></a>
            <a class="next" href="{nxt['slug']}.html"><div class="lab">Next →</div><div class="nm">{html.escape(nxt['name'])}</div></a>
          </div>
          <div class="lets text-center" style="margin-top: 60px;">
            <p style="color:#ccc; font-size:14px; margin-bottom:18px;">Your brand could be next.</p>
            <a href="contact.html" class="btn-curve btn-lit"><span>Start a project</span></a>
          </div>
        </div>
      </section>
    </div>
    </main>"""
    out = page(f"{s['name']} Brand Book | G.designthings", f"{s['name']} brand identity system by G.designthings. {s['description']}", f"https://www.gdesignthings.com/case-studies/{s['slug']}.html", body, 1, "case-studies", og=s["cover"])
    # inside the case page, Previous/Next links are siblings in the same folder: undo the ../ added by fix_paths
    out = out.replace(f'href="../{prev["slug"]}.html"', f'href="{prev["slug"]}.html"').replace(f'href="../{nxt["slug"]}.html"', f'href="{nxt["slug"]}.html"')
    open(os.path.join(ROOT, "case-studies", f"{s['slug']}.html"), "w", encoding="utf-8").write(out)


if __name__ == "__main__":
    studies = DATA["studies"]
    build_index()
    for i, s in enumerate(studies):
        build_study(s, studies[i - 1], studies[(i + 1) % len(studies)])
    print("built case-studies.html +", len(studies), "case pages")
