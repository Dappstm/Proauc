# titlegen.py
import random

def generate_title(labels):
    # labels is list of short phrases. Combine and create funny title heuristically.
    choices = [
        "Top {n} Pranks Gone Wrong",
        "People Regret These {n} Moments",
        "Cringe Compilation: {n} Clips That Backfired",
        "When Pranks Fail — {n} Times",
        "You Won't Believe #1 — {n} Clips"
    ]
    template = random.choice(choices)
    n = len(labels)
    base = template.format(n=n)
    # attach tag summarizing labels: take short keywords from each
    summary = " | ".join((l if len(l)<=20 else l[:17]+"...") for l in labels)
    return f"{base} — {summary}"
