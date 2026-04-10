import os
import json
import subprocess
import math

print("=========================================")
print("🚀 SyllabuswithRohit - V24 MOBILE-OPTIMIZED")
print("=========================================")

# --- CONFIG ---
UPI_ID = "syllabuswithrohit@upi"
COFFEE_LINK = "https://buymeacoffee.com/SyllabuswithRohit"
YT_LINK = "https://www.youtube.com/@SyllabuswithRohit"

draft_file = "draft.txt"
with open(draft_file, 'r', encoding='utf-8') as f: content = f.read().strip()

# --- CALCULATE READING TIME ---
word_count = len(content.split())
reading_time = math.ceil(word_count / 200) # Average reading speed 200 wpm

title = input("📚 Kitab ka Title: ")
author = input("✍️ Original Writer: ")
category = input("🏷️ Category: ")

filename = title.lower().replace(" ", "_") + ".html"
filepath = f"books/{filename}"

shared_styles = """
    :root { --bg: #fdfbf7; --text: #1a1a1a; --accent: #000; }
    body.sepia { --bg: #f4ecd8; --text: #2c1e0f; --accent: #6f421a; }
    body.dark { --bg: #121212; --text: #d1d1d1; --accent: #555555; }
    body.red-mode { --bg: #000000; --text: #ff0000; --accent: #ff0000; }
    body { background-color: var(--bg); color: var(--text); font-family: 'Lora', serif; transition: 0.4s; }
    
    /* Mobile First Adjustments */
    .nav-btn { font-size: 12px; font-weight: bold; padding: 10px 15px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.1); }
    .profile-img { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; transition: 0.3s; }
    article p { margin-bottom: 2.5rem; font-size: 20px; line-height: 1.8; text-align: justify; }
    @media (max-width: 640px) { 
        article p { font-size: 18px; line-height: 1.7; } 
        .nav-text { display: none; } /* Hide name on mobile nav to save space */
    }
"""

book_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | SyllabuswithRohit</title>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>{shared_styles}</style>
</head>
<body>
    <div id="pb" style="position:fixed; top:0; left:0; height:3px; background:var(--accent); width:0%; z-index:100;"></div>
    <nav class="flex justify-between items-center px-4 py-2 sticky top-0 bg-inherit border-b border-black/5 z-50">
        <a href="../index.html" class="font-sans text-[10px] font-bold tracking-[2px]">← BACK</a>
        <div class="flex items-center gap-3">
            <button onclick="setTheme('light')" class="nav-btn">L</button>
            <button onclick="setTheme('sepia')" class="nav-btn">S</button>
            <button onclick="setTheme('red-mode')" class="nav-btn text-red-600">R</button>
            <a href="{YT_LINK}" target="_blank"><img src="../myprofile.jpg" class="profile-img"></a>
        </div>
    </nav>
    <main class="max-w-[680px] mx-auto px-6 py-12">
        <header class="text-center mb-12">
            <div class="text-[10px] tracking-[4px] uppercase font-bold opacity-50 mb-2">{category} • {reading_time} MIN READ</div>
            <h1 class="text-3xl md:text-5xl font-bold italic mb-4">{title}</h1>
            <p class="opacity-60 italic">By {author}</p>
        </header>
        <article>{"".join([f"<p>{p}</p>" for p in content.split('\n\n')])}</article>
    </main>
    <script>
        function setTheme(t) {{ document.body.className = t; localStorage.setItem('theme', t); }}
        setTheme(localStorage.getItem('theme') || 'light');
        window.onscroll = () => {{ document.getElementById("pb").style.width = ((document.documentElement.scrollTop)/(document.documentElement.scrollHeight-document.documentElement.clientHeight)*100)+"%"; }};
    </script>
</body>
</html>"""

with open(filepath, 'w', encoding='utf-8') as f: f.write(book_html)

# --- HOMEPAGE UPDATE ---
library_file = "library.json"
library = []
if os.path.exists(library_file):
    with open(library_file, 'r', encoding='utf-8') as f: library = json.load(f)
library.append({"title": title, "author": author, "category": category, "link": f"books/{filename}", "time": reading_time})
with open(library_file, "w", encoding='utf-8') as f: json.dump(library, f, indent=4)

cards = ""
for book in reversed(library):
    cards += f"""
    <a href="{book['link']}" class="bg-white p-8 border-l-[12px] border-black hover:shadow-xl transition-all flex flex-col justify-between min-h-[250px]">
        <div>
            <span class="text-[9px] font-bold tracking-[2px] opacity-40 mb-3 block uppercase">{book['category']} • {book.get('time', 5)} MIN</span>
            <h3 class="text-xl font-bold italic leading-tight mb-2">{book['title']}</h3>
            <p class="text-sm opacity-60 italic">{book['author']}</p>
        </div>
        <div class="text-[10px] font-bold tracking-[2px] uppercase mt-6">Read →</div>
    </a>"""

index_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SyllabuswithRohit</title>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>{shared_styles}</style>
</head>
<body>
    <nav class="flex justify-between items-center px-6 py-4 sticky top-0 bg-inherit border-b border-black/5 z-50">
        <div class="text-xs font-bold tracking-[3px]">SyllabuswithRohit</div>
        <a href="{YT_LINK}" target="_blank"><img src="myprofile.jpg" class="profile-img"></a>
    </nav>
    <main class="max-w-6xl mx-auto px-6 py-12">
        <h1 class="text-center text-4xl md:text-6xl font-bold italic mb-16">SyllabuswithRohit</h1>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">{cards}</div>
    </main>
    <script>
        function setTheme(t) {{ document.body.className = t; localStorage.setItem('theme', t); }}
        setTheme(localStorage.getItem('theme') || 'light');
    </script>
</body>
</html>"""

with open("index.html", 'w', encoding='utf-8') as f: f.write(index_html)

subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "V24: Mobile optimization & Reading time"], check=True)
subprocess.run(["git", "push"], check=True)
print("🌟 MOBILE-READY! Site check karein.")
