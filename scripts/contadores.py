"""Gera assets/contadores.svg com estrelas, contribuições e repositórios.
"""

import json
import os
import urllib.request
from pathlib import Path

USER = os.environ.get("GH_USER", "nullfeel")
ROOT = Path(__file__).resolve().parent.parent
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


def render(stats):
    w, h = 600, 110
    cols = []
    for i, (label, value) in enumerate(stats):
        x = w / len(stats) * (i + 0.5)
        cols.append(
            f'  <text x="{x}" y="58" class="n">{str(value).zfill(3)}</text>\n'
            f'  <text x="{x}" y="88" class="l">{label}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <style>
    text {{ font-family: Consolas, 'Courier New', monospace; text-anchor: middle; }}
    .n {{ font-size: 40px; fill: #d6d8e0; letter-spacing: 4px; }}
    .l {{ font-size: 13px; fill: #b3122e; letter-spacing: 3px; text-transform: uppercase; }}
  </style>
{chr(10).join(cols)}
</svg>
"""


if __name__ == "__main__":
    OUT.write_text(render(fetch_stats()), encoding="utf-8")
    print(f"gerado {OUT}")
