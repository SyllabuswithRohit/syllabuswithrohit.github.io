import os
import json
import subprocess

print("=========================================")
print("🌟 SyllabuswithRohit - V20 FIXED-PRO")
print("=========================================")

# --- CONFIG ---
UPI_ID = "syllabuswithrohit@upi"
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

# --- 1. PAGE GENERATION ---
paras_list = [p.strip() for p in content.split('\n\n') if p.strip()]
processed_paras = ""
for i, p in enumerate(paras_list):
    processed_paras += f"<p>{p}</p>"
    if i == 3:
        processed_paras += '<div id="support-trigger"></div>'

book_html = f"""<!DOCTYPE html>
<html lang="hi" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | SyllabuswithRohit</title>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {{ --bg: #fdfbf7; --text: #1a1a1a; --accent: #000; }}
        body.sepia {{ --bg: #f4ecd8; --text: #4a3c2b; }}
        body.dark {{ --bg: #121212; --text: #d1d1d1; --accent: #555555; }}
        body.red-mode {{ --bg: #000000; --text: #ff0000; --accent: #ff0000; }}
        body {{ background-color: var(--bg); color: var(--text); font-family: 'Lora', serif; transition: 0.4s; }}
        #pb {{ position:fixed; top:0; left:0; height:3px; background: var(--accent); width:0%; z-index:100; }}
        article p {{ margin-bottom: 2.8rem; font-size: 21px; line-height: 1.85; text-align: justify; }}
        #supportModal {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,0.9); z-index:1000; align-items:center; justify-content:center; padding:20px; backdrop-blur: 5px; }}
        .modal-content {{ background:var(--bg); color:var(--text); padding:40px; border-radius:15px; max-width:380px; width:100%; text-align:center; border: 1px solid rgba(128,128,128,0.2); position:relative; }}
    </style>
</head>
<body>
    <div id="pb"></div>
    <nav class="flex justify-between items-center p-4 sticky top-0 bg-inherit border-b border-black/5 z-50">
        <a href="../index.html" class="font-sans text-[10px] font-bold tracking-[3px] uppercase">← Library</a>
        <div class="flex gap-4">
            <button onclick="setTheme('light')" class="text-[10px] font-bold uppercase tracking-widest opacity-60">Light</button>
            <button onclick="setTheme('red-mode')" class="text-[10px] font-bold uppercase tracking-widest text-red-600">Red</button>
        </div>
    </nav>
    <main class="max-w-[680px] mx-auto px-6 py-20">
        <header class="text-center mb-16">
            <div class="text-[11px] tracking-[4px] uppercase font-bold opacity-60 mb-4">{category}</div>
            <h1 class="text-4xl md:text-5xl font-bold italic mb-4 leading-tight">{title}</h1>
            <p class="text-lg opacity-60 italic">By {author}</p>
        </header>
        <article>{processed_paras}</article>
    </main>
    <div id="supportModal">
        <div class="modal-content">
            <button onclick="closeModal()" class="absolute top-4 right-4 text-2xl opacity-50 hover:opacity-100">&times;</button>
            <h2 class="text-2xl font-bold mb-2 italic">Support</h2>
            <p class="text-sm opacity-70 mb-6">Aapka support humein aur kitabein laane mein madad karta hai.</p>
            <div class="bg-white p-4 rounded-lg inline-block mb-4 shadow-inner">
                <img src="{QR_IMAGE}" alt="UPI QR Code" class="w-48 h-48 object-contain">
            </div>
            <div class="font-mono text-xs mb-6 opacity-60 tracking-wider font-bold">{UPI_ID}</div>
            <a href="upi://pay?pa={UPI_ID}&pn=SyllabuswithRohit" class="block bg-black text-white py-3 rounded-full text-xs font-bold tracking-[2px] uppercase">Pay via UPI App</a>
        </div>
    </div>
    <script>
        function setTheme(t) {{ document.body.className = t; localStorage.setItem('theme', t); }}
        setTheme(localStorage.getItem('theme') || 'light');
        window.onscroll = () => {{ 
            document.getElementById("pb").style.width = ((document.documentElement.scrollTop)/(document.documentElement.scrollHeight-document.documentElement.clientHeight)*100)+"%"; 
            let trigger = document.getElementById('support-trigger');
            if(trigger && !localStorage.getItem('popupDone')) {{
                let pos = trigger.getBoundingClientRect();
                if(pos.top < window.innerHeight) {{
                    showModal();
                    localStorage.setItem('popupDone', 'true');
                }}
            }}
        }};
        function showModal() {{ document.getElementById('supportModal').style.display = 'flex'; }}
        function closeModal() {{ document.getElementById('supportModal').style.display = 'none'; }}
    </script>
</body>
</html>"""

with open(filepath, 'w', encoding='utf-8') as f: f.write(book_html)

# --- 2. UPDATE LIBRARY DATA (FIXED) ---
library_file = "library.json"
library = []
if os.path.exists(library_file):
    with open(library_file, 'r', encoding='utf-8') as f: library = json.load(f)

library.append({"title": title, "author": author, "category": category, "link": f"books/{filename}"})
with open(library_file, 'w', encoding='utf-8') as f: json.dump(library, f, indent=4)

# --- 3. HOMEPAGE ---
cards = ""
for book in reversed(library):
    cards += f"""
    <a href="{book['link']}" class="group bg-white p-10 border-l-[12px] border-black shadow-sm hover:shadow-xl hover:-translate-y-2 transition-all duration-300 flex flex-col justify-between min-h-[280px]">
        <div>
            <span class="text-[10px] font-bold tracking-[3px] opacity-40 mb-4 block uppercase">{book['category']}</span>
            <h3 class="text-2xl font-bold italic leading-snug mb-2">{book['title']}</h3>
            <p class="text-sm opacity-60 italic">{book['author']}</p>
        </div>
        <div class="text-[11px] font-bold tracking-[2px] uppercase mt-8 group-hover:translate-x-2 transition-transform">Read Book →</div>
    </a>"""

index_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SyllabuswithRohit Library</title>
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#fdfbf7] text-[#1a1a1a] font-['Lora',serif]">
    <nav class="p-6 border-b border-black/5 flex justify-between items-center sticky top-0 bg-[#fdfbf7]/90 backdrop-blur-md z-50">
        <div class="text-xs font-bold tracking-[4px] uppercase">SyllabuswithRohit</div>
        <a href="{YT_LINK}" target="_blank" class="text-xs font-bold tracking-[2px] uppercase opacity-60 hover:opacity-100 border-b border-black">YouTube Community</a>
    </nav>
    <main class="max-w-6xl mx-auto px-6 py-24">
        <div class="flex flex-col items-center mb-24 text-center">
            <img src="myprofile.jpg" class="w-32 h-32 rounded-full object-cover mb-8 shadow-2xl border-4 border-white">
            <h1 class="text-3xl font-bold tracking-[5px] uppercase mb-4">SyllabuswithRohit</h1>
            <div class="h-px w-20 bg-black/20"></div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
            {cards}
        </div>
    </main>
</body>
</html>"""

with open("index.html", 'w', encoding='utf-8') as f: f.write(index_html)

# --- 4. PUSH ---
with open(draft_file, 'w', encoding='utf-8') as f: f.write("")
print("⏳ GitHub par Push ho raha hai...")
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", f"V20 Fixed: QR & Support for {title}"], check=True)
subprocess.run(["git", "push"], check=True)
print("🌟 SUCCESS! Website update ho gayi hai.")
