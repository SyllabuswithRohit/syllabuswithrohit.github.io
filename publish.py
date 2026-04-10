import os
import json
import subprocess

print("=========================================")
print("🌟 SyllabuswithRohit - V22 POLISHED PRO")
print("=========================================")

# --- CONFIG ---
UPI_ID = "syllabuswithrohit@upi"
COFFEE_LINK = "https://buymeacoffee.com/SyllabuswithRohit"
YT_LINK = "https://www.youtube.com/@SyllabuswithRohit"
QR_IMAGE = "../qr.png" 

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
category = input("🏷️ Category: ")

filename = title.lower().replace(" ", "_") + ".html"
filepath = f"books/{filename}"

# --- CSS SHARED CLASSES (Sepia visibility FIXED) ---
shared_styles = """
    :root { --bg: #fdfbf7; --text: #1a1a1a; --accent: #000; }
    body.sepia { --bg: #f4ecd8; --text: #2c1e0f; --accent: #6f421a; } /* Fixed: Darker text for visibility */
    body.dark { --bg: #121212; --text: #d1d1d1; --accent: #555555; }
    body.red-mode { --bg: #000000; --text: #ff0000; --accent: #ff0000; }
    
    body { background-color: var(--bg); color: var(--text); font-family: 'Lora', serif; transition: 0.4s; overflow-x: hidden; }
    .nav-btn { font-size: 10px; font-weight: bold; letter-spacing: 1px; opacity: 0.6; transition: 0.3s; padding: 4px 8px; border: 1px solid transparent; }
    .nav-btn:hover { opacity: 1; border-color: currentColor; }
    .profile-img { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; border: 2px solid #fff; box-shadow: 0 0 0 0 rgba(0,0,0,0.2); transition: 0.4s; }
    .profile-img:hover { transform: scale(1.1); box-shadow: 0 0 15px 5px rgba(0,0,0,0.1); }
    #supportModal { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.92); z-index:1000; align-items:center; justify-content:center; padding:20px; backdrop-blur: 8px; }
"""

# --- 1. BOOK PAGE ---
paras = "".join([f"<p>{p.strip()}</p>" for p in content.split('\n\n') if p.strip()])

book_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | SyllabuswithRohit</title>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>{shared_styles} article p {{ margin-bottom: 2.8rem; font-size: 21px; line-height: 1.85; text-align: justify; }}</style>
</head>
<body>
    <div id="pb"></div>
    <nav class="flex justify-between items-center px-6 py-3 sticky top-0 bg-inherit border-b border-black/5 z-50">
        <a href="../index.html" class="font-sans text-[11px] font-bold tracking-[2px]">SyllabuswithRohit</a>
        <div class="flex items-center gap-6">
            <div class="hidden md:flex gap-2">
                <button onclick="setTheme('light')" class="nav-btn">Light</button>
                <button onclick="setTheme('sepia')" class="nav-btn">Sepia</button>
                <button onclick="setTheme('red-mode')" class="nav-btn text-red-600">Red</button>
            </div>
            <a href="{YT_LINK}" target="_blank"><img src="../myprofile.jpg" class="profile-img"></a>
        </div>
    </nav>
    <main class="max-w-[680px] mx-auto px-6 py-20">
        <header class="text-center mb-16">
            <div class="text-[10px] tracking-[4px] uppercase font-bold opacity-50 mb-4">{category}</div>
            <h1 class="text-4xl font-bold italic mb-4">{title}</h1>
            <p class="opacity-60 italic">By {author}</p>
        </header>
        <article>{paras}</article>
    </main>
    <div id="supportModal">
        <div class="bg-inherit border border-white/10 p-10 rounded-2xl max-w-sm w-full text-center relative">
            <button onclick="closeModal()" class="absolute top-4 right-4 text-2xl opacity-40">&times;</button>
            <h2 class="text-2xl font-bold mb-6 italic">Support My Work</h2>
            <img src="{QR_IMAGE}" class="w-40 h-40 mx-auto mb-6 rounded-lg bg-white p-2">
            <p class="text-sm opacity-70 mb-6">Aapka support mujhe aur books laane me madad karega.</p>
            <div class="text-[10px] opacity-40 uppercase tracking-widest mb-2 font-mono">{UPI_ID}</div>
            <a href="{COFFEE_LINK}" target="_blank" class="block bg-yellow-500 text-black py-3 rounded-full text-[10px] font-bold tracking-[2px] uppercase mb-3 hover:bg-yellow-400 transition-colors">Buy me a Coffee</a>
            <a href="upi://pay?pa={UPI_ID}&pn=SyllabuswithRohit" class="block bg-black text-white py-3 rounded-full text-[10px] font-bold tracking-[2px] uppercase hover:bg-zinc-800 transition-colors">Pay via UPI App</a>
        </div>
    </div>
    <script>
        function setTheme(t) {{ document.body.className = t; localStorage.setItem('theme', t); }}
        setTheme(localStorage.getItem('theme') || 'light');
        function closeModal() {{ document.getElementById('supportModal').style.display = 'none'; }}
        setTimeout(() => {{ document.getElementById('supportModal').style.display = 'flex'; }}, 900000); // 15 Minute pop-up
    </script>
</body>
</html>"""

with open(filepath, 'w', encoding='utf-8') as f: f.write(book_html)

# --- 2. UPDATE LIBRARY ---
library_file = "library.json"
library = []
if os.path.exists(library_file):
    with open(library_file, 'r', encoding='utf-8') as f: library = json.load(f)
library.append({"title": title, "author": author, "category": category, "link": f"books/{filename}"})
with open(library_file, "w", encoding='utf-8') as f: json.dump(library, f, indent=4)

# --- 3. HOMEPAGE ---
cards = ""
for book in reversed(library):
    cards += f"""
    <a href="{book['link']}" class="group bg-white p-10 border-l-[12px] border-black hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 flex flex-col justify-between min-h-[280px]">
        <div>
            <span class="text-[9px] font-bold tracking-[3px] opacity-40 mb-4 block uppercase text-black">{book['category']}</span>
            <h3 class="text-2xl font-bold italic leading-tight mb-2 text-black">{book['title']}</h3>
            <p class="text-sm opacity-60 italic text-black">{book['author']}</p>
        </div>
        <div class="text-[10px] font-bold tracking-[2px] uppercase text-black">Read Book →</div>
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
        <div class="flex items-center gap-6">
            <div class="flex gap-2">
                <button onclick="setTheme('light')" class="nav-btn">Light</button>
                <button onclick="setTheme('sepia')" class="nav-btn">Sepia</button>
                <button onclick="setTheme('red-mode')" class="nav-btn text-red-600">Red</button>
            </div>
            <a href="{YT_LINK}" target="_blank" title="YouTube Community">
                <img src="myprofile.jpg" class="profile-img">
            </a>
        </div>
    </nav>
    <main class="max-w-6xl mx-auto px-6 py-20">
        <h1 class="text-center text-4xl md:text-6xl font-bold italic mb-20 tracking-tight">SyllabuswithRohit</h1>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">{cards}</div>
    </main>
    <script>
        function setTheme(t) {{ document.body.className = t; localStorage.setItem('theme', t); }}
        setTheme(localStorage.getItem('theme') || 'light');
    </script>
</body>
</html>"""

with open("index.html", 'w', encoding='utf-8') as f: f.write(index_html)

# --- 4. PUSH ---
with open(draft_file, "w", encoding='utf-8') as f: f.write("")
print("⏳ GitHub par Push ho raha hai... Polished Pro Launch!")
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", f"V22 Polished: Sepia fixed, Modal text & BMAC link"], check=True)
subprocess.run(["git", "push"], check=True)
print("🌟 SUCCESS! Website polished ho gayi hai. 1 minute baad check karein.")
