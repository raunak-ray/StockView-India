"""Tests for article body extraction.

Offline by convention: inline HTML fixtures shaped like the real publishers we
measured (livemint, ET, Moneycontrol), never the network.
"""

from __future__ import annotations

import pytest

from app.modules.news import extractor

# Structurally like a real publisher page: chrome, a story in <article>, related
# article teasers, and a legal footer.
PUBLISHER_HTML = """
<html><head><title>Q2 results</title><style>.x{color:red}</style></head>
<body>
  <nav>Home Markets Markets</nav>
  <header><h1>livemint</h1></header>
  <article>
    <p>Reliance Industries reported quarterly profit of 12,480 crore, ahead of
       the 11,900 crore estimate, as the oil-to-chemicals segment offset softer
       refining margins in the March quarter.</p>
    <p>The company said retail revenue rose 14% year on year, while Jio Platforms
       subscriber additions of 12.3 million were the highest in six quarters.</p>
    <p>Shares closed 1.8% higher on the National Stock Exchange, and analysts at
       three brokerages raised their target prices following the announcement.</p>
  </article>
  <aside><p>Also read: HDFC Bank Q2 profit rises 12% on net interest income.</p></aside>
  <div class="related"><p>Adani Enterprises wins a 4,000 crore solar order in
       Rajasthan, according to a company filing made to the exchanges.</p></div>
  <footer><p>All rights reserved. Read our terms of use and privacy policy.</p></footer>
  <script>var ad=1; track(ad);</script>
</body></html>
"""

# A JS-only shell: the text exists but the story never renders server-side.
JS_SHELL_HTML = """
<html><body>
  <div id="root"></div>
  <script>window.__DATA__={"body":"loaded client side"};</script>
</body></html>
"""


class TestExtractBody:
    def test_recovers_the_story(self):
        body = extractor.extract_body(PUBLISHER_HTML)
        assert body is not None
        assert "Reliance Industries reported quarterly profit" in body
        assert "Jio Platforms subscriber additions" in body

    def test_drops_footer_and_script(self):
        body = extractor.extract_body(PUBLISHER_HTML)
        assert body is not None
        assert "All rights reserved" not in body
        assert "track(ad)" not in body

    def test_drops_the_larger_related_teaser(self):
        """Related-article teasers are often longer than the story is deep.

        They must not win the density contest and become the stored body.
        """
        body = extractor.extract_body(PUBLISHER_HTML)
        assert body is not None
        assert "Adani Enterprises wins a 4,000 crore solar order" not in body

    def test_still_rejects_a_js_only_shell(self):
        assert extractor.extract_body(JS_SHELL_HTML) is None

    def test_empty_and_missing_html_return_none(self):
        assert extractor.extract_body(None) is None
        assert extractor.extract_body("") is None

    def test_malformed_html_does_not_raise(self):
        """A broken page must cost one body, never abort a whole run."""
        assert extractor.extract_body("<html><body><p>unclosed") is None or isinstance(
            extractor.extract_body("<html><body><p>unclosed"), str
        )

    def test_whitespace_is_collapsed(self):
        body = extractor.extract_body(PUBLISHER_HTML)
        assert body is not None
        assert "  " not in body


class TestGracefulDegradation:
    def test_extractor_capability_flag_exists(self):
        """Same optional-dependency contract as FINBERT_OK and NSE_AVAILABLE."""
        assert isinstance(extractor.EXTRACTOR_OK, bool)

    def test_extract_body_is_safe_when_unavailable(self, monkeypatch):
        monkeypatch.setattr(extractor, "EXTRACTOR_OK", False)
        assert extractor.extract_body(PUBLISHER_HTML) is None


class TestMinBodyChars:
    def test_threshold_is_stricter_than_a_paywall_stub(self):
        """A "Subscribe to continue" stub must not be stored as an article."""
        assert extractor.MIN_BODY_CHARS >= 200

    def test_stub_shorter_than_threshold_is_rejected(self):
        stub = "Subscribe to continue reading this article."
        page = f"<html><body><article><p>{stub}</p></article></body></html>"
        assert extractor.extract_body(page) is None


class TestPublicSchemaContract:
    def test_article_out_exposes_body(self):
        from app.modules.news.schemas import NewsArticleOut

        assert "body" in NewsArticleOut.model_fields

    def test_article_out_no_longer_exposes_query_used(self):
        from app.modules.news.schemas import NewsArticleOut

        assert "query_used" not in NewsArticleOut.model_fields


class TestScrapeRequestContract:
    def test_exactly_two_fields(self):
        """symbol + days, nothing else — the caller has no throttle to misconfigure."""
        from app.modules.news.schemas import ScrapeRequest

        assert set(ScrapeRequest.model_fields) == {"symbol", "days"}

    def test_days_default_is_the_weekly_window(self):
        from app.modules.news.schemas import ScrapeRequest

        assert ScrapeRequest.model_fields["days"].default == 7

    @pytest.mark.parametrize("bad", [0, -1, 3651])
    def test_days_is_bounded(self, bad):
        from pydantic import ValidationError

        from app.modules.news.schemas import ScrapeRequest

        with pytest.raises(ValidationError):
            ScrapeRequest(symbol="RELIANCE.NS", days=bad)