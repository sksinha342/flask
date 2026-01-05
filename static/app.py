from PyPDF2 import PdfReader, PdfWriter

reader = PdfReader("loc.pdf")
reader.decrypt("121")   
writer = PdfWriter()
for p in reader.pages:
    writer.add_page(p)
with open("unloc.pdf", "wb") as f:
    writer.write(f)
