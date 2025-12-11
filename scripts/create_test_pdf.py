
def create_dummy_pdf(filename):
    # Minimal PDF structure
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f\n"
        b"0000000010 00000 n\n"
        b"0000000053 00000 n\n"
        b"0000000102 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>startxref\n"
        b"178\n"
        b"%%EOF"
    )
    with open(filename, "wb") as f:
        f.write(content)
    print(f"Created {filename}")

if __name__ == "__main__":
    create_dummy_pdf("test_rera.pdf")
