"""Tests for the news scraper (Phase 1 — collection and storage only).

Offline by convention, like the rest of `tests/`: RSS parsing, the dedupe hash,
the relevance filter and the query ladder are all exercised against inline XML
fixtures, never the network.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.dialects import postgresql

from app.modules.news import service, sources, symbols
from app.modules.news.models import NewsArticle
from app.modules.news.sources import RawArticle

# A trimmed but structurally faithful Google News RSS payload: it carries
# <title>, <link>, <guid>, <pubDate>, <source> — the fields the legacy scraper
# discarded.
RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>Google News</title>
<item>
  <title>Reliance Industries Q4 profit beats estimates - Business Today</title>
  <link>https://news.google.com/rss/articles/CBMi4gFBVV95</link>
  <guid>CBMi4gFBVV95</guid>
  <pubDate>Tue, 09 Apr 2024 07:00:00 GMT</pubDate>
  <source url="https://www.businesstoday.in">Business Today</source>
</item>
<item>
  <title>Reliance arm signs renewable deal - Moneycontrol</title>
  <link>https://news.google.com/rss/articles/CBMiZZZ99</link>
  <guid>CBMiZZZ99</guid>
  <pubDate>Wed, 10 Apr 2024 09:30:00 GMT</pubDate>
  <source url="https://www.moneycontrol.com">Moneycontrol</source>
</item>
</channel></rss>"""


class TestParseRss:
    def test_extracts_every_field(self):
        articles = sources.parse_rss(RSS_FIXTURE)
        assert len(articles) == 2

        first = articles[0]
        assert first.title.startswith("Reliance Industries Q4 profit")
        assert first.source == "Business Today"
        assert first.url == "https://news.google.com/rss/articles/CBMi4gFBVV95"
        assert first.published_at == datetime(2024, 4, 9, 7, 0, tzinfo=UTC)

    def test_publisher_suffix_kept_in_raw_title(self):
        """The raw title is stored verbatim; normalisation happens only for hashing."""
        assert sources.parse_rss(RSS_FIXTURE)[0].title.endswith("- Business Today")

    def test_empty_channel_returns_empty_list(self):
        empty = '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
        assert sources.parse_rss(empty) == []

    def test_malformed_xml_raises_loudly(self):
        """A broken feed must fail loudly rather than silently return nothing —
        this is the failure mode of the legacy regex scraper."""
        from xml.etree import ElementTree

        with pytest.raises(ElementTree.ParseError):
            sources.parse_rss("<rss><channel><item>broken")

    def test_missing_pubdate_becomes_none(self):
        payload = (
            '<?xml version="1.0"?><rss version="2.0"><channel><item>'
            "<title>Reliance Industries news without a date</title>"
            "</item></channel></rss>"
        )
        article = sources.parse_rss(payload)[0]
        assert article.published_at is None

    def test_item_without_title_is_skipped(self):
        payload = (
            '<?xml version="1.0"?><rss version="2.0"><channel><item>'
            "<pubDate>Tue, 09 Apr 2024 07:00:00 GMT</pubDate></item></channel></rss>"
        )
        assert sources.parse_rss(payload) == []


class TestBuildQuery:
    def test_uses_after_and_before_dates(self):
        query = sources.build_query(
            '"Reliance Industries" NSE',
            datetime(2024, 4, 1, tzinfo=UTC),
            datetime(2024, 4, 2, tzinfo=UTC),
        )
        assert query == '"Reliance Industries" NSE after:2024-04-01 before:2024-04-02'


class TestNormaliseTitle:
    def test_strips_publisher_suffix(self):
        assert (
            sources.normalise_title("Reliance Q4 profit beats - Business Today")
            == "reliance q4 profit beats"
        )

    def test_lowercases_and_collapses_punctuation(self):
        assert sources.normalise_title("Reliance's Q4: Profit, Up 14%!") == (
            "reliance s q4 profit up 14"
        )

    def test_same_headline_different_publishers_collide(self):
        """This is what makes cross-outlet dedupe work."""
        a = sources.normalise_title("Reliance Q4 profit beats estimates - Business Today")
        b = sources.normalise_title("Reliance Q4 profit beats estimates - Moneycontrol")
        assert a == b

    def test_genuinely_different_headlines_do_not_collide(self):
        assert sources.normalise_title("Reliance Q4 profit beats") != sources.normalise_title(
            "Reliance Q4 profit misses"
        )


class TestContentHash:
    def test_is_sha256_hex_of_normalised_title(self):
        expected = hashlib.sha256(b"reliance q4 profit beats").hexdigest()
        assert service.content_hash("Reliance Q4 profit beats - Business Today") == expected

    def test_len_is_64(self):
        assert len(service.content_hash("anything at all")) == 64

    def test_publisher_variant_produces_identical_hash(self):
        """The dedupe guarantee, asserted at the unit level."""
        assert service.content_hash("TCS profit surges - ET") == service.content_hash(
            "TCS profit surges - Moneycontrol"
        )


class TestSymbols:
    def test_universe_is_the_nifty_100_intersection(self):
        coverage = symbols.coverage()
        assert coverage["covered"] == len(symbols.targets())
        assert coverage["covered"] == 86
        assert coverage["nifty100_total"] == 100

    def test_targets_are_well_formed(self):
        for target in symbols.targets():
            assert target.symbol.endswith(".NS")
            assert target.base_symbol == target.symbol.removesuffix(".NS")
            assert target.display_name
            assert target.industry

    def test_lookup_by_full_and_bare_symbol(self):
        assert symbols.by_symbol("RELIANCE.NS").base_symbol == "RELIANCE"
        assert symbols.by_symbol("reliance").base_symbol == "RELIANCE"

    def test_unknown_symbol_returns_none(self):
        assert symbols.by_symbol("NOTATICKER") is None

    def test_every_target_is_in_the_app_instrument_master(self):
        """Guard against drift: the scraper must only cover symbols the app knows."""
        from app.modules.instruments import service as instruments

        known = {ticker for ticker in instruments.all_stocks().values()}
        for target in symbols.targets():
            assert target.symbol in known, target.symbol

    def test_query_ladder_is_ordered_most_precise_first(self):
        terms = symbols.by_symbol("RELIANCE.NS").query_terms()
        assert terms[0].startswith('"Reliance Industries" NSE')
        assert any("shares NSE" in term for term in terms)

    def test_corporate_suffix_stripped_from_query(self):
        terms = symbols.by_symbol("ADANIENT").query_terms()
        assert terms[0] == '"Adani Enterprises" NSE'
        assert "Ltd" not in terms[0]

    def test_ladder_has_no_duplicate_rungs(self):
        for target in symbols.targets():
            terms = target.query_terms()
            assert len(terms) == len(set(terms))


class TestIsRelevant:
    def _target(self) -> symbols.Target:
        return symbols.by_symbol("RELIANCE.NS")

    def test_accepts_company_name_in_title(self):
        article = RawArticle("Reliance Industries announces profit", "ET", None, None)
        assert service.is_relevant(article, self._target()) is True

    def test_rejects_unrelated_article(self):
        article = RawArticle("Saudi cricket team wins match", "ESPNcricinfo", None, None)
        assert service.is_relevant(article, self._target()) is False

    def test_rejects_ticker_appearing_inside_a_longer_word(self):
        """Regression guard: bare 'ACC' must not match American College of Cardiology."""
        target = symbols.Target(
            symbol="ACC.NS",
            base_symbol="ACC",
            display_name="ACC",
            nse_name="ACC Ltd",
            industry="Construction Materials",
        )
        article = RawArticle(
            "Get to Know ACC's president: American College of Cardiology", "MSN", None, None
        )
        assert service.is_relevant(article, target) is False

    def test_accepts_bare_symbol_as_standalone_token_for_long_symbols(self):
        target = symbols.Target(
            symbol="TCS.NS",
            base_symbol="TCS",
            display_name="TCS",
            nse_name="Tata Consultancy Services Ltd.",
            industry="Information Technology",
        )
        assert service.is_relevant(RawArticle("TCS wins deal", "ET", None, None), target) is True

    @pytest.mark.parametrize(
        ("symbol", "title", "expected"),
        [
            # The three-letter symbols in our universe that are also English
            # words or abbreviations — the false-positive risk that made the
            # bare-symbol fallback case-sensitive.
            ("HAL", "HAL Q2 profit beats estimates", True),
            ("HAL", "Hal Smith wins the match on Sunday", False),
            ("BEL", "BEL expands office footprint", True),
            ("BEL", "She belittled the proposal", False),
            ("ACC", "American College of Cardiology president speaks", False),
            ("ACC", "ACC cement company profit rises", True),
            ("TCS", "TCSs and other tech news", False),
            ("ITC", "itc compliance rules explained", False),
            # Punctuation-bearing symbol.
            ("M&M", "M&M wins order from government", True),
            # Ordinary longs.
            ("LIC", "LIC declares dividend", True),
            ("DLF", "DLF launches new project", True),
            ("BSE", "BSE Sensex crosses 80000", True),
        ],
    )
    def test_bare_symbol_guards(self, symbol, title, expected):
        target = symbols.Target(
            symbol=f"{symbol}.NS",
            base_symbol=symbol,
            display_name=symbol,
            nse_name=f"{symbol} Ltd",
            industry="Test",
        )
        assert service.is_relevant(RawArticle(title, "ET", None, None), target) is expected

    def test_is_standalone_helper_boundaries(self):
        assert service._is_standalone(" ACC ", " ACC profit ") is True
        assert service._is_standalone(" ACC ", " ACCS profit ") is False
        assert service._is_standalone(" M&M ", " M&M wins ") is True


class TestScrapeSymbolWindows:
    """The load-bearing behaviour: one request per day, not one per wide window."""

    async def test_issues_one_request_per_day(self, monkeypatch):
        calls: list[tuple[str, datetime, datetime]] = []

        async def fake_fetch(client, terms, start, end):
            calls.append((terms, start, end))
            return [RawArticle("Reliance Industries headline", "ET", None, None)]

        monkeypatch.setattr(service, "fetch_articles", fake_fetch)

        target = symbols.by_symbol("RELIANCE.NS")
        await service.scrape_symbol(  # type: ignore[arg-type]
            None, target, days=7, end=datetime(2024, 5, 1, tzinfo=UTC)
        )

        # Rung 1 hits on day one, so the ladder stops: 7 days = 7 requests,
        # one per 1-day window — not 1 request covering the whole range.
        assert len(calls) == 7
        assert {term for term, _, _ in calls} == {'"Reliance Industries" NSE'}

    async def test_every_window_is_exactly_one_day(self, monkeypatch):
        calls: list[tuple[datetime, datetime]] = []

        async def fake_fetch(client, terms, start, end):
            calls.append((start, end))
            return []

        monkeypatch.setattr(service, "fetch_articles", fake_fetch)

        target = symbols.by_symbol("RELIANCE.NS")
        await service.scrape_symbol(  # type: ignore[arg-type]
            None, target, days=3, end=datetime(2024, 5, 1, tzinfo=UTC)
        )

        assert calls
        assert all((end - start).days == 1 for start, end in calls)

    async def test_windows_walk_backwards_in_time(self, monkeypatch):
        ends: list[datetime] = []

        async def fake_fetch(client, terms, start, end):
            ends.append(end)
            return []

        monkeypatch.setattr(service, "fetch_articles", fake_fetch)

        target = symbols.by_symbol("RELIANCE.NS")
        await service.scrape_symbol(  # type: ignore[arg-type]
            None, target, days=4, end=datetime(2024, 5, 1, tzinfo=UTC)
        )

        # Nothing was found, so the ladder exhausts all 3 rungs x 4 days.
        assert len(ends) == 12
        # Within each rung the days are walked strictly backwards.
        first_rung = ends[:4]
        assert first_rung == sorted(first_rung, reverse=True)
        assert len(set(first_rung)) == 4

    async def test_falls_through_rungs_when_a_day_is_empty(self, monkeypatch):
        """A precise query that yields nothing must widen, not report a gap."""
        seen_terms: list[str] = []

        async def fake_fetch(client, terms, start, end):
            seen_terms.append(terms)
            return []

        monkeypatch.setattr(service, "fetch_articles", fake_fetch)
        target = symbols.by_symbol("RELIANCE.NS")
        await service.scrape_symbol(  # type: ignore[arg-type]
            None, target, days=1, end=datetime(2024, 5, 1, tzinfo=UTC)
        )

        assert len(seen_terms) == len(target.query_terms())
        assert seen_terms == list(target.query_terms())

    async def test_stops_at_first_rung_that_yields_results(self, monkeypatch):
        seen_terms: list[str] = []

        async def fake_fetch(client, terms, start, end):
            seen_terms.append(terms)
            return [RawArticle("Reliance Industries headline", "ET", None, None)]

        monkeypatch.setattr(service, "fetch_articles", fake_fetch)
        target = symbols.by_symbol("RELIANCE.NS")
        await service.scrape_symbol(  # type: ignore[arg-type]
            None, target, days=1, end=datetime(2024, 5, 1, tzinfo=UTC)
        )

        assert seen_terms == ['"Reliance Industries" NSE']

    async def test_wide_window_would_find_fewer_articles(self, monkeypatch):
        """Documents why day-by-day slicing exists, using the real parser."""
        calls: list[tuple[datetime, datetime]] = []

        async def fake_fetch(client, terms, start, end):
            calls.append((start, end))
            return []

        monkeypatch.setattr(service, "fetch_articles", fake_fetch)
        target = symbols.by_symbol("RELIANCE.NS")
        await service.scrape_symbol(  # type: ignore[arg-type]
            None, target, days=7, end=datetime(2024, 5, 1, tzinfo=UTC)
        )
        # 7 single-day windows, versus the 1 seven-day window the legacy
        # approach used (measured: 25% recall).
        assert all((end - start).days == 1 for start, end in calls)


class TestScrapeValidation:
    @pytest.mark.asyncio
    async def test_rejects_out_of_range_days(self):
        for bad in (0, -1, service.MAX_DAYS + 1):
            with pytest.raises(ValueError):
                await service.scrape(symbol="RELIANCE.NS", days=bad)

    @pytest.mark.asyncio
    async def test_unknown_symbol_raises(self):
        with pytest.raises(ValueError, match="not in the news scrape universe"):
            await service.scrape(symbol="NOSUCHTICKER", days=1)

    @pytest.mark.asyncio
    async def test_bare_symbol_is_accepted(self):
        """A bare NSE symbol resolves the same as the suffixed form."""
        target = symbols.by_symbol("RELIANCE")
        assert target is not None
        assert target.symbol == "RELIANCE.NS"


class TestScrapeStopsWhenSourceIsDown:
    """The load-bearing safety property: an outage must never look like a quiet day.

    `fetch_articles` used to return `[]` on network failure, which made a Google
    503 indistinguishable from "this stock had no news" — a backfill would store
    three years of nothing and report success.
    """

    @pytest.mark.asyncio
    async def test_source_failure_raises_rather_than_returning_empty(self, monkeypatch):
        async def always_down(*args, **kwargs):
            raise sources.SourceUnavailable("google news unavailable: HTTP 503")

        monkeypatch.setattr(service, "fetch_articles", always_down)

        stats = service.ScrapeStats()
        target = symbols.by_symbol("RELIANCE.NS")
        abort = asyncio.Event()

        await service.scrape_symbol(
            client=None,  # type: ignore[arg-type]  # never reached: fetch is stubbed
            target=target,
            days=3,
            end=datetime.now(UTC),
            stats=stats,
            semaphore=asyncio.Semaphore(1),
            abort=abort,
        )

        assert stats.aborted is True
        assert stats.errors == 1
        assert abort.is_set() is True

    @pytest.mark.asyncio
    async def test_abort_event_stops_remaining_requests(self, monkeypatch):
        """Once a window fails, the rest of the chunk must not be fired."""
        requests: list[str] = []

        async def always_down(client, terms, start, end, attempts=5):
            requests.append("request")
            raise sources.SourceUnavailable("HTTP 503")

        monkeypatch.setattr(service, "fetch_articles", always_down)

        stats = service.ScrapeStats()
        target = symbols.by_symbol("RELIANCE.NS")
        abort = asyncio.Event()
        abort.set()  # already aborted — no request should be made at all

        await service.scrape_symbol(
            client=None,  # type: ignore[arg-type]
            target=target,
            days=50,
            end=datetime.now(UTC),
            stats=stats,
            semaphore=asyncio.Semaphore(4),
            abort=abort,
        )

        assert requests == []

    @pytest.mark.asyncio
    async def test_preflight_failure_aborts_before_any_work(self, monkeypatch):
        """One stock over 1,000 days is ~1,000 requests. It must not start blind."""
        scraped: list[str] = []

        async def dead_preflight(client):
            raise sources.SourceUnavailable("HTTP 503")

        async def never_scrape(*args, **kwargs):
            scraped.append("scrape")
            return []

        monkeypatch.setattr(service, "preflight", dead_preflight)
        monkeypatch.setattr(service, "scrape_symbol", never_scrape)

        with pytest.raises(service.ScrapeAborted):
            await service.scrape(symbol="RELIANCE.NS", days=1000)

        assert scraped == []


class TestCheckpointing:
    """Days are committed in groups, so progress is visible while a crawl runs.

    A 1,000-day run at the measured rate cap is ~50 minutes. Committing only at
    the end means a crash discards all of it.
    """

    def test_checkpoint_interval_is_30_days(self):
        assert service.CHECKPOINT_EVERY_DAYS == 30

    def test_day_chunks_partition_the_window(self):
        chunks = service._day_chunks(1000, datetime(2026, 1, 1, tzinfo=UTC))
        # ceil, not floor: 1,000 days is 33 full chunks of 30 plus a 10-day remainder.
        assert len(chunks) == -(-1000 // service.CHECKPOINT_EVERY_DAYS)
        assert sum(len(c) for c in chunks) == 1000
        assert all(len(c) <= service.CHECKPOINT_EVERY_DAYS for c in chunks)

    def test_chunks_cover_exactly_one_day_each(self):
        for chunk in service._day_chunks(70, datetime(2026, 1, 1, tzinfo=UTC)):
            for start, end, _ in chunk:
                assert (end - start).days == 1

    def test_newest_days_come_first(self):
        """An interrupted run should have covered recent news before history."""
        stop_at = datetime(2026, 1, 31, tzinfo=UTC)
        chunks = service._day_chunks(60, stop_at)
        first_day = chunks[0][0][0]
        last_day = chunks[-1][-1][0]
        assert (stop_at - first_day).days == 1
        assert (stop_at - last_day).days == 60

    @pytest.mark.asyncio
    async def test_each_chunk_reaches_the_sink(self, monkeypatch):
        seen: list[int] = []

        async def fake(client, terms, windows, stats, sem, halt):
            return [
                RawArticle(f"Reliance Industries item {len(windows)}", "ET", None, None)
            ]

        async def sink(chunk):
            seen.append(len(chunk))

        monkeypatch.setattr(service, "_collect_for_windows", fake)
        target = symbols.by_symbol("RELIANCE.NS")

        await service.scrape_symbol(
            None,  # type: ignore[arg-type]
            target,
            days=90,
            end=datetime(2026, 1, 1, tzinfo=UTC),
            on_chunk=sink,
        )

        assert len(seen) == 3  # 90 days / 30

    @pytest.mark.asyncio
    async def test_skip_days_bypasses_already_stored_windows(self, monkeypatch):
        """A resumed run must not re-request days it already has articles for."""
        asked: list[tuple] = []

        async def fake(client, terms, windows, stats, sem, halt):
            asked.extend(windows)
            return []

        monkeypatch.setattr(service, "_collect_for_windows", fake)
        target = symbols.by_symbol("RELIANCE.NS")

        await service.scrape_symbol(
            None,  # type: ignore[arg-type]
            target,
            days=10,
            end=datetime(2026, 1, 11, tzinfo=UTC),
            skip_days=frozenset({date(2026, 1, 5), date(2026, 1, 6)}),
        )

        asked_days = {start.date() for start, _ in asked}
        assert date(2026, 1, 5) not in asked_days
        assert date(2026, 1, 6) not in asked_days
        # 8 surviving days, tried against all 3 query rungs because the stub
        # returns nothing and so the ladder widens.
        assert len(asked) == 8 * len(target.query_terms())


class TestBodyParsingDisabled:
    def test_fill_bodies_is_not_called_by_scrape(self):
        """Body extraction is disabled pending a source that serves publisher URLs.

        The function itself stays, intact and tested, so re-enabling is a
        two-line change rather than a rewrite.
        """
        import inspect

        assert "fill_bodies" not in inspect.getsource(service.scrape)

    def test_fill_bodies_still_exists(self):
        assert callable(service.fill_bodies)


class TestBodyExtraction:
    """Bodies come from a second fetch; the schema and windowing must hold."""

    def test_body_column_exists(self):
        from app.modules.news.models import NewsArticle

        assert "body" in NewsArticle.__table__.c

    def test_query_used_column_is_gone(self):
        from app.modules.news.models import NewsArticle

        assert "query_used" not in NewsArticle.__table__.c

    def test_body_fill_window_is_one_week(self):
        """Bodies are a weekly-refresh luxury, never a 3-year backfill."""
        assert service.BODY_FILL_DAYS == 7

    def test_backfill_window_would_not_qualify_for_bodies(self):
        """A 1095-day backfill stores headline-only rows by construction."""
        cutoff = datetime.now(UTC) - timedelta(days=service.BODY_FILL_DAYS)
        three_years_ago = datetime.now(UTC) - timedelta(days=1095)
        assert three_years_ago < cutoff


class TestScrapeStats:
    def test_as_dict_shape(self):
        stats = service.ScrapeStats(
            articles_seen=10, articles_new=4, duplicates=6, per_symbol={"RELIANCE.NS": 4}
        )
        payload = stats.as_dict()
        assert payload["articles_seen"] == 10
        assert payload["duplicates"] == 6
        assert payload["symbols_processed"] == 1

    def test_as_dict_reports_bodies_and_abort(self):
        payload = service.ScrapeStats(symbol="TCS.NS", bodies_stored=3, bodies_failed=1).as_dict()
        assert payload["symbol"] == "TCS.NS"
        assert payload["bodies_stored"] == 3
        assert payload["bodies_failed"] == 1
        assert payload["aborted"] is False


class TestStoreDedupe:
    """Deduplication is enforced by the database, so assert the contract exists."""

    def test_unique_constraint_is_declared(self):
        from app.modules.news.models import NewsArticle

        names = {c.name for c in NewsArticle.__table__.constraints if c.name}
        assert "uq_news_article_hash_symbol" in names

    def test_hash_and_symbol_are_the_constraint_columns(self):
        from app.modules.news.models import NewsArticle

        constraint = next(
            c
            for c in NewsArticle.__table__.constraints
            if c.name == "uq_news_article_hash_symbol"
        )
        assert {col.name for col in constraint.columns} == {"content_hash", "symbol"}


class TestBodyUpdateStatement:
    """The bulk body UPDATE took three attempts to get right.

    SQLAlchemy's ORM "bulk update by primary key" path rejected it twice at
    runtime — first demanding `synchronize_session=False`, then insisting the
    dicts be keyed by `id`, which collides with the reserved `id` bindparam. None
    of that is reachable without a live database, so the statement's shape is
    pinned here instead. Caught by `scripts`-level DB verification, not by the
    offline suite.
    """

    def _statement(self):
        from sqlalchemy import bindparam, update

        table = NewsArticle.__table__
        return (
            update(table)
            .where(table.c.id == bindparam("article_id"))
            .values({"body": bindparam("body")})
        )

    def test_compiles_against_the_postgres_dialect(self):
        sql = str(self._statement().compile(dialect=postgresql.dialect()))
        assert "UPDATE news_articles" in sql
        assert "SET body=" in sql

    def test_is_built_from_the_table_not_the_mapped_entity(self):
        """Passing `NewsArticle` instead of `NewsArticle.__table__` is what drags
        the statement into the ORM bulk path. Pin the target so it stays Core."""
        statement = self._statement()
        assert statement.table is NewsArticle.__table__

    def test_bind_name_avoids_the_reserved_id(self):
        sql = str(self._statement().compile(dialect=postgresql.dialect()))
        assert "news_articles.id = %(article_id)s" in sql


class TestBoilerplateFilter:
    """Added after a live run stored 30 RELIANCE articles, 26 of them junk.

    16 were Upstox auto-generated quote templates for unrelated companies
    ("Oberoi Realty Share Price - Upstox"). These matched the quoted-phrase query
    because the phrase constrains the query, not the results.
    """

    @pytest.mark.parametrize(
        "title",
        [
            "Oberoi Realty Share Price - Live NSE: OBEROIRLTY Stock Price & Chart - Upstox",
            "ITC Share Price - Upstox",
            "Amber Enterprises (I) Share Price - Upstox",
            "IEX Share Price - Upstox",
            "RELIANCE INDUSTRIES LTD Option Chain - Live RELIANCE INDUSTRIES LTD Option Chain",
            "HINDALCO Share Price Today - Hindalco Industries on NSE/BSE - scanx.trade",
            "Nifty 50 Index Today (NSEI) | Live Level - TechGraph",
            "Nifty 100 Index Price Today, Nifty 100 share price - Business Today",
            "Top 20 Energy Stocks To Buy In India For October 2026",
            "List of Petrochemical Stocks in India (2026) - INDmoney",
            "Large Cap Stocks BSE | List of Top Large Cap Companies BSE - Livemint",
        ],
    )
    def test_rejects_templated_pages(self, title):
        assert service.is_boilerplate(RawArticle(title, "Upstox", None, None)) is True

    @pytest.mark.parametrize(
        "title",
        [
            # Real headlines that contain the same words the patterns look for.
            "Reliance share price slips 2% after Q2 profit miss",
            "Reliance Industries Q4 profit beats estimates",
            "Hindustan Unilever to raise prices again, stock falls",
            "Why is Apollo Hospitals share price down 5% today? Supreme Court verdict",
            "Tata Steel wins top order, stock climbs",
            "Adani Ports raises cargo guidance for FY27",
        ],
    )
    def test_keeps_real_headlines(self, title):
        assert service.is_boilerplate(RawArticle(title, "ET", None, None)) is False

    def test_patterns_are_reusable_across_calls(self):
        """Regression guard: these were a generator, so `any()` consumed them.

        Every call after the first silently matched nothing — which is exactly
        what happened in the live run before it was caught.
        """
        junk = RawArticle("ITC Share Price - Upstox", "Upstox", None, None)
        real = RawArticle("Reliance Q2 profit beats estimates", "ET", None, None)
        for _ in range(5):
            assert service.is_boilerplate(junk) is True
            assert service.is_boilerplate(real) is False

    def test_boilerplate_is_checked_before_relevance(self):
        """A stock's own quote page is about it and still worthless."""
        target = symbols.by_symbol("RELIANCE.NS")
        article = RawArticle(
            "Reliance Industries Share Price - Live NSE: RELIANCE Stock Price & Chart - Upstox",
            "Upstox",
            None,
            None,
        )
        assert service.is_relevant(article, target) is True
        assert service.is_boilerplate(article) is True


class TestDistinctiveTokens:
    def test_strips_non_identifying_words(self):
        tokens = service._distinctive_tokens(symbols.by_symbol("RELIANCE.NS"))
        assert "reliance" in tokens
        assert "industries" not in tokens

    def test_falls_back_to_a_real_word_for_bank_names(self):
        """'State Bank of India' must not match on the word 'State'."""
        tokens = service._distinctive_tokens(symbols.by_symbol("SBIN.NS"))
        assert "state" not in tokens
        assert "bank" not in tokens

    def test_tokens_are_deduplicated(self):
        tokens = service._distinctive_tokens(symbols.by_symbol("RELIANCE.NS"))
        assert len(tokens) == len(set(tokens))

    def test_possessive_headline_is_accepted(self):
        """The recall case the old strict full-name substring test threw away."""
        target = symbols.by_symbol("RELIANCE.NS")
        article = RawArticle("Reliance's Andhra Pradesh CBG push gathers pace", "ET", None, None)
        assert service.is_relevant(article, target) is True


class TestQuotedRungIsFiltered:
    """The quoted-phrase bypass was the root cause of the junk in the corpus."""

    async def test_quoted_rung_does_not_bypass_the_filter(self, monkeypatch):
        async def junk_everywhere(client, terms, start, end):
            return [RawArticle("Oberoi Realty Share Price - Upstox", "Upstox", None, None)]

        monkeypatch.setattr(service, "fetch_articles", junk_everywhere)
        target = symbols.by_symbol("RELIANCE.NS")

        result = await service.scrape_symbol(  # type: ignore[arg-type]
            None, target, days=1, end=datetime(2024, 5, 1, tzinfo=UTC)
        )
        assert result == []

    async def test_quoted_rung_still_yields_real_news(self, monkeypatch):
        async def good(client, terms, start, end):
            return [RawArticle("Reliance Industries Q2 profit beats estimates", "ET", None, None)]

        monkeypatch.setattr(service, "fetch_articles", good)
        target = symbols.by_symbol("RELIANCE.NS")

        result = await service.scrape_symbol(  # type: ignore[arg-type]
            None, target, days=1, end=datetime(2024, 5, 1, tzinfo=UTC)
        )
        assert len(result) == 1

    def test_precise_helper_is_gone(self):
        """Nothing may reintroduce the "quoted means filtered" shortcut."""
        assert not hasattr(service, "_is_precise")


class TestOpenApiDocs:
    def test_news_endpoints_documented(self):
        from app.main import app

        paths = app.openapi()["paths"]
        assert "/api/v1/news/scrape" in paths
        assert "/api/v1/news/articles" in paths
        assert "/api/v1/news/coverage" in paths

    def test_scrape_is_a_post(self):
        from app.main import app

        assert "post" in app.openapi()["paths"]["/api/v1/news/scrape"]

    def test_scrape_takes_only_symbol_and_days(self):
        """The two-field contract is deliberate — see ScrapeRequest's docstring."""
        from app.main import app

        body = app.openapi()["paths"]["/api/v1/news/scrape"]["post"]["requestBody"]
        ref = body["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[-1]
        schema = app.openapi()["components"]["schemas"][ref]
        assert set(schema["properties"]) == {"symbol", "days"}

    def test_scrape_documents_the_days_parameter_and_truncation_reason(self):
        from app.main import app

        op = app.openapi()["paths"]["/api/v1/news/scrape"]["post"]
        description = op["description"]
        assert "one day at a time" in description
        assert "truncat" in description.lower()

    def test_news_tag_registered(self):
        from app.main import app

        tags = {t for path in app.openapi()["paths"].values() for op in path.values() for t in op.get("tags", [])}
        assert "news" in tags