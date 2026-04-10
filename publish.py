import os
import json
import subprocess

print("=========================================")
print("🌟 SyllabusWithRohit - PREMIUM EDITION")
print("=========================================")

draft_file = "draft.txt"
if not os.path.exists(draft_file):
    print("❌ Error: 'draft.txt' nahi mili.")
    exit()

with open(draft_file, 'r', encoding='utf-8') as f: content = f.read().strip()
if not content:
    print("❌ Error: 'draft.txt' khali hai.")
    exit()

title = input("📚 Kitab ka Title: ")
author = input("✍️ Original Writer: ")
category = input("🏷️ Category (eg. Philosophy, History): ")

filename = title.lower().replace(" ", "_") + ".html"
filepath = f"books/{filename}"

# --- 1. KINDLE BOOK PAGE TEMPLATE ---
paragraphs = "".join([f"<p>{p.strip()}</p>" for p in content.split('\n\n') if p.strip()])

book_html = f"""<!DOCTYPE html>
<html lang="hi" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | SyllabusWithRohit</title>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {{ --bg: #fdfbf7; --text: #111111; --accent: #8b5a2b; }}
        body.sepia {{ --bg: #f4ecd8; --text: #433422; }}
        body.dark {{ --bg: #121212; --text: #d1d1d1; --accent: #b37339; }}
        body.red-mode {{ --bg: #000000; --text: #ff3333; --accent: #ff0000; }}
        
        body {{ background-color: var(--bg); color: var(--text); font-family: 'Lora', serif; transition: background-color 0.4s, color 0.4s; }}
        #pb {{ position:fixed; top:0; left:0; height:3px; background: var(--accent); width:0%; z-index:100; transition: width 0.2s; }}
        
        article p {{ margin-bottom: 2.5rem; font-size: 21px; line-height: 1.85; text-align: justify; hyphens: auto; letter-spacing: -0.01em; }}
        article p:first-of-type::first-letter {{ float:left; font-size:4.5rem; line-height:0.8; padding-right:12px; font-weight:bold; color: var(--accent); }}
        
        .nav-btn {{ padding: 4px 12px; border: 1px solid currentColor; border-radius: 4px; font-size: 12px; cursor: pointer; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; }}
        .nav-btn:hover {{ opacity: 1; }}
    </style>
</head>
<body>
    <div id="pb"></div>
    <nav style="border-bottom: 1px solid rgba(128,128,128,0.2); padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; background: inherit; z-index: 50;">
        <a href="../index.html" style="font-family: sans-serif; font-size: 12px; font-weight: bold; text-decoration: none; color: inherit; text-transform: uppercase; letter-spacing: 2px;">← Library</a>
        <div style="display: flex; gap: 10px; font-family: sans-serif;">
            <button onclick="setTheme('light')" class="nav-btn">Light</button>
            <button onclick="setTheme('sepia')" class="nav-btn">Sepia</button>
            <button onclick="setTheme('dark')" class="nav-btn">Dark</button>
            <button onclick="setTheme('red-mode')" class="nav-btn" style="border-color:#ff3333; color:#ff3333;">Red</button>
        </div>
    </nav>
    <main style="max-width: 680px; margin: 0 auto; padding: 60px 20px 100px;">
        <header style="text-align: center; margin-bottom: 60px;">
            <div style="font-family: sans-serif; font-size: 12px; letter-spacing: 3px; text-transform: uppercase; color: var(--accent); margin-bottom: 15px; font-weight: bold;">{category}</div>
            <h1 style="font-size: 2.8rem; font-weight: bold; font-style: italic; margin-bottom: 15px; line-height: 1.2;">{title}</h1>
            <p style="font-size: 1.2rem; opacity: 0.7; font-style: italic;">By {author}</p>
        </header>
        <article>{paragraphs}</article>
    </main>
    <script>
        window.onscroll = () => {{ document.getElementById("pb").style.width = ((document.documentElement.scrollTop)/(document.documentElement.scrollHeight-document.documentElement.clientHeight)*100)+"%"; }};
        function setTheme(t) {{
            document.body.className = t;
            localStorage.setItem('theme', t);
        }}
        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme);
    </script>
</body>
</html>"""

with open(filepath, 'w', encoding='utf-8') as f: f.write(book_html)

# --- 2. UPDATE LIBRARY DATA ---
library_file = "library.json"
library = []
if os.path.exists(library_file):
    with open(library_file, 'r', encoding='utf-8') as f: library = json.load(f)

library.append({"title": title, "author": author, "category": category, "link": f"books/{filename}"})
with open(library_file, 'w', encoding='utf-8') as f: json.dump(library, f, indent=4)

# --- 3. ZERO-IMAGE FAST HOMEPAGE TEMPLATE ---
cards = ""
for book in reversed(library):
    cards += f"""
    <a href="{book['link']}" class="book-card" style="display: flex; flex-direction: column; justify-content: space-between; background: #fff; padding: 30px; border-radius: 4px; text-decoration: none; color: #111; box-shadow: 0 4px 6px rgba(0,0,0,0.05); position: relative; border-left: 12px solid #8b5a2b; transition: transform 0.3s, box-shadow 0.3s; min-height: 250px;">
        <div>
            <span style="font-family: sans-serif; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; color: #8b5a2b; display: block; margin-bottom: 10px;">{book['category']}</span>
            <h3 style="font-family: 'Lora', serif; font-size: 24px; font-weight: bold; font-style: italic; margin: 0 0 10px 0; line-height: 1.3;">{book['title']}</h3>
            <p style="font-family: sans-serif; font-size: 14px; opacity: 0.7; margin: 0;">{book['author']}</p>
        </div>
        <div style="font-family: sans-serif; font-size: 12px; font-weight: bold; color: #8b5a2b; text-transform: uppercase; letter-spacing: 1px; margin-top: 30px;">Read →</div>
    </a>"""

index_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Library | SyllabusWithRohit</title>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #fdfbf7; color: #111; font-family: 'Lora', serif; margin: 0; padding: 0; }}
        nav {{ padding: 20px 40px; border-bottom: 1px solid rgba(0,0,0,0.05); background: #fdfbf7; }}
        .logo {{ font-family: sans-serif; font-size: 18px; font-weight: bold; letter-spacing: 3px; text-transform: uppercase; }}
        header {{ text-align: center; padding: 80px 20px; }}
        .search-container {{ max-width: 500px; margin: 40px auto 0; }}
        #searchBox {{ width: 100%; padding: 15px 20px; font-size: 16px; font-family: sans-serif; border: 1px solid #ccc; border-radius: 30px; outline: none; transition: border-color 0.3s; background: transparent; }}
        #searchBox:focus {{ border-color: #8b5a2b; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 30px; max-width: 1000px; margin: 0 auto; padding: 0 20px 100px; }}
        .book-card:hover {{ transform: translateY(-5px); box-shadow: 0 12px 20px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <nav>
        <div class="logo">Syllabus<span style="color: #8b5a2b;">With</span>Rohit</div>
    </nav>
    <header>
        <h1 style="font-size: 3.5rem; font-style: italic; margin: 0 0 15px 0;">Gyan Sabke <span style="color: #8b5a2b;">Liye.</span></h1>
        <p style="font-size: 1.2rem; opacity: 0.7; max-width: 600px; margin: auto;">Zero distractions. Premium reading experience.</p>
        <div class="search-container">
            <input type="text" id="searchBox" onkeyup="filterBooks()" placeholder="Kitaab ka naam dhoondhein...">
        </div>
    </header>
    <main class="grid" id="bookGrid">{cards}</main>
    <script>
        function filterBooks() {{
            let input = document.getElementById('searchBox').value.toLowerCase();
            let cards = document.getElementsByClassName('book-card');
            for (let i = 0; i < cards.length; i++) {{
                let title = cards[i].querySelector('h3').innerText.toLowerCase();
                if (title.indexOf(input) > -1) cards[i].style.display = 'flex';
                else cards[i].style.display = 'none';
            }}
        }}
    </script>
</body>
</html>"""

with open("index.html", 'w', encoding='utf-8') as f: f.write(index_html)

# --- 4. CLEAR & PUSH ---
with open(draft_file, 'w', encoding='utf-8') as f: f.write("")
print("⏳ GitHub par Push ho raha hai...")
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", f"Premium UI Update with: {title}"], check=True)
subprocess.run(["git", "push"], check=True)
print("🌟 BAM! Nayi kitab aur Naya Design GitHub par live ho raha hai (Wait 1 minute).")
