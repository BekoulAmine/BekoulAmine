"""Fills the Daily Commission section of README.md: character of the day + a daily wish roll."""
import datetime, random, re, sys

CHARS = [
    ("Venti", "🌀 Anemo", "Mondstadt"), ("Kazuha", "🌀 Anemo", "Inazuma"), ("Xiao", "🌀 Anemo", "Liyue"),
    ("Zhongli", "🪨 Geo", "Liyue"), ("Navia", "🪨 Geo", "Fontaine"), ("Itto", "🪨 Geo", "Inazuma"),
    ("Raiden Shogun", "⚡ Electro", "Inazuma"), ("Fischl", "⚡ Electro", "Mondstadt"), ("Clorinde", "⚡ Electro", "Fontaine"),
    ("Nahida", "🌿 Dendro", "Sumeru"), ("Alhaitham", "🌿 Dendro", "Sumeru"), ("Tighnari", "🌿 Dendro", "Sumeru"),
    ("Furina", "💧 Hydro", "Fontaine"), ("Neuvillette", "💧 Hydro", "Fontaine"), ("Xingqiu", "💧 Hydro", "Liyue"),
    ("Hu Tao", "🔥 Pyro", "Liyue"), ("Diluc", "🔥 Pyro", "Mondstadt"), ("Mavuika", "🔥 Pyro", "Natlan"),
    ("Ganyu", "❄️ Cryo", "Liyue"), ("Ayaka", "❄️ Cryo", "Inazuma"), ("Wriothesley", "❄️ Cryo", "Fontaine"),
]
QUESTS = [
    "Refactor one legacy function — it has been waiting longer than my 50/50.",
    "Write a test before the bug finds you, like checking the map before a domain.",
    "Ship a small PR. Small commits, like daily commissions, add up to Primogems.",
    "Read the docs. Every chest in Teyvat is found by actually looking around.",
    "Clean up your Docker images. Your storage is fuller than a 2000/2000 Mora bag.",
    "Review a teammate's PR. Co-op mode gives bonus EXP.",
    "Automate one boring task. Let the CI farm the resin for you.",
]
TRASH = ["Cool Steel", "Harbinger of Dawn", "Slingshot", "Debate Club", "Thrilling Tales of Dragon Slayers"]
FOURS = ["Xiangling", "Bennett", "Xingqiu", "Sucrose", "Fischl", "Faruzan", "Chevreuse"]


def section(today: datetime.date) -> str:
    rng = random.Random(today.toordinal())  # same result for reruns on the same day
    name, element, region = CHARS[today.toordinal() % len(CHARS)]
    roll = rng.random()
    if roll < 0.006:
        wish = f"✨✨✨✨✨ **GOLDEN!** {rng.choice(CHARS)[0]} joined the party!"
    elif roll < 0.057:
        wish = f"💜💜💜💜 Purple glow — **{rng.choice(FOURS)}** answered the call."
    else:
        wish = f"💙💙💙 Blue star... another **{rng.choice(TRASH)}**. Pity +1."
    return (
        f"| 🌟 Character of the day | 🧭 Today's quest | 🎲 Daily wish |\n"
        f"|:-:|:--|:--|\n"
        f"| **{name}**<br>{element} · {region} | {rng.choice(QUESTS)} | {wish} |\n\n"
        f"<sub>🕒 Refreshed by GitHub Actions on {today.isoformat()} (Teyvat server reset)</sub>"
    )


def update(text: str, today: datetime.date) -> str:
    pattern = r"(<!--START_SECTION:teyvat-->).*?(<!--END_SECTION:teyvat-->)"
    assert re.search(pattern, text, re.S), "teyvat markers missing from README"
    return re.sub(pattern, lambda m: f"{m[1]}\n{section(today)}\n{m[2]}", text, flags=re.S)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new = update(text, datetime.date.today())
    assert update(new, datetime.date.today()) == new  # idempotent: rerun changes nothing
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
