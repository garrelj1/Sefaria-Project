from sefaria.model import *
from sefaria.utils.util import list_depth


def test_verse_chunk():
    chunks = [
        TextChunk(Ref("Daniel 2:3"), "en", "The Holy Scriptures: A New Translation (JPS 1917)"),
        TextChunk(Ref("Daniel 2:3"), "he", "Tanach with Nikkud"),
        TextChunk(Ref("Daniel 2:3"), "en"),
        TextChunk(Ref("Daniel 2:3"), "he")
    ]
    for c in chunks:
        assert isinstance(c.text, basestring)
        assert len(c.text)


def test_chapter_chunk():
    chunks = [
        TextChunk(Ref("Daniel 2"), "en", "The Holy Scriptures: A New Translation (JPS 1917)"),
        TextChunk(Ref("Daniel 2"), "he", "Tanach with Nikkud"),
        TextChunk(Ref("Daniel 2"), "en"),
        TextChunk(Ref("Daniel 2"), "he")
    ]
    for c in chunks:
        assert isinstance(c.text, list)
        assert len(c.text)


def test_range_chunk():
    chunks = [
        TextChunk(Ref("Daniel 2:3-5"), "en", "The Holy Scriptures: A New Translation (JPS 1917)"),
        TextChunk(Ref("Daniel 2:3-5"), "he", "Tanach with Nikkud"),
        TextChunk(Ref("Daniel 2:3-5"), "en"),
        TextChunk(Ref("Daniel 2:3-5"), "he"),
    ]

    for c in chunks:
        assert isinstance(c.text, list)
        assert len(c.text) == 3


def test_spanning_chunk():
    chunks = [
        TextChunk(Ref("Daniel 2:3-4:5"), "en", "The Holy Scriptures: A New Translation (JPS 1917)"),
        TextChunk(Ref("Daniel 2:3-4:5"), "he", "Tanach with Nikkud"),
        TextChunk(Ref("Daniel 2:3-4:5"), "en"),
        TextChunk(Ref("Daniel 2:3-4:5"), "he")
    ]

    for c in chunks:
        assert isinstance(c.text, list)
        assert isinstance(c.text[0], list)
        assert len(c.text) == 3
        assert len(c.text[2]) == 5


def test_commentary_chunks():
    verse = TextChunk(Ref("Rashi on Exodus 3:1"), lang="he")
    rang = TextChunk(Ref("Rashi on Exodus 3:1-10"), lang="he")
    span = TextChunk(Ref("Rashi on Exodus 3:1-4:10"), lang="he")
    assert verse.text == rang.text[0]
    assert verse.text == span.text[0][0]

    verse = TextChunk(Ref("Rashi on Exodus 4:10"), lang="he")
    rang = TextChunk(Ref("Rashi on Exodus 4:1-10"), lang="he")
    assert rang.text[-1] == verse.text
    assert span.text[-1][-1] == verse.text


def test_spanning_family():
    f = TextFamily(Ref("Daniel 2:3-4:5"), context=0)

    assert isinstance(f.text, list)
    assert isinstance(f.he, list)
    assert len(f.text) == 3
    assert len(f.text[2]) == 5
    assert len(f.he) == 3
    assert len(f.he[2]) == 5
    assert isinstance(f.commentary[0], list)

    f = TextFamily(Ref("Daniel 2:3-4:5"))  # context = 1
    assert isinstance(f.text, list)
    assert isinstance(f.he, list)
    assert len(f.text) == 3
    assert len(f.text[2]) == 34
    assert len(f.he) == 3
    assert len(f.he[2]) == 34
    assert isinstance(f.commentary[0], list)




def test_family_chapter_result_no_merge():
    families = [
        TextFamily(Ref("Midrash Tanchuma.1.2")),  # this is supposed to get a version with exactly 1 en and 1 he.  The data may change.
        TextFamily(Ref("Daniel 2")),
        TextFamily(Ref("Daniel 4"), lang="en", version="The Holy Scriptures: A New Translation (JPS 1917)"),
        TextFamily(Ref("Daniel 4"), lang="he", version="Tanach with Nikkud")
    ]

    for v in families:
        assert isinstance(v.text, list)
        assert isinstance(v.he, list)

        c = v.contents()
        for key in ["text", "ref", "he", "book", "commentary"]:  # todo: etc.
            assert key in c


def test_chapter_result_merge():
    v = TextFamily(Ref("Mishnah_Yoma.1"))

    assert isinstance(v.text, list)
    assert isinstance(v.he, list)
    c = v.contents()
    for key in ["text", "ref", "he", "book", "sources", "commentary"]:  # todo: etc.
        assert key in c


def test_validate():
    passing_refs = [
        Ref("Exodus"),
        Ref("Exodus 3"),
        Ref("Exodus 3:4"),
        Ref("Exodus 3-5"),
        Ref("Exodus 3:4-5:7"),
        Ref("Exodus 3:4-7"),
        Ref("Rashi on Exodus"),
        Ref("Rashi on Exodus 3"),
        Ref("Rashi on Exodus 3:2"),
        Ref("Rashi on Exodus 3-5"),
        Ref("Rashi on Exodus 3:2-5:7"),
        Ref("Rashi on Exodus 3:2-7"),
        Ref("Rashi on Exodus 3:2:1"),
        Ref("Rashi on Exodus 3:2:1-3"),
        Ref("Rashi on Exodus 3:2:1-3:5:1"),
        Ref("Shabbat 7a"),
        Ref("Shabbat 7a-8b"),
        Ref("Shabbat 7a:12"),
        Ref("Shabbat 7a:12-23"),
        Ref("Shabbat 7a:12-7b:3"),
        Ref("Rashi on Shabbat 7a"),
        Ref("Rashi on Shabbat 7a-8b"),
        Ref("Rashi on Shabbat 7a:12"),
        Ref("Rashi on Shabbat 7a:12-23"),
        Ref("Rashi on Shabbat 7a:12-7b:3")
    ]
    for ref in passing_refs:
        TextChunk(ref, lang="he")._validate()
