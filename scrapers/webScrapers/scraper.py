import requests
from bs4 import BeautifulSoup

page = requests.get(
    "https://github.com/trending?since=daily",
    headers={"User-Agent": "InsightSenderBot/1.0"},
)
soup = BeautifulSoup(page.text, "html.parser")

repos = soup.select("article.Box-row")
print(len(repos))

for repo in repos:
    h2 = repo.select_one("h2 a")
    if not h2:
        continue
    path = h2.get("href", "").strip()
    parts = path.strip("/").split("/")
    if len(parts) < 2:
        continue
    developer = parts[0]
    repo_name = parts[1]
    print("Developer name:", developer)
    print("Repo name:", repo_name)

    stars_el = repo.select_one("span.d-inline-block.float-sm-right")
    if stars_el:
        num_stars = "".join(filter(str.isdigit, stars_el.get_text(strip=True)))
        print("Stars:", num_stars or "0")
    else:
        print("Stars: 0")
