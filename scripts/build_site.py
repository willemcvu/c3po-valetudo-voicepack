#!/usr/bin/env python3
"""Generate the GitHub Pages catalog into docs/.

Scans every pack, emits a self-contained docs/index.html (manifest inlined so it
works from file:// too) and copies each pack's preview audio into docs/samples/.
Designed to scale to a large number of packs: the page is a plain searchable
list, nothing per-character.

    scripts/build_site.py [owner/repo] [branch]

A pack appears as "released" (with install fields) only once it has a built
dist/<name>.tar.gz + dist/HASH.txt; otherwise it is listed as unreleased.

Preview audio: a pack's packs/<name>/preview/*.{ogg,mp3} are published, in name
order. If there is no preview/ dir, samples/demo.ogg is used when present.
"""
import html
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import packlib  # noqa: E402

ROOT = packlib.ROOT
DOCS = ROOT / "docs"
DEFAULT_BRANCH = "main"


def git_slug():
    """owner/repo from the git origin remote, so a repo rename needs no edits.

    CI passes the slug explicitly (${{ github.repository }}); this is only the
    fallback for local runs.
    """
    import re
    import subprocess

    try:
        url = subprocess.run(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "OWNER/REPO"
    m = re.search(r"[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    return m.group(1) if m else "OWNER/REPO"


def preview_files(pdir):
    pv = pdir / "preview"
    if pv.is_dir():
        return sorted(f for f in pv.iterdir() if f.suffix in (".ogg", ".mp3"))
    demo = pdir / "samples" / "demo.ogg"
    return [demo] if demo.exists() else []


def build_manifest(repo, branch):
    packs = []
    for name in packlib.list_packs():
        pdir = packlib.pack_dir(name)
        meta = packlib.load_pack(name).META
        tar = pdir / "dist" / f"{name}.tar.gz"
        hashf = pdir / "dist" / "HASH.txt"
        released = tar.exists() and hashf.exists()

        samples = []
        dest_dir = DOCS / "samples" / name
        for i, f in enumerate(preview_files(pdir)):
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest_dir / f.name)
            samples.append({"label": f.stem.replace("_", " "),
                            "file": f"samples/{name}/{f.name}"})

        entry = {
            "name": name,
            "title": meta.get("title", name),
            "description": meta.get("description", ""),
            "language_code": meta["language_code"],
            "released": released,
            "samples": samples,
        }
        if released:
            entry["hash"] = hashf.read_text().strip()
            entry["size_bytes"] = tar.stat().st_size
            entry["install_url"] = (
                f"https://github.com/{repo}/raw/{branch}/packs/{name}/dist/{name}.tar.gz"
            )
        packs.append(entry)
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "repo": repo,
        "packs": packs,
    }


def render(manifest):
    # Inline JSON in a <script type="application/json"> block. The browser reads
    # script content as raw text and does NOT decode HTML entities, so escape
    # only the characters that could break out of / mis-parse the tag, as JSON
    # \u escapes (valid inside JSON, decoded by JSON.parse).
    data = (json.dumps(manifest)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026"))
    return PAGE.replace("__MANIFEST__", data)


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Valetudo voice packs</title>
<style>
  :root{
    --bg:#ffffff; --fg:#1a1a1a; --muted:#666; --line:#ddd; --card:#fafafa;
    --field:#f0f0f0; --btn:#e8e8e8; --btn-fg:#1a1a1a; --ok:#137a3f;
  }
  @media (prefers-color-scheme:dark){
    :root{
      --bg:#161616; --fg:#e8e8e8; --muted:#9a9a9a; --line:#333; --card:#1e1e1e;
      --field:#262626; --btn:#333; --btn-fg:#e8e8e8; --ok:#4caf6e;
    }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--fg);
    font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  .wrap{max-width:760px;margin:0 auto;padding:24px 16px 64px}
  h1{font-size:20px;margin:0 0 4px}
  .sub{color:var(--muted);margin:0 0 20px;font-size:14px}
  input[type=search]{width:100%;padding:9px 12px;font:inherit;
    border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
  .count{color:var(--muted);font-size:13px;margin:12px 2px}
  .pack{border:1px solid var(--line);border-radius:8px;background:var(--card);
    padding:14px 16px;margin:10px 0}
  .pack h2{font-size:16px;margin:0 0 2px;display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
  .tag{font-size:11px;color:var(--muted);border:1px solid var(--line);
    border-radius:99px;padding:1px 8px;font-weight:400}
  .tag.soon{color:#a67c00;border-color:#a67c0055}
  .desc{color:var(--muted);margin:2px 0 12px;font-size:14px}
  .field{display:flex;align-items:center;gap:8px;margin:6px 0}
  .field label{width:84px;color:var(--muted);font-size:12px;flex:none}
  .field code{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
    background:var(--field);padding:6px 9px;border-radius:5px;font-size:13px}
  button.copy{flex:none;font:inherit;font-size:12px;padding:6px 10px;cursor:pointer;
    border:1px solid var(--line);border-radius:5px;background:var(--btn);color:var(--btn-fg)}
  button.copy.done{color:var(--ok);border-color:var(--ok)}
  .samples{margin:12px 0 2px;display:flex;flex-direction:column;gap:7px}
  .sample{display:flex;align-items:center;gap:10px}
  .sample audio{display:none}
  .slabel{width:84px;flex:none;font-size:12px;color:var(--muted);
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .play{flex:none;width:30px;height:30px;border-radius:50%;cursor:pointer;
    border:1px solid var(--line);background:var(--btn);color:var(--btn-fg);
    font-size:11px;line-height:1;display:flex;align-items:center;justify-content:center;padding:0}
  .play.playing{border-color:var(--ok);color:var(--ok)}
  .bar{flex:1;height:6px;border-radius:3px;background:var(--field);
    position:relative;overflow:hidden;cursor:pointer}
  .fill{position:absolute;left:0;top:0;bottom:0;width:0;background:var(--muted)}
  .time{flex:none;width:36px;text-align:right;font-size:11px;color:var(--muted);
    font-variant-numeric:tabular-nums}
  .how{margin:28px 2px 0;color:var(--muted);font-size:13px}
  .how code{background:var(--field);padding:1px 5px;border-radius:4px}
  footer{margin-top:36px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:12px}
  a{color:inherit}
</style>
</head>
<body>
<div class="wrap">
  <h1>Valetudo voice packs</h1>
  <p class="sub">Custom voice packs for Dreame robots running Valetudo. Pick one, sample it,
     then paste the three fields into <em>Robot Settings &rarr; Misc &rarr; Voice packs</em>.</p>
  <input type="search" id="q" placeholder="Search packs&hellip;" aria-label="Search packs">
  <p class="count" id="count"></p>
  <div id="list"></div>

  <p class="how"><strong>Installing:</strong> in Valetudo, open
     <code>Robot Settings &rarr; Misc Settings &rarr; Voice packs</code>, paste the
     <b>URL</b>, <b>Language Code</b> and <b>Hash</b> below, and press
     <em>Set Voice Pack</em>. To undo, set the language code back to <code>EN</code>.</p>
  <footer id="foot"></footer>
</div>
<script id="data" type="application/json">__MANIFEST__</script>
<script>
const M = JSON.parse(document.getElementById("data").textContent);
const esc = s => (s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmtSize = b => b ? (b/1048576).toFixed(1)+" MB" : "";

function field(label, value){
  return `<div class="field"><label>${label}</label>`+
    `<code title="${esc(value)}">${esc(value)}</code>`+
    `<button class="copy" data-copy="${esc(value)}">Copy</button></div>`;
}

function packHTML(p){
  const soon = p.released ? "" : `<span class="tag soon">not yet released</span>`;
  const install = p.released ? (
    field("URL", p.install_url) +
    field("Language", p.language_code) +
    field("Hash", p.hash)
  ) : "";
  const samples = (p.samples||[]).map(s =>
    `<div class="sample">`+
      `<span class="slabel" title="${esc(s.label)}">${esc(s.label)}</span>`+
      `<button class="play" aria-label="Play ${esc(s.label)}">&#9654;</button>`+
      `<div class="bar"><div class="fill"></div></div>`+
      `<span class="time">0:00</span>`+
      `<audio preload="none" src="${esc(s.file)}"></audio>`+
    `</div>`).join("");
  const size = p.size_bytes ? `<span class="tag">${fmtSize(p.size_bytes)}</span>` : "";
  return `<div class="pack" data-name="${esc(p.name)} ${esc(p.description)}">`+
    `<h2>${esc(p.title||p.name)} <span class="tag">${esc(p.language_code)}</span> ${size} ${soon}</h2>`+
    (p.description?`<p class="desc">${esc(p.description)}</p>`:"")+
    (samples?`<div class="samples">${samples}</div>`:"")+
    install +
  `</div>`;
}

const PLAY = "▶", PAUSE = "⏸";
const fmt = t => { t = Math.max(0, t|0); return (t/60|0)+":"+String(t%60).padStart(2,"0"); };

function initPlayers(){
  document.querySelectorAll(".sample").forEach(row => {
    const a = row.querySelector("audio"), fill = row.querySelector(".fill"),
          time = row.querySelector(".time"), btn = row.querySelector(".play");
    a.addEventListener("timeupdate", () => {
      const d = a.duration || 0;
      fill.style.width = d ? (a.currentTime / d * 100) + "%" : "0";
      time.textContent = fmt(a.currentTime);
    });
    a.addEventListener("ended", () => {
      btn.textContent = PLAY; btn.classList.remove("playing");
      fill.style.width = "0"; time.textContent = "0:00";
    });
  });
}

function render(filter){
  const f = (filter||"").toLowerCase();
  const packs = M.packs.filter(p => !f || (p.name+" "+p.description+" "+p.language_code).toLowerCase().includes(f));
  document.getElementById("list").innerHTML = packs.map(packHTML).join("") ||
    `<p class="count">No packs match.</p>`;
  document.getElementById("count").textContent =
    `${packs.length} of ${M.packs.length} pack${M.packs.length===1?"":"s"}`;
  initPlayers();
}
document.getElementById("q").addEventListener("input", e => render(e.target.value));

document.getElementById("list").addEventListener("click", async e => {
  const play = e.target.closest(".play");
  if(play){
    const a = play.closest(".sample").querySelector("audio");
    if(a.paused){
      document.querySelectorAll(".sample audio").forEach(o => { if(o!==a) o.pause(); });
      document.querySelectorAll(".play").forEach(b => { if(b!==play){ b.textContent=PLAY; b.classList.remove("playing"); }});
      a.play(); play.textContent = PAUSE; play.classList.add("playing");
    } else { a.pause(); play.textContent = PLAY; play.classList.remove("playing"); }
    return;
  }
  const bar = e.target.closest(".bar");
  if(bar){
    const a = bar.closest(".sample").querySelector("audio");
    const r = bar.getBoundingClientRect();
    if(a.duration) a.currentTime = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)) * a.duration;
    return;
  }
  const b = e.target.closest("button.copy"); if(!b) return;
  try{ await navigator.clipboard.writeText(b.dataset.copy);
       b.textContent="Copied"; b.classList.add("done");
       setTimeout(()=>{b.textContent="Copy";b.classList.remove("done")},1200);
  }catch{ b.textContent="Copy failed"; }
});
document.getElementById("foot").textContent =
  `Generated ${M.generated} · ${M.repo}`;
render("");
</script>
</body>
</html>
"""


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else git_slug()
    branch = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BRANCH
    DOCS.mkdir(exist_ok=True)
    manifest = build_manifest(repo, branch)
    (DOCS / "index.html").write_text(render(manifest))
    (DOCS / "manifest.json").write_text(json.dumps(manifest, indent=1))
    rel = sum(1 for p in manifest["packs"] if p["released"])
    print(f"wrote {DOCS}/index.html  ({len(manifest['packs'])} packs, {rel} released)")
    for p in manifest["packs"]:
        print(f"  {p['name']:<12} {'released' if p['released'] else 'unreleased':<11} "
              f"{len(p['samples'])} sample(s)")


if __name__ == "__main__":
    sys.exit(main())
