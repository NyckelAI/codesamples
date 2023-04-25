from near_duplicate_deduper import DuplicateClusterIdentifier


def test_two_linked():
    deduper = DuplicateClusterIdentifier()

    clusters = deduper([("a", "c"), ("a", "b")])
    assert len(clusters) == 1
    assert clusters[0] == set(["a", "b", "c"])


def test_two_mirrored():
    deduper = DuplicateClusterIdentifier()

    clusters = deduper([("a", "c"), ("c", "a")])
    assert len(clusters) == 1
    assert clusters[0] == set(["a", "c"])


def test_no_overlap():
    deduper = DuplicateClusterIdentifier()

    clusters = deduper([("a", "c"), ("d", "b")])
    assert len(clusters) == 2


def test_empty():
    deduper = DuplicateClusterIdentifier()

    clusters = deduper([])
    assert len(clusters) == 0


def test_three_linked():
    deduper = DuplicateClusterIdentifier()

    clusters = deduper([("a", "c"), ("b", "d"), ("a", "b")])
    print(clusters)
    assert len(clusters) == 1
    assert clusters[0] == set(["a", "b", "c", "d"])
