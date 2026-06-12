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
