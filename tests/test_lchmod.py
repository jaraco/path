import errno
import os
import stat

import pytest

from path import Path


def test_lchmod_does_not_follow_symlinks(monkeypatch, tmp_path):
    item = Path(tmp_path / 'link')
    calls = []

    def fake_chmod(filename, mode, *, follow_symlinks=True):
        calls.append((filename, mode, follow_symlinks))

    monkeypatch.setattr(os, 'chmod', fake_chmod)

    assert item.lchmod(0o600) is item
    assert calls == [(item, 0o600, False)]


@pytest.mark.parametrize(
    'error',
    [PermissionError('denied'), NotImplementedError('unsupported')],
)
def test_lchmod_propagates_errors(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(os, 'chmod', fail)

    with pytest.raises(type(error)) as caught:
        Path('link').lchmod(0o600)

    assert caught.value is error


def test_lchmod_regular_file(tmp_path):
    item = Path(tmp_path / 'file.txt')
    item.write_text('content')

    assert item.lchmod(0o600) is item
    assert item.stat().st_mode & stat.S_IWRITE

    if os.name != 'nt':
        assert stat.S_IMODE(item.stat().st_mode) == 0o600


def test_lchmod_symlink_leaves_target_unchanged(tmp_path):
    target = tmp_path / 'target.txt'
    target.write_text('content')
    target.chmod(0o600)
    link = Path(tmp_path / 'link')

    try:
        os.symlink(target, link)
    except OSError as error:
        if getattr(error, 'winerror', None) == 1314:
            pytest.skip('Creating symlinks requires Windows privileges')
        raise

    before = stat.S_IMODE(target.stat().st_mode)

    try:
        result = link.lchmod(0o700)
    except NotImplementedError:
        pytest.skip('Symlink permissions are unsupported on this platform')
    except OSError as error:
        if error.errno in {errno.ENOTSUP, errno.EOPNOTSUPP}:
            pytest.skip('Symlink permissions are unsupported on this filesystem')
        raise

    assert result is link
    assert stat.S_IMODE(target.stat().st_mode) == before
    assert target.read_text() == 'content'

    if os.name != 'nt':
        assert stat.S_IMODE(link.lstat().st_mode) == 0o700
