from prereise.gather.griddata.hifld.data_access.load import _join_line_segments


def test_join_line_segments_single_segment():
    # Seattle to Tacoma via Seatac
    segments = [[(-122.34, 47.60), (-122.30, 47.44), (-122.44, 47.25)]]
    assert _join_line_segments(segments) is segments[0]


def test_join_line_segments_single_segment_after_filtering():
    segments = [
        # Long line with extremely similar start & end in Tacoma, should get filtered
        [(-122.45, 47.24), (-122.90, 47.04), (-122.45, 47.240001)],
        # Seattle to Tacoma via Seatac
        [(-122.34, 47.60), (-122.30, 47.44), (-122.44, 47.25)],
    ]
    assert _join_line_segments(segments) is segments[1]


def test_join_line_segments_two_segments():
    segments = [
        # Seattle to Tacoma via Seatac
        [(-122.34, 47.60), (-122.30, 47.44), (-122.44, 47.25)],
        # Olympia to a slightly different point in Tacoma
        [(-122.90, 47.04), (-122.45, 47.24)],
    ]
    joined_segments = _join_line_segments(segments)
    assert joined_segments == [
        (-122.34, 47.60),
        (-122.30, 47.44),
        (-122.44, 47.25),
        (-122.45, 47.24),
        (-122.90, 47.04),
    ]


def test_join_line_segments_three_segments():
    segments = [
        # Olympia to Tacoma
        [(-122.90, 47.04), (-122.45, 47.24)],
        # Seattle to a slightly different point in Tacoma via Seatac
        [(-122.34, 47.60), (-122.30, 47.44), (-122.44, 47.25)],
        # Seattle (exact same point) to Everett
        [(-122.34, 47.60), (-122.18, 47.99)],
    ]
    joined_segments = _join_line_segments(segments)
    assert joined_segments == [
        (-122.90, 47.04),
        (-122.45, 47.24),
        (-122.44, 47.25),
        (-122.30, 47.44),
        (-122.34, 47.60),
        (-122.34, 47.60),
        (-122.18, 47.99),
    ]


def test_join_line_segments_four_segments_non_linear():
    segments = [
        # Olympia to Tacoma
        [(-122.90, 47.04), (-122.45, 47.24)],
        # Seattle to Bellevue via Kenmore (should be dropped)
        [(-122.34, 47.60), (-122.253, 47.755), (-122.195, 47.603)],
        # Seattle to a slightly different point in Tacoma via Seatac
        [(-122.34, 47.60), (-122.30, 47.44), (-122.44, 47.25)],
        # Seattle (exact same point) to Everett
        [(-122.34, 47.60), (-122.18, 47.99)],
    ]
    joined_segments = _join_line_segments(segments)
    assert joined_segments == [
        (-122.90, 47.04),
        (-122.45, 47.24),
        (-122.44, 47.25),
        (-122.30, 47.44),
        (-122.34, 47.60),
        (-122.34, 47.60),
        (-122.18, 47.99),
    ]
