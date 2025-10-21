import pytest
from local_tools_example import (
  delete_file,
  get_disk_size,
  get_ip,
  get_os_info,
  get_route,
  head_file,
  list_dir,
  regex_search_file,
  sha256_file,
  tail_file,
  write_file,
)


@pytest.fixture
def temp_file(tmp_path):
  d = tmp_path / "sub"
  d.mkdir()
  p = d / "test.txt"
  content = (
    "line 1\nline 2\nline 3\nfour\nfive\nsix\nseven\neight\nnine\nten\neleven"
  )
  p.write_text(content)
  return p


def test_non_existing_dir():
  with pytest.raises(FileNotFoundError):
    _ = list_dir("/non/existing/path")


def test_get_ip():
  ip_info = get_ip()
  assert isinstance(ip_info, str)
  assert "Error" not in ip_info


def test_get_route():
  route_info = get_route()
  assert isinstance(route_info, str)
  assert "Error" not in route_info


def test_get_os_info():
  os_info = get_os_info()
  assert isinstance(os_info, str)
  assert "System" in os_info


def test_sha256_file(temp_file):
  # SHA256 for the content in temp_file fixture
  expected_hash = (
    "330969838acbce80d2b049b501ed28c04f52980c88a21fcd9782c87ab33e3a6f"
  )
  file_hash = sha256_file(str(temp_file))
  assert file_hash == expected_hash


def test_tail_file(temp_file):
  last_lines = tail_file(str(temp_file), n_lines=3)
  assert last_lines == ["nine", "ten", "eleven"]


def test_head_file(temp_file):
  first_lines = head_file(str(temp_file), n_lines=3)
  assert first_lines == ["line 1", "line 2", "line 3"]


def test_regex_search_file(temp_file):
  matches = regex_search_file(str(temp_file), r"line \d")
  assert matches == ["line 1", "line 2", "line 3"]


def test_get_disk_size():
  disk_size = get_disk_size()
  assert isinstance(disk_size, str)
  assert "GiB" in disk_size
  assert "Error" not in disk_size


def test_write_and_delete_file(tmp_path):
  file_path = tmp_path / "test_write.txt"
  write_result = write_file(str(file_path), "hello world")
  assert "Successfully" in write_result
  assert file_path.read_text() == "hello world"

  delete_result = delete_file(str(file_path))
  assert "Successfully" in delete_result
  assert not file_path.exists()
