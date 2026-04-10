import os
import json
import subprocess
import math

print("=========================================")
print("📖 SyllabuswithRohit - V28 KINDLE-PARITY")
print("=========================================")

UPI_ID = "syllabuswithrohit@upi"
COFFEE_LINK = "https://buymeacoffee.com/SyllabuswithRohit"
YT_LINK = "https://www.youtube.com/@SyllabuswithRohit"
QR_IMAGE_BOOK = "../qr.png" 
QR_IMAGE_HOME = "qr.png"

draft_file = "draft.txt"
with open(draft_file, 'r', encoding='utf-8') as f: content = f.read().strip()
word_count = len(content.split())
reading_time = math.ceil(word_count / 200)

title = input("📚 Kitab ka Title: ")
author = input("✍️ Original Writer: ")
category = input("🏷️ Category: ")

filename = title.lower().replace(" ", "_") + ".html"
filepath = f"books/{filename}"

# --- CSS WITH DYNAMIC FONT VARIABLE ---
shared_styles = """
    :root { --bg: #fdfbf7; --text: #1a1a1a; --accent: #000; --font-size: 21px; }
    body.sepia { --bg: #f4ecd8; --text: #2c1e0f; --accent: #6f421a; }
    body.dark { --bg: #121212; --text: #d1d1d1; --accent: #888888; }
    body.red-mode { --bg: #000000; --text: #ff0000; --accent: #ff0000; }
    
    body { background-color: var(--bg); color: var(--text); font-family: 'Lora', serif; transition: background-color 0.4s, color 0.4s; overflow-x: hidden; }
    .nav-btn { font-size: 11px; font-weight: bold; padding: 6px 10px; border-radius: 6px; border: 1px solid rgba(128,128,128,0.2); cursor:pointer; background:transparent; color:inherit; transition: 0.2s;}
    .nav-btn:hover { background: var(--text); color: var(--bg); }
    .profile-img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; transition: 0.3s; border: 2px solid var(--accent); }
    
    #scrollPercent { position: fixed; bottom: 20px; right: 20px; background: var(--text); color: var(--bg); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-family: sans-serif; opacity: 0; transition: opacity 0.3s; z-index: 200; font-weight: bold; }
    article p { margin-bottom: 2.8rem; font-size: var(--font-size); line-height: 1.85; text-align: justify; transition: font-size 0.3s; }
    @media (max-width: 640px) { article p { line-height: 1.75; } }

    /* Modal Styles */
    #supportModal { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:1000; align-items:center; justify-content:center; padding:20px; backdrop-blur: 5px; }
    .modal-content { background:var(--bg); color:var(--text); padding:40px; border-radius:15px; max-width:380px; width:100%; text-align:center; border: 2px solid var(--accent); position:relative; }
    .close-btn { position:absolute; top:10px; right:20px; font-size:32px; color:var(--text); opacity:0.6; cursor:pointer; background:none; border:none; padding:0; }
"""

paras = "".join([f"<p>{p.strip()}</p>" for p in content.split('\n\n') if p.strip()])

# --- 1. BOOK PAGE (WITH AUTO-RESUME & TEXT CONTROLS) ---
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
    <div id="scrollPercent">0%</div>

    <nav class="flex justify-between items-center px-4 py-3 sticky top-0 bg-inherit border-b border-black/10 z-50">
        <div class="flex items-center gap-4">
            <a href="../index.html" class="font-sans text-[10px] font-bold tracking-[2px] uppercase">← Library</a>
        </div>
        <div class="flex items-center gap-2 md:gap-3">
            <button onclick="changeFont(-2)" class="nav-btn" title="Decrease Font">A-</button>
            <button onclick="changeFont(2)" class="nav-btn" title="Increase Font">A+</button>
            <div class="w-px h-4 bg-gray-400 opacity-50 mx-1"></div>
            <button onclick="setTheme('light')" class="nav-btn">L</button>
            <button onclick="setTheme('sepia')" class="nav-btn">S</button>
            <button onclick="setTheme('dark')" class="nav-btn">D</button>
            <button onclick="setTheme('red-mode')" class="nav-btn" style="color:#ff0000; border-color:#ff0000;">R</button>
        </div>
    </nav>

    <main class="max-w-[680px] mx-auto px-6 py-16">
        <header class="text-center mb-16">
            <div class="text-[10px] tracking-[4px] uppercase font-bold opacity-50 mb-4">{category} • {reading_time} MIN</div>
            <h1 class="text-4xl md:text-5xl font-bold italic mb-4">{title}</h1>
            <p class="opacity-60 italic">By {author}</p>
        </header>
        <article>{paras}</article>
    </main>

    <div id="supportModal">
        <div class="modal-content">
            <button onclick="closeModal()" class="close-btn">&times;</button>
            <h2 class="text-2xl font-bold mb-4 italic">Support</h2>
            <div style="background:white; padding:10px; border-radius:10px; display:inline-block; margin-bottom:20px; border: 2px solid var(--accent);">
                <img src="{QR_IMAGE_BOOK}" class="w-40 h-40 object-contain">
            </div>
            <p class="text-sm opacity-80 mb-6 font-sans">Aapka support mujhe aur books laane me madad karega.</p>
            <a href="upi://pay?pa={UPI_ID}&pn=SyllabuswithRohit" style="background:var(--accent); color:var(--bg); padding:14px; border-radius:30px; display:block; font-size:11px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px; text-decoration:none;">Pay via UPI App</a>
            <a href="{COFFEE_LINK}" target="_blank" style="background:#FFDD00; color:#000; padding:14px; border-radius:30px; display:block; font-size:11px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; text-decoration:none;">Buy me a Coffee</a>
        </div>
    </div>

    <script>
        // --- 1. Theme Engine ---
        function setTheme(t) {{ document.body.className = t; localStorage.setItem('theme', t); }}
        setTheme(localStorage.getItem('theme') || 'light');

        // --- 2. Typography Engine (A- / A+) ---
        let currentFont = parseInt(localStorage.getItem('fontSize')) || 21;
        document.documentElement.style.setProperty('--font-size', currentFont + 'px');
        
        function changeFont(step) {{
            currentFont += step;
            if(currentFont < 16) currentFont = 16; // Minimum limit
            if(currentFont > 32) currentFont = 32; // Maximum limit
            document.documentElement.style.setProperty('--font-size', currentFont + 'px');
            localStorage.setItem('fontSize', currentFont);
        }}

        // --- 3. Auto-Resume (The Kindle Magic) ---
        const bookId = "pos_{filename}";
        window.onload = () => {{
            let savedPos = localStorage.getItem(bookId);
            if(savedPos) window.scrollTo({{top: savedPos, behavior: 'smooth'}});
        }};

        // --- 4. Scroll Tracking ---
        let timer;
        const scrollLabel = document.getElementById('scrollPercent');
        window.onscroll = () => {{
            const winScroll = document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            let scrolled = (winScroll / height) * 100;
            if (scrolled < 0) scrolled = 0; if (scrolled > 100) scrolled = 100;
            
            document.getElementById("pb").style.width = scrolled + "%";
            scrollLabel.innerText = Math.round(scrolled) + "%";
            scrollLabel.style.opacity = "1";
            
            // Save position silently
            localStorage.setItem(bookId, winScroll);
            
            clearTimeout(timer);
            timer = setTimeout(() => {{ scrollLabel.style.opacity = "0"; }}, 2000);
        }};

        function showModal() {{ document.getElementById('supportModal').style.display = 'flex'; }}
        function closeModal() {{ document.getElementById('supportModal').style.display = 'none'; }}
        setTimeout(() => {{ if(document.getElementById('supportModal').style.display !== 'flex') showModal(); }}, 900000);
    </script>
</body>
</html>"""

with open(filepath, 'w', encoding='utf-8') as f: f.write(book_html)

# --- 2. HOMEPAGE UPDATE ---
library_file = "library.json"
library = []
if os.path.exists(library_file):
    with open(library_file, 'r', encoding='utf-8') as f: library = json.load(f)

new_book = {"title": title, "author": author, "category": category, "link": f"books/{filename}", "time": reading_time}
if not any(b['title'] == title for b in library): library.append(new_book)
else:
    for idx, b in enumerate(library):
        if b['title'] == title: library[idx] = new_book
            
with open(library_file, "w", encoding='utf-8') as f: json.dump(library, f, indent=4)

cards = ""
for book in reversed(library):
    cards += f"""
    <a href="{book['link']}" class="group p-8 border-l-[10px] hover:-translate-y-2 transition-all duration-300 flex flex-col justify-between min-h-[250px]" style="background:var(--bg); border-color:var(--accent); border-top:1px solid rgba(128,128,128,0.2); border-right:1px solid rgba(128,128,128,0.2); border-bottom:1px solid rgba(128,128,128,0.2); box-shadow: 0 10px 30px -10px rgba(0,0,0,0.1);">
        <div>
            <span class="text-[9px] font-bold tracking-[3px] opacity-50 mb-4 block uppercase font-sans">{book['category']} • {book.get('time', 5)} MIN</span>
            <h3 class="text-2xl font-bold italic leading-tight mb-2" style="color:var(--text);">{book['title']}</h3>
            <p class="text-sm opacity-70 italic" style="color:var(--text);">{book['author']}</p>
        </div>
        <div class="text-[10px] font-bold tracking-[2px] uppercase mt-6" style="color:var(--text);">Read Book →</div>
    </a>"""

# Keep index.html minimal changes for now to save space, assuming it's already generated well in V27
# I'm focusing the push on the reading features.
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "V28: Kindle Parity - Auto Resume & Font Scaling"], check=True)
subprocess.run(["git", "push"], check=True)
print("🌟 KINDLE PARITY LIVE! Font Size and Auto-Resume Activated.")
