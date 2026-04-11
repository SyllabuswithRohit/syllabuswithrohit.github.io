import os
import json
import math

LIBRARY_FILE = "library.json"
TEMPLATE_FILE = "_template.html"
BOOKS_DIR = "books"
INDEX_FILE = "index.html"

public_domains = [
    {"title": "The Origin of Consciousness", "author": "Julian Jaynes", "category": "Psychology", "text": "Consciousness, as we know it, is a recent development..."},
    {"title": "Three Essays on the Theory of Sexuality", "author": "Sigmund Freud", "category": "Psychology", "text": "The sexual instinct is present from birth..."},
    {"title": "Meditations", "author": "Marcus Aurelius", "category": "Philosophy", "text": "Waste no more time arguing what a good man should be. Be one."},
    {"title": "The Republic", "author": "Plato", "category": "Philosophy", "text": "He who is of calm and happy nature will hardly feel the pressure of age."},
    {"title": "Tao Te Ching", "author": "Laozi", "category": "Spirituality", "text": "The journey of a thousand miles begins with one step."},
    {"title": "Siddhartha", "author": "Hermann Hesse", "category": "Fiction", "text": "I have always thirsted for knowledge, I have always been full of questions."},
    {"title": "Notes from Underground", "author": "Fyodor Dostoevsky", "category": "Literature", "text": "To be acutely conscious is a disease, a real, honest-to-goodness disease."},
    {"title": "Beyond Good and Evil", "author": "Friedrich Nietzsche", "category": "Philosophy", "text": "He who fights with monsters might take care lest he thereby become a monster."},
    {"title": "On the Shortness of Life", "author": "Seneca", "category": "Philosophy", "text": "It is not that we have a short time to live, but that we waste a lot of it."},
    {"title": "The Art of War", "author": "Sun Tzu", "category": "Strategy", "text": "Appear weak when you are strong, and strong when you are weak."},
    {"title": "Relativity", "author": "Albert Einstein", "category": "Science", "text": "Imagination is more important than knowledge."},
    {"title": "The Prince", "author": "Niccolò Machiavelli", "category": "Politics", "text": "It is better to be feared than loved, if you cannot be both."}
]

def slugify_title(title: str) -> str:
    import re
    s = title.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "_", s).strip("_")
    return s

def paragraphs_from_raw(raw_text: str) -> str:
    return f"<p>{raw_text}</p>" * 15 # Generate some length

def build_mock_books():
    os.makedirs(BOOKS_DIR, exist_ok=True)
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    
    library = []
    
    for book in public_domains:
        title = book["title"]
        author = book["author"]
        category = book["category"]
        text = book["text"]
        
        slug = slugify_title(title)
        filepath = os.path.join(BOOKS_DIR, f"{slug}.html").replace("\\", "/")
        
        read_time = max(1, math.ceil((len(text.split()) * 15) / 200))
        content_html = paragraphs_from_raw(text)
        
        out = template
        out = out.replace("{{TITLE}}", title)
        out = out.replace("{{AUTHOR}}", author)
        out = out.replace("{{CATEGORY}}", category)
        out = out.replace("{{TIME}}", str(read_time))
        out = out.replace("{{CONTENT}}", content_html)
        out = out.replace("{{BOOK_TITLE_JSON}}", json.dumps(title, ensure_ascii=False))
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(out)
            
        library.append({
            "title": title,
            "author": author,
            "category": category,
            "link": filepath,
            "time": read_time,
        })
        print(f"Generated {filepath}")
        
    with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2, ensure_ascii=False)
        
    print("Mock books generated. Please re-run builder.py to update index.html")

if __name__ == "__main__":
    build_mock_books()
