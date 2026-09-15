import csv
import importlib.util
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("index", HERE.parent / "index.py")
ix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ix)


def page(root, typ, slug, url, title, lastmod="2026-01-01"):
    d = root / typ
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{slug}.md").write_text(
        f'---\nurl: "{url}"\ntitle: "{title}"\ntype: "{typ}"\nlastmod: "{lastmod}"\n---\n\nBody text.\n')


def test_index_and_products(tmp_path):
    pages = tmp_path / "pages"
    base = "https://www.realpage.com/"
    page(pages, "pages", "utility-management", base + "utility-management/", "Utility Management")
    page(pages, "pages", "billing", base + "utility-management/billing", "Utility Billing")
    page(pages, "pages", "security", base + "support/security", "Security")
    page(pages, "case-studies", "acme", base + "case-studies/acme/", "Acme Case Study")
    for i in range(60):
        page(pages, "posts", f"p{i}", base + f"blog/p{i}/", f"Post {i}", lastmod=f"2026-01-{i % 28 + 1:02d}")
    idx, prod = tmp_path / "index.md", tmp_path / "products.csv"
    ix.main(["--pages", str(pages), "--index-out", str(idx), "--products-out", str(prod)])

    text = idx.read_text()
    assert "[Utility Management](https://www.realpage.com/utility-management/)" in text
    assert "## Case Studies (1)" in text
    assert "## Posts (60 total, newest 50)" in text
    assert text.count("](https://www.realpage.com/blog/") == 50

    rows = list(csv.DictReader(prod.open()))
    assert [r["name"] for r in rows] == ["Utility Management"]  # support/ is not a product
    assert rows[0]["related"] == base + "utility-management/billing"
