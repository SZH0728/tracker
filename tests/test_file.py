# -*- coding:utf-8 -*-
# AUTHOR: Sun

"""
@brief 验证规范 tracker 文件的文本协议与原子访问。
@details 覆盖 File 的文本读取、同级暂存发布、异常透传与并发读写可见性。
"""

from pathlib import Path
from threading import Thread

import pytest

import file as file_module
from file import File, TRACKER_CONTENT_ENCODING


def test_tracker_content_encoding_is_utf8() -> None:
    """
    @brief 验证文件内容使用 UTF-8 编码。
    @return 无返回值。
    """
    assert TRACKER_CONTENT_ENCODING == 'utf-8'


def test_file_creates_its_own_lock(tmp_path: Path) -> None:
    first_boundary = File(tmp_path / 'first.txt')
    second_boundary = File(tmp_path / 'second.txt')

    assert first_boundary._lock is not second_boundary._lock  # type: ignore[attr-defined]  # 验证每个文件边界持有独立锁


def test_file_reads_existing_content_without_outer_whitespace(tmp_path: Path) -> None:
    tracker_path = tmp_path / 'trackers.txt'
    tracker_path.write_text(' udp://first.example\n', encoding=TRACKER_CONTENT_ENCODING)

    assert File(tracker_path).read() == 'udp://first.example'


def test_file_reads_empty_and_blank_content_as_empty(tmp_path: Path) -> None:
    tracker_path = tmp_path / 'trackers.txt'
    boundary = File(tracker_path)

    tracker_path.write_text('', encoding=TRACKER_CONTENT_ENCODING)
    assert boundary.read() == ''

    tracker_path.write_text(' \t\n', encoding=TRACKER_CONTENT_ENCODING)
    assert boundary.read() == ''


def test_file_raises_when_content_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        File(tmp_path / 'trackers.txt').read()


def test_file_raises_when_content_is_not_utf8(tmp_path: Path) -> None:
    tracker_path = tmp_path / 'trackers.txt'
    tracker_path.write_bytes(b'\xff')

    with pytest.raises(UnicodeDecodeError):
        File(tracker_path).read()


def test_file_rejects_non_text_content(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match='str'):
        File(tmp_path / 'trackers.txt').publish(123)  # type: ignore[arg-type]  # 验证运行时文本边界


def test_file_publishes_content_and_empty_content(tmp_path: Path) -> None:
    tracker_path = tmp_path / 'trackers.txt'
    temporary_path = tmp_path / 'trackers.txt.tmp'
    boundary = File(tracker_path)

    boundary.publish('udp://first.example\n')
    assert tracker_path.read_text(encoding=TRACKER_CONTENT_ENCODING) == 'udp://first.example\n'

    boundary.publish('')
    assert tracker_path.read_text(encoding=TRACKER_CONTENT_ENCODING) == ''
    assert not temporary_path.exists()
    assert list(tmp_path.iterdir()) == [tracker_path]


def test_file_replaces_stale_temporary_file(tmp_path: Path) -> None:
    tracker_path = tmp_path / 'trackers.txt'
    temporary_path = tmp_path / 'trackers.txt.tmp'
    temporary_path.write_text('udp://stale.example\n', encoding=TRACKER_CONTENT_ENCODING)

    File(tracker_path).publish('udp://next.example\n')
    assert tracker_path.read_text(encoding=TRACKER_CONTENT_ENCODING) == 'udp://next.example\n'
    assert not temporary_path.exists()


def test_file_preserves_existing_content_when_replace_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tracker_path = tmp_path / 'trackers.txt'
    temporary_path = tmp_path / 'trackers.txt.tmp'
    previous_content = 'udp://previous.example\n'
    tracker_path.write_text(previous_content, encoding=TRACKER_CONTENT_ENCODING)

    def raise_replace(source: Path, destination: Path) -> None:
        raise OSError('replace failed')

    monkeypatch.setattr(file_module, 'replace', raise_replace)

    with pytest.raises(OSError, match='replace failed'):
        File(tracker_path).publish('udp://next.example\n')

    assert tracker_path.read_text(encoding=TRACKER_CONTENT_ENCODING) == previous_content
    assert temporary_path.exists()


def test_file_raises_when_read_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tracker_path = tmp_path / 'trackers.txt'

    def raise_read(self: Path, encoding: str) -> str:
        raise OSError('read failed')

    monkeypatch.setattr(Path, 'read_text', raise_read)

    with pytest.raises(OSError, match='read failed'):
        File(tracker_path).read()


def test_file_readers_only_observe_complete_published_content(tmp_path: Path) -> None:
    tracker_path = tmp_path / 'trackers.txt'
    old_content = 'udp://old.example\n' * 4096
    new_content = 'udp://new.example\n' * 4096
    boundary = File(tracker_path)
    boundary.publish(old_content)

    observed_contents: list[str] = []

    def publish() -> None:
        boundary.publish(new_content)

    publisher = Thread(target=publish)
    publisher.start()
    while publisher.is_alive():
        observed_contents.append(boundary.read())
    publisher.join()
    observed_contents.append(boundary.read())

    assert observed_contents
    assert set(observed_contents) <= {old_content.strip(), new_content.strip()}
    assert new_content.strip() in observed_contents


if __name__ == '__main__':
    pass
