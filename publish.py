import os
import json
import subprocess
import math
import re

print("=========================================")
print("⚡ SyllabuswithRohit - V33 SEAMLESS ENGINE")
print("=========================================")

UPI_ID = "syllabuswithrohit@upi"
COFFEE_LINK = "https://buymeacoffee.com/SyllabuswithRohit"
YT_LINK = "https://www.youtube.com/@SyllabuswithRohit"

draft_file = "draft.txt"
if not os.path.exists(draft_file): open(draft_file, 'w').close()
with open(draft_file, 'r', encoding='utf-8') as f: content = f.read().strip()

shared_styles = """
    :root { --bg: #fdfbf7; --text: #1a1a1a; --accent: #000; --font-size: 21px; }
    body.sepia { --bg: #f4ecd8; --text: #2c1e0f; --accent: #6f421a; }
    body.dark { --bg: #121212; --text: #d1d1d1; --accent: #888888; }
    body.red-mode { --bg: #000000; --text: #ff0000; --accent: #ff0000; }
    
    /* HTMX Seamless Transitions */
    body { opacity: 1; transition: opacity 0.3s ease-out, background-color 0.4s, color 0.4s; background-color: var(--bg); color: var(--text); font-family: 'Lora', serif; overflow-x: hidden; }
    body.htmx-swapping { opacity: 0 !important; }
    
    .zen-nav { transition: transform 0.3s ease-in-out; }
    .zen-nav.hidden-nav { transform: translateY(-100%); }
    .nav-btn { font-size: 11px; font-weight: bold; padding: 6px 10px; border-radius: 6px; border: 1px solid rgba(128,128,128,0.2); cursor:pointer; background:transparent; color:inherit; transition: 0.2s; display:flex; align-items:center; gap:4px;}
    .nav-btn:hover { background: var(--text); color: var(--bg); }
    
    #scrollPercent { position: fixed; bottom: 20px; right: 20px; background: var(--text); color: var(--bg); padding: 5px 12px; border-radius: 20px; font-size: 12px; font-family: sans-serif; opacity: 0; transition: opacity 0.3s; z-index: 200; font-weight: bold; }
    article p { margin-bottom: 2.8rem; font-size: var(--font-size); line-height: 1.85; text-align: justify; transition: font-size 0.3s; }
    @media (max-width: 640px) { article p { line-height: 1.75; font-size: calc(var(--font-size) - 2px); } }

    .bionic-word b { font-weight: 800; opacity: 1; }
    .bionic-word { opacity: 0.85; }

    #supportModal { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:1000; align-items:center; justify-content:center; padding:20px; backdrop-blur: 5px; }
    .modal-content { background:var(--bg); color:var(--text); padding:40px; border-radius:15px; max-width:380px; width:100%; text-align:center; border: 2px solid var(--accent); position:relative; }
    .close-btn { position:absolute; top:10px; right:20px; font-size:32px; color:var(--text); opacity:0.6; cursor:pointer; background:none; border:none; }
"""

def generate_book_html(book_title, book_author, book_category, book_time, paragraphs_html, filename, word_count):
    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{book_title} | SyllabuswithRohit</title>
    <meta name="theme-color" content="#fdfbf7">
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.11"></script>
    <style>{shared_styles}</style>
</head>
<body hx-boost="true">
    <div id="pb" style="position:fixed; top:0; left:0; height:3px; background:var(--accent); width:0%; z-index:100;"></div>
    <div id="scrollPercent">0%</div>

    <nav id="navbar" class="zen-nav flex justify-between items-center px-4 py-3 fixed w-full top-0 bg-inherit border-b border-black/10 z-50 overflow-x-auto whitespace-nowrap hide-scrollbar">
        <a href="../index.html" class="font-sans text-[11px] font-bold tracking-[2px] uppercase shrink-0 mr-4" hx-target="body">← Library</a>
        <div class="flex items-center gap-2 shrink-0">
            <button onclick="toggleBionic()" class="nav-btn" title="Speed Reading Mode">⚡ <span class="hidden sm:inline">Speed</span></button>
            <button onclick="saveBookmark('{filename}', '{book_title}')" class="nav-btn" title="Save to My Books">🔖 <span class="hidden sm:inline">Save</span></button>
            <div class="w-px h-4 bg-gray-400 opacity-50 mx-1"></div>
            <button onclick="changeFont(-2)" class="nav-btn" title="Decrease Font">A-</button>
            <button onclick="changeFont(2)" class="nav-btn" title="Increase Font">A+</button>
            <div class="w-px h-4 bg-gray-400 opacity-50 mx-1"></div>
            <button onclick="setTheme('light')" class="nav-btn">L</button>
            <button onclick="setTheme('sepia')" class="nav-btn">S</button>
            <button onclick="setTheme('dark')" class="nav-btn">D</button>
            <button onclick="setTheme('red-mode')" class="nav-btn" style="color:#ff0000; border-color:#ff0000;">R</button>
        </div>
    </nav>

    <main class="max-w-[680px] mx-auto px-6 pt-28 pb-16">
        <header class="text-center mb-16">
            <div class="text-[10px] tracking-[4px] uppercase font-bold opacity-50 mb-4">{book_category} • {book_time} MIN READ • <span id="finish-time"></span></div>
            <h1 class="text-4xl md:text-5xl font-bold italic mb-4">{book_title}</h1>
            <p class="opacity-60 italic">By {book_author}</p>
        </header>
        <article id="content" data-words="{word_count}">{paragraphs_html}</article>
    </main>

    <div id="supportModal">
        <div class="modal-content">
            <button onclick="closeModal()" class="close-btn">&times;</button>
            <h2 class="text-2xl font-bold mb-4 italic">Support</h2>
            <div style="background:white; padding:10px; border-radius:10px; display:inline-block; margin-bottom:20px; border: 2px solid var(--accent);"><img src="../qr.png" class="w-40 h-40 object-contain"></div>
            <p class="text-sm opacity-80 mb-6 font-sans">Aapka support mujhe aur books laane me madad karega.</p>
            <a href="upi://pay?pa={UPI_ID}&pn=SyllabuswithRohit" style="background:var(--accent); color:var(--bg); padding:14px; border-radius:30px; display:block; font-size:11px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px; text-decoration:none;">Pay via UPI App</a>
            <a href="{COFFEE_LINK}" target="_blank" style="background:#FFDD00; color:#000; padding:14px; border-radius:30px; display:block; font-size:11px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; text-decoration:none;">Buy me a Coffee</a>
        </div>
    </div>

    <script>
        (function() {{
            const readMins = {book_time}; const finishDate = new Date(new Date().getTime() + readMins * 60000);
            document.getElementById('finish-time').innerText = "FINISH BY " + finishDate.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}});

            let wordsRead = parseInt(localStorage.getItem('wordsRead') || 0); let articleWords = parseInt(document.getElementById('content').getAttribute('data-words')); let hasCounted = false;

            window.setTheme = function(t) {{ document.body.className = t; localStorage.setItem('theme', t); let colors = {{ 'light': '#fdfbf7', 'sepia': '#f4ecd8', 'dark': '#121212', 'red-mode': '#000000' }}; document.querySelector('meta[name="theme-color"]').setAttribute('content', colors[t]); }}
            setTheme(localStorage.getItem('theme') || 'light');
            
            let currentFont = parseInt(localStorage.getItem('fontSize')) || 21; document.documentElement.style.setProperty('--font-size', currentFont + 'px');
            window.changeFont = function(step) {{ currentFont += step; if(currentFont < 16) currentFont = 16; if(currentFont > 32) currentFont = 32; document.documentElement.style.setProperty('--font-size', currentFont + 'px'); localStorage.setItem('fontSize', currentFont); }}

            const bookId = "pos_{filename}";
            let savedPos = localStorage.getItem(bookId); if(savedPos) window.scrollTo({{top: savedPos, behavior: 'auto'}});
            
            const today = new Date().toDateString(); let lastRead = localStorage.getItem('lastReadDate'); let streak = parseInt(localStorage.getItem('readingStreak') || 0);
            if (lastRead !== today) {{ let yesterday = new Date(); yesterday.setDate(yesterday.getDate() - 1); if (lastRead === yesterday.toDateString()) {{ streak++; }} else if (lastRead !== today) {{ streak = 1; }} localStorage.setItem('readingStreak', streak); localStorage.setItem('lastReadDate', today); }}

            let timer; let lastScrollTop = 0; const navbar = document.getElementById('navbar'); const scrollLabel = document.getElementById('scrollPercent');
            window.onscroll = () => {{
                const winScroll = document.documentElement.scrollTop; const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
                let scrolled = (winScroll / height) * 100; if (scrolled < 0) scrolled = 0; if (scrolled > 100) scrolled = 100;
                document.getElementById("pb").style.width = scrolled + "%"; scrollLabel.innerText = Math.round(scrolled) + "%"; scrollLabel.style.opacity = "1";
                if (scrolled > 80 && !hasCounted) {{ localStorage.setItem('wordsRead', wordsRead + articleWords); hasCounted = true; }}
                if (winScroll > lastScrollTop && winScroll > 100) {{ navbar.classList.add('hidden-nav'); }} else {{ navbar.classList.remove('hidden-nav'); }}
                lastScrollTop = winScroll <= 0 ? 0 : winScroll; localStorage.setItem(bookId, winScroll);
                clearTimeout(timer); timer = setTimeout(() => {{ scrollLabel.style.opacity = "0"; }}, 2000);
            }};

            window.showModal = function() {{ document.getElementById('supportModal').style.display = 'flex'; }}
            window.closeModal = function() {{ document.getElementById('supportModal').style.display = 'none'; }}
            setTimeout(() => {{ if(document.getElementById('supportModal').style.display !== 'flex') showModal(); }}, 900000);

            window.saveBookmark = function(id, title) {{ let marks = JSON.parse(localStorage.getItem('myBookmarks') || '[]'); if(!marks.find(b => b.id === id)) {{ marks.push({{id: id, title: title, link: "books/" + id + ".html"}}); localStorage.setItem('myBookmarks', JSON.stringify(marks)); alert("Book saved to your Library!"); }} else {{ alert("Already saved in your Library."); }} }}

            window.isBionic = false; window.originalHTML = document.getElementById('content').innerHTML;
            window.toggleBionic = function() {{
                const contentDiv = document.getElementById('content');
                if (window.isBionic) {{ contentDiv.innerHTML = window.originalHTML; window.isBionic = false; }} 
                else {{
                    let pTags = contentDiv.getElementsByTagName('p');
                    for (let p of pTags) {{ let words = p.innerText.split(' '); let bionicWords = words.map(word => {{ if (word.length <= 1) return word; let mid = Math.ceil(word.length / 2); return `<span class="bionic-word"><b>${{word.slice(0, mid)}}</b>${{word.slice(mid)}}</span>`; }}); p.innerHTML = bionicWords.join(' '); }}
                    window.isBionic = true;
                }}
            }}
        }})();
    </script>
</body>
</html>"""

# --- LIBRARY PROCESSING & BULK UPDATE ---
library_file = "library.json"
library = []
if os.path.exists(library_file):
    with open(library_file, 'r', encoding='utf-8') as f: library = json.load(f)

print("🔄 Installing 15KB Bypass Engine across all books...")
for b in library:
    old_filepath = b['link']
    if os.path.exists(old_filepath):
        with open(old_filepath, 'r', encoding='utf-8') as old_f: old_html = old_f.read()
        article_match = re.search(r'<article[^>]*>(.*?)</article>', old_html, re.DOTALL)
        if article_match:
            old_paras = article_match.group(1)
            b_word_count = len(re.sub(r'<[^>]+>', '', old_paras).split())
            b_filename = old_filepath.split('/')[-1].replace('.html', '')
            new_html = generate_book_html(b['title'], b['author'], b['category'], b.get('time', 5), old_paras, b_filename, b_word_count)
            with open(old_filepath, 'w', encoding='utf-8') as new_f: new_f.write(new_html)

if content:
    word_count = len(content.split())
    reading_time = math.ceil(word_count / 200)
    title = input("📚 Nayi Kitab ka Title: ")
    author = input("✍️ Original Writer: ")
    category = input("🏷️ Category: ")
    filename = title.lower().replace(" ", "_")
    filepath = f"books/{filename}.html"
    paras = "".join([f"<p>{p.strip()}</p>" for p in content.split('\n\n') if p.strip()])
    new_html = generate_book_html(title, author, category, reading_time, paras, filename, word_count)
    with open(filepath, 'w', encoding='utf-8') as f: f.write(new_html)
    
    new_book = {"title": title, "author": author, "category": category, "link": filepath, "time": reading_time, "words": word_count}
    if not any(b['title'] == title for b in library): library.append(new_book)
    else:
        for idx, b in enumerate(library):
            if b['title'] == title: library[idx] = new_book

with open(library_file, "w", encoding='utf-8') as f: json.dump(library, f, indent=4)

# --- GENERATE HOMEPAGE ---
cards = ""
for book in reversed(library):
    cards += f"""
    <a href="{book['link']}" hx-target="body" class="book-card group p-8 border-l-[10px] hover:-translate-y-2 transition-all duration-300 flex flex-col justify-between min-h-[250px]" style="background:var(--bg); border-color:var(--accent); border-top:1px solid rgba(128,128,128,0.2); border-right:1px solid rgba(128,128,128,0.2); border-bottom:1px solid rgba(128,128,128,0.2); box-shadow: 0 10px 30px -10px rgba(0,0,0,0.1);">
        <div>
            <span class="text-[9px] font-bold tracking-[3px] opacity-50 mb-4 block uppercase font-sans">{book['category']} • {book.get('time', 5)} MIN</span>
            <h3 class="book-title text-2xl font-bold italic leading-tight mb-2" style="color:var(--text);">{book['title']}</h3>
            <p class="text-sm opacity-70 italic" style="color:var(--text);">{book['author']}</p>
        </div>
        <div class="text-[10px] font-bold tracking-[2px] uppercase mt-6" style="color:var(--text);">Read Book →</div>
    </a>"""

index_html = f"""<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Library | SyllabuswithRohit</title>
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#fdfbf7">
    <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400..700;1,400..700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.11"></script>
    <style>{shared_styles}</style>
</head>
<body hx-boost="true">
    <nav class="flex justify-between items-center px-4 py-3 sticky top-0 bg-inherit border-b border-black/10 z-50">
        <div class="text-[11px] font-bold tracking-[2px] font-sans uppercase opacity-80">LIBRARY</div>
        <div class="flex items-center gap-2 md:gap-4">
            <button onclick="setTheme('light')" class="nav-btn">L</button>
            <button onclick="setTheme('sepia')" class="nav-btn">S</button>
            <button onclick="setTheme('dark')" class="nav-btn">D</button>
            <button onclick="setTheme('red-mode')" class="nav-btn" style="color:#ff0000; border-color:#ff0000;">R</button>
            <button onclick="showModal()" class="nav-btn ml-2">SUPPORT</button>
        </div>
    </nav>
    <main class="max-w-6xl mx-auto px-6 py-16">
        <div class="text-center mb-10">
            <img src="myprofile.jpg" class="w-24 h-24 rounded-full object-cover mx-auto mb-6 shadow-xl" style="border: 3px solid var(--accent);">
            
            <div class="flex flex-col md:flex-row justify-center items-center gap-6 mb-10">
                <h1 class="text-4xl md:text-5xl font-bold italic tracking-tight">SyllabuswithRohit</h1>
            </div>
            
            <div class="flex justify-center gap-6 font-sans">
                <div class="text-center">
                    <div id="streak-counter" class="text-3xl font-bold" style="color:var(--accent);">0</div>
                    <div class="text-[9px] font-bold tracking-[2px] uppercase opacity-50">Day Streak 🔥</div>
                </div>
                <div class="w-px bg-black opacity-10"></div>
                <div class="text-center">
                    <div id="words-counter" class="text-3xl font-bold" style="color:var(--accent);">0</div>
                    <div class="text-[9px] font-bold tracking-[2px] uppercase opacity-50">Words Read 📚</div>
                </div>
            </div>
        </div>

        <div class="max-w-md mx-auto mb-16 relative">
            <input type="text" id="searchBox" onkeyup="filterBooks()" placeholder="Search books..." class="w-full px-6 py-4 rounded-full border-2 text-sm font-sans focus:outline-none transition-colors" style="background:transparent; border-color:var(--accent); color:var(--text);">
        </div>
        
        <div id="bookmarks-section" class="mb-16 hidden">
            <h2 class="text-xs font-bold tracking-[3px] uppercase opacity-50 mb-6 font-sans">🔖 Your Bookmarks</h2>
            <div id="bookmarks-container" class="flex gap-4 overflow-x-auto pb-4 hide-scrollbar"></div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8" id="bookGrid">{cards}</div>
    </main>

    <div id="supportModal">
        <div class="modal-content">
            <button onclick="closeModal()" class="close-btn">&times;</button>
            <h2 class="text-2xl font-bold mb-4 italic">Support</h2>
            <div style="background:white; padding:10px; border-radius:10px; display:inline-block; margin-bottom:20px; border: 2px solid var(--accent);"><img src="qr.png" class="w-40 h-40 object-contain"></div>
            <p class="text-sm opacity-80 mb-6 font-sans">Aapka support mujhe aur books laane me madad karega.</p>
            <a href="upi://pay?pa={UPI_ID}&pn=SyllabuswithRohit" class="theme-btn-primary">Pay via UPI App</a>
            <a href="{COFFEE_LINK}" target="_blank" style="background:#FFDD00; color:#000; padding:14px; border-radius:30px; display:block; font-size:11px; font-weight:bold; letter-spacing:2px; text-transform:uppercase; text-decoration:none;">Buy me a Coffee</a>
        </div>
    </div>

    <script>
        (function() {{
            window.setTheme = function(t) {{ document.body.className = t; localStorage.setItem('theme', t); let colors = {{ 'light': '#fdfbf7', 'sepia': '#f4ecd8', 'dark': '#121212', 'red-mode': '#000000' }}; document.querySelector('meta[name="theme-color"]').setAttribute('content', colors[t]); }}
            setTheme(localStorage.getItem('theme') || 'light');
            window.showModal = function() {{ document.getElementById('supportModal').style.display = 'flex'; }}
            window.closeModal = function() {{ document.getElementById('supportModal').style.display = 'none'; }}
            
            window.filterBooks = function() {{
                let input = document.getElementById('searchBox').value.toLowerCase();
                let cards = document.getElementsByClassName('book-card');
                for (let i = 0; i < cards.length; i++) {{
                    let title = cards[i].querySelector('.book-title').innerText.toLowerCase();
                    if (title.indexOf(input) > -1) cards[i].style.display = 'flex';
                    else cards[i].style.display = 'none';
                }}
            }}

            document.getElementById('streak-counter').innerText = localStorage.getItem('readingStreak') || 0;
            document.getElementById('words-counter').innerText = (localStorage.getItem('wordsRead') || 0).toString().replace(/\B(?=(\d{{3}})+(?!\d))/g, ",");
            
            let marks = JSON.parse(localStorage.getItem('myBookmarks') || '[]');
            if(marks.length > 0) {{
                document.getElementById('bookmarks-section').classList.remove('hidden');
                let container = document.getElementById('bookmarks-container');
                marks.forEach(m => {{ container.innerHTML += `<a href="${{m.link}}" hx-target="body" class="shrink-0 w-64 p-6 border-l-[6px] transition-transform hover:-translate-y-1" style="background:var(--bg); border-color:var(--accent); border-top:1px solid rgba(128,128,128,0.2); border-right:1px solid rgba(128,128,128,0.2); border-bottom:1px solid rgba(128,128,128,0.2);"><h3 class="font-bold italic text-lg" style="color:var(--text);">${{m.title}}</h3><p class="text-[9px] uppercase tracking-[2px] mt-4 opacity-50" style="color:var(--text);">Resume →</p></a>`; }});
            }}
            if('serviceWorker' in navigator) {{ navigator.serviceWorker.register('sw.js'); }}
        }})();
    </script>
</body>
</html>"""
with open("index.html", 'w', encoding='utf-8') as f: f.write(index_html)

# --- PUSH ---
with open(draft_file, "w", encoding='utf-8') as f: f.write("")
print("⏳ GitHub par Push ho raha hai...")
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "V33 Seamless Engine: HTMX integration for instant navigation"], check=True)
subprocess.run(["git", "push"], check=True)
print("🌟 SEAMLESS ENGINE LIVE! Ab website reload nahi hogi, App ki tarah chalegi.")
