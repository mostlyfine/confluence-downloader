import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import confluence_downloader as cd


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


import base64 as _base64


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
