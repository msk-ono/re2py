from re2py import re_to_post, post_to_nfa, match
import pytest


@pytest.mark.parametrize(
    ("re", "post"),
    [
        ("a", "a"),
        ("(a)", "a"),
        ("ab", "ab."),
        ("a*", "a*"),
        ("a+", "a+"),
        ("a?", "a?"),
        ("a|b", "ab|"),
        ("a(b|c)", "abc|."),
        ("ab|c", "ab.c|"),
        ("a(bb)+a", "abb.+.a."),
        ("a(bb|cc|a?)+a", "abb.cc.a?||+.a."),
    ],
)
def test_re_to_post(re, post):
    assert post == re_to_post(re)


def test_post_to_nfa():
    # TODO: Implement the nfa test in more detail
    x = post_to_nfa("a")
    assert x.is_out()
    assert x.char == "a"
    y = x.out
    assert y.is_match()


@pytest.mark.parametrize(
    ("re", "s", "is_match_case"),
    [
        ("a", "a", True),
        ("a", "ab", False),
        ("ab", "ab", True),
        ("ab", "abb", False),
        ("a*", "", True),
        ("a*", "a", True),
        ("a*", "aaaaaa", True),
        ("a*", "aaaaaab", False),
        ("a+", "a", True),
        ("a+", "aaaaaa", True),
        ("a+", "", False),
        ("a+", "aaaaaab", False),
        ("a?", "", True),
        ("a?", "a", True),
        ("a?", "ab", False),
        ("a?", "aaaaaa", False),
        ("a|bb", "a", True),
        ("a|bb", "bb", True),
        ("a|bb", "b", False),
        ("a(b|c)", "ab", True),
        ("a(b|c)", "ac", True),
        ("a(b|c)", "a", False),
        ("a(b|c)", "aa", False),
        ("a(bb)+a", "abba", True),
        ("a(bb)+a", "abbbba", True),
        ("a(bb)+a", "aa", False),
        ("a(bb)+a", "abbba", False),
        ("a(bb)+a", "abbac", False),
    ],
)
def test_match(re, s, is_match_case):
    if is_match_case:
        assert match(post_to_nfa(re_to_post(re)), s)
    else:
        assert not match(post_to_nfa(re_to_post(re)), s)
