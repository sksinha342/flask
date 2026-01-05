import fitz    
doc = fitz.open("unlocked.pdf")
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)  
    pix.save(f"page_{i+1}.jpg")
doc.close()
