"""Gera assets/contadores.svg com estrelas, contribuições e repositórios.

Os números são desenhados com os GIFs do tema cat-girls-yay do Moe-Counter
(github.com/journey-ad/Moe-Counter, licença MIT).
"""

import base64
import json
import os
import struct
import urllib.request
from pathlib import Path

USER = os.environ.get("GH_USER", "nullfeel")
ROOT = Path(__file__).resolve().parent.parent
DIGITS = ROOT / "assets" / "moe"
OUT = ROOT / "assets" / "contadores.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection { contributionCalendar { totalContributions } }
  }
}
"""


def fetch_stats():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(req) as resp:
        user = json.load(resp)["data"]["user"]
    repos = user["repositories"]
    return [
        ("estrelas", sum(r["stargazerCount"] for r in repos["nodes"])),
        ("contribuições no ano", user["contributionsCollection"]["contributionCalendar"]["totalContributions"]),
        ("repositórios", repos["totalCount"]),
    ]


def load_digits():
    digits = {}
    for d in "0123456789":
        raw = (DIGITS / f"{d}.gif").read_bytes()
        width, height = struct.unpack("<HH", raw[6:10])
        digits[d] = (width, height, base64.b64encode(raw).decode())
    return digits


def render(stats, digits):
    gap, label_h, pad = 40, 26, 10
    blocks, x = [], pad
    for label, value in stats:
        text = str(value).zfill(3)
        width = sum(digits[c][0] for c in text)
        blocks.append((label, text, x, width))
        x += width + gap
    total_w = x - gap + pad
    total_h = label_h + 100 + pad

    used = sorted({c for _, text, _, _ in blocks for c in text})
    defs = "\n".join(
        f'    <image id="d{c}" width="{digits[c][0]}" height="{digits[c][1]}" '
        f'href="data:image/gif;base64,{digits[c][2]}" />'
        for c in used
    )

    parts = []
    n = 0
    for label, text, bx, width in blocks:
        parts.append(
            f'  <text x="{bx + width / 2}" y="18" text-anchor="middle">{label}</text>'
        )
        cx = bx
        for c in text:
            parts.append(
                f'  <use href="#d{c}" x="{cx}" y="{label_h}" class="g" '
                f'style="animation-delay:{n * 0.12:.2f}s" />'
            )
            cx += digits[c][0]
            n += 1

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">
  <style>
    svg {{ image-rendering: pixelated; }}
    text {{ font: 600 14px 'Segoe UI', Ubuntu, sans-serif; fill: #6C5CE7; }}
    .g {{ animation: pula 1.6s ease-in-out infinite; transform-box: fill-box; }}
    @keyframes pula {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-5px); }} }}
  </style>
  <defs>
{defs}
  </defs>
{chr(10).join(parts)}
</svg>
"""


if __name__ == "__main__":
    OUT.write_text(render(fetch_stats(), load_digits()), encoding="utf-8")
    print(f"gerado {OUT}")
