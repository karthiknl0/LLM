from finetune import code_to_dataset as c2d


def test_chunks_respect_min_and_max():
    text = "\n".join(f"line {i}" for i in range(130))
    chunks = list(c2d._chunks(text))
    assert all(len(c.splitlines()) <= c2d.MAX_CHUNK_LINES for c in chunks)
    assert chunks  # 130 lines -> at least two chunks


def test_chunks_drops_tiny_tail():
    text = "\n".join(f"line {i}" for i in range(3))  # below MIN_CHUNK_LINES
    assert list(c2d._chunks(text)) == []


def test_iter_files_filters_extensions_and_skips_noise(tmp_path):
    (tmp_path / "keep.py").write_text("print(1)\n")
    (tmp_path / "notes.txt").write_text("ignore me\n")
    junk = tmp_path / "node_modules"
    junk.mkdir()
    (junk / "lib.js").write_text("x\n")

    found = {p.name for p in c2d._iter_files(tmp_path)}
    assert found == {"keep.py"}
