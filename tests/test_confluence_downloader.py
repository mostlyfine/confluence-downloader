import base64 as _base64
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import confluence_downloader as cd
import requests as _req


class TestParseConfig:
    def test_parses_rows_with_depth(self, tmp_path):
        config = tmp_path / "config.csv"
        config.write_text("page_id,output_dir,depth\n1234,output,2\n")
        result = cd.parse_config(str(config))
        assert result == [{"page_id": "1234", "output_dir": "output", "depth": 2}]

    def test_defaults_depth_to_zero_when_missing(self, tmp_path):
        config = tmp_path / "config.csv"
        config.write_text("page_id,output_dir,depth\n5678,output/PRD\n")
        result = cd.parse_config(str(config))
        assert result == [{"page_id": "5678", "output_dir": "output/PRD", "depth": 0}]

    def test_skips_header_row(self, tmp_path):
        config = tmp_path / "config.csv"
        config.write_text("page_id,output_dir,depth\n1111,out,1\n")
        result = cd.parse_config(str(config))
        assert len(result) == 1

    def test_skips_comment_lines(self, tmp_path):
        config = tmp_path / "config.csv"
        config.write_text("page_id,output_dir,depth\n# comment\n1111,out,1\n")
        result = cd.parse_config(str(config))
        assert len(result) == 1

    def test_skips_empty_lines(self, tmp_path):
        config = tmp_path / "config.csv"
        config.write_text("page_id,output_dir,depth\n\n1111,out,1\n")
        result = cd.parse_config(str(config))
        assert len(result) == 1

    def test_parses_multiple_rows(self, tmp_path):
        config = tmp_path / "config.csv"
        config.write_text("page_id,output_dir,depth\n1111,out1,0\n2222,out2,3\n")
        result = cd.parse_config(str(config))
        assert len(result) == 2
        assert result[1] == {"page_id": "2222", "output_dir": "out2", "depth": 3}


class TestSanitizeFilename:
    def test_replaces_spaces_with_underscore(self):
        assert cd.sanitize_filename("My Page") == "My_Page"

    def test_replaces_slashes(self):
        assert cd.sanitize_filename("a/b\\c") == "a_b_c"

    def test_replaces_special_chars(self):
        assert cd.sanitize_filename('a:b*c?d"e<f>g|h') == "a_b_c_d_e_f_g_h"

    def test_normal_name_unchanged(self):
        assert cd.sanitize_filename("MyPage") == "MyPage"

    def test_leading_trailing_underscores_stripped(self):
        assert cd.sanitize_filename(" Page ") == "Page"

    def test_consecutive_special_chars_become_single_underscore(self):
        assert cd.sanitize_filename("a  b") == "a_b"

    def test_all_special_chars_returns_untitled(self):
        assert cd.sanitize_filename("???") == "untitled"


class TestGetAuthHeaders:
    def test_server_returns_bearer_token(self):
        headers = cd.get_auth_headers("https://conf.example.com", "my-pat")
        assert headers == {"Authorization": "Bearer my-pat"}

    def test_cloud_returns_basic_auth(self):
        headers = cd.get_auth_headers(
            "https://mysite.atlassian.net", "my-token", "user@example.com"
        )
        expected = _base64.b64encode(b"user@example.com:my-token").decode()
        assert headers == {"Authorization": f"Basic {expected}"}

    def test_cloud_detection_by_atlassian_net(self):
        headers = cd.get_auth_headers(
            "https://example.atlassian.net/wiki", "tok", "a@b.com"
        )
        assert headers["Authorization"].startswith("Basic ")

    def test_server_no_email_needed(self):
        headers = cd.get_auth_headers("https://internal.company.com/confluence", "pat-token")
        assert headers["Authorization"] == "Bearer pat-token"

    def test_cloud_raises_without_email(self):
        with pytest.raises(ValueError, match="CONFLUENCE_EMAIL"):
            cd.get_auth_headers("https://mysite.atlassian.net", "token", None)


class TestHtmlToMarkdown:
    def test_converts_paragraph(self):
        result = cd.html_to_markdown("<p>Hello world</p>")
        assert "Hello world" in result

    def test_converts_heading(self):
        result = cd.html_to_markdown("<h1>Title</h1>")
        assert "# Title" in result

    def test_converts_bold(self):
        result = cd.html_to_markdown("<strong>bold</strong>")
        assert "**bold**" in result

    def test_converts_link(self):
        result = cd.html_to_markdown('<a href="https://example.com">link</a>')
        assert "[link](https://example.com)" in result

    def test_converts_code_block(self):
        result = cd.html_to_markdown("<pre><code>print('hi')</code></pre>")
        assert "print('hi')" in result

    def test_converts_table(self):
        html = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
        result = cd.html_to_markdown(html)
        assert "A" in result and "1" in result


class TestSaveMarkdown:
    def test_creates_file_with_correct_name(self, tmp_path):
        path = cd.save_markdown(str(tmp_path), "My Page", "1234", "# Content")
        assert Path(path).name == "My_Page_1234.md"

    def test_writes_content_to_file(self, tmp_path):
        path = cd.save_markdown(str(tmp_path), "Page", "99", "# Hello")
        assert Path(path).read_text(encoding="utf-8") == "# Hello"

    def test_creates_output_directory_if_missing(self, tmp_path):
        out = str(tmp_path / "deep" / "dir")
        path = cd.save_markdown(out, "Page", "1", "content")
        assert Path(path).exists()

    def test_sanitizes_title_in_filename(self, tmp_path):
        path = cd.save_markdown(str(tmp_path), "My: Page/Title", "42", "x")
        assert Path(path).name == "My_Page_Title_42.md"


class TestFetchPage:
    def test_fetches_page_content(self):
        session = MagicMock()
        session.get.return_value.json.return_value = {
            "id": "1234",
            "title": "My Page",
            "body": {"storage": {"value": "<p>Hello</p>"}},
        }
        session.get.return_value.raise_for_status = MagicMock()
        result = cd.fetch_page(session, "https://conf.example.com", "1234")
        assert result["title"] == "My Page"
        assert result["body"]["storage"]["value"] == "<p>Hello</p>"

    def test_uses_wiki_prefix_for_cloud(self):
        session = MagicMock()
        session.get.return_value.json.return_value = {
            "id": "1", "title": "T", "body": {"storage": {"value": ""}},
        }
        session.get.return_value.raise_for_status = MagicMock()
        cd.fetch_page(session, "https://mysite.atlassian.net", "1")
        call_url = session.get.call_args[0][0]
        assert "/wiki/rest/api/content/1" in call_url

    def test_no_wiki_prefix_for_server(self):
        session = MagicMock()
        session.get.return_value.json.return_value = {
            "id": "1", "title": "T", "body": {"storage": {"value": ""}},
        }
        session.get.return_value.raise_for_status = MagicMock()
        cd.fetch_page(session, "https://conf.example.com", "1")
        call_url = session.get.call_args[0][0]
        assert "/wiki/" not in call_url
        assert "/rest/api/content/1" in call_url

    def test_raises_on_http_error(self):
        session = MagicMock()
        session.get.return_value.raise_for_status.side_effect = _req.HTTPError("404")
        with pytest.raises(_req.HTTPError):
            cd.fetch_page(session, "https://conf.example.com", "9999")


class TestFetchChildren:
    def test_returns_children(self):
        session = MagicMock()
        session.get.return_value.json.return_value = {
            "results": [{"id": "111", "title": "Child A"}, {"id": "222", "title": "Child B"}],
        }
        session.get.return_value.raise_for_status = MagicMock()
        result = cd.fetch_children(session, "https://conf.example.com", "1234")
        assert len(result) == 2
        assert result[0]["id"] == "111"

    def test_paginates_when_full_page(self):
        session = MagicMock()
        page1 = {"results": [{"id": str(i), "title": f"P{i}"} for i in range(25)]}
        page2 = {"results": [{"id": "99", "title": "Last"}]}
        session.get.return_value.json.side_effect = [page1, page2]
        session.get.return_value.raise_for_status = MagicMock()
        result = cd.fetch_children(session, "https://conf.example.com", "1234")
        assert len(result) == 26
        assert session.get.call_count == 2

    def test_raises_on_http_error(self):
        session = MagicMock()
        session.get.return_value.raise_for_status.side_effect = _req.HTTPError("500")
        with pytest.raises(_req.HTTPError):
            cd.fetch_children(session, "https://conf.example.com", "1234")

    def test_returns_empty_list_when_no_children(self):
        session = MagicMock()
        session.get.return_value.json.return_value = {"results": []}
        session.get.return_value.raise_for_status = MagicMock()
        result = cd.fetch_children(session, "https://conf.example.com", "1234")
        assert result == []


class TestApiPrefix:
    def test_returns_wiki_for_cloud(self):
        assert cd._api_prefix("https://mysite.atlassian.net") == "/wiki"

    def test_returns_empty_for_server(self):
        assert cd._api_prefix("https://conf.example.com") == ""

    def test_no_double_wiki_if_already_present(self):
        assert cd._api_prefix("https://mysite.atlassian.net/wiki") == ""


class TestProcessPage:
    def _page(self, pid, title):
        return {"id": pid, "title": title, "body": {"storage": {"value": f"<p>{title}</p>"}}}

    def _mock(self, *responses):
        session = MagicMock()
        mocks = []
        for data in responses:
            m = MagicMock()
            m.json.return_value = data
            m.raise_for_status = MagicMock()
            mocks.append(m)
        session.get.side_effect = mocks
        return session

    def test_saves_page_file(self, tmp_path):
        session = self._mock(self._page("1234", "My Page"))
        stats = {"saved": 0, "skipped": 0}
        cd.process_page(session, "https://conf.example.com", "1234", str(tmp_path), 0, stats)
        assert (tmp_path / "My_Page_1234.md").exists()
        assert stats["saved"] == 1

    def test_depth_zero_does_not_fetch_children(self, tmp_path):
        session = self._mock(self._page("1", "P"))
        stats = {"saved": 0, "skipped": 0}
        cd.process_page(session, "https://conf.example.com", "1", str(tmp_path), 0, stats)
        assert session.get.call_count == 1

    def test_depth_one_recurses_into_children(self, tmp_path):
        session = self._mock(
            self._page("1", "Parent"),
            {"results": [{"id": "2", "title": "Child"}]},
            self._page("2", "Child"),
        )
        stats = {"saved": 0, "skipped": 0}
        cd.process_page(session, "https://conf.example.com", "1", str(tmp_path), 1, stats)
        assert stats["saved"] == 2

    def test_skips_page_on_http_error(self, tmp_path):
        session = MagicMock()
        session.get.return_value.raise_for_status.side_effect = _req.HTTPError("404")
        stats = {"saved": 0, "skipped": 0}
        cd.process_page(session, "https://conf.example.com", "9999", str(tmp_path), 0, stats)
        assert stats["skipped"] == 1
        assert stats["saved"] == 0

    def test_skips_empty_content(self, tmp_path):
        page = {"id": "1", "title": "Empty", "body": {"storage": {"value": ""}}}
        session = self._mock(page)
        stats = {"saved": 0, "skipped": 0}
        cd.process_page(session, "https://conf.example.com", "1", str(tmp_path), 0, stats)
        assert stats["saved"] == 0
        assert not list(tmp_path.glob("*.md"))

    def test_empty_content_still_recurses_children(self, tmp_path):
        page = {"id": "1", "title": "Empty Parent", "body": {"storage": {"value": ""}}}
        session = self._mock(
            page,
            {"results": [{"id": "2", "title": "Child"}]},
            self._page("2", "Child"),
        )
        stats = {"saved": 0, "skipped": 0}
        cd.process_page(session, "https://conf.example.com", "1", str(tmp_path), 1, stats)
        assert stats["saved"] == 1
        assert (tmp_path / "Empty_Parent" / "Child_2.md").exists()

    def test_child_pages_saved_in_subdirectory(self, tmp_path):
        session = self._mock(
            self._page("1", "Parent"),
            {"results": [{"id": "2", "title": "Child"}]},
            self._page("2", "Child"),
        )
        stats = {"saved": 0, "skipped": 0}
        cd.process_page(session, "https://conf.example.com", "1", str(tmp_path), 1, stats)
        assert (tmp_path / "Parent" / "Child_2.md").exists()
