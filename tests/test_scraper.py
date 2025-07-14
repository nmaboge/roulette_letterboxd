import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from api.letterboxd_scraper import LetterboxdScraper


def test_valid_watchlist_url():
    scraper = LetterboxdScraper()
    url = "https://letterboxd.com/johndoe/watchlist/"
    assert scraper._is_valid_letterboxd_list_url(url) is True
    assert scraper.username == "johndoe"
    assert scraper.list_type == "watchlist"

def test_valid_films_url():
    scraper = LetterboxdScraper()
    url = "https://letterboxd.com/janedoe/films/"
    assert scraper._is_valid_letterboxd_list_url(url) is True
    assert scraper.username == "janedoe"
    assert scraper.list_type == "films"

def test_custom_list_url():
    scraper = LetterboxdScraper()
    url = "https://letterboxd.com/list/my-custom-list/"
    assert scraper._is_valid_letterboxd_list_url(url) is True
    assert scraper.list_type == "list"
    assert scraper.list_slug == "my-custom-list"

def test_invalid_url():
    scraper = LetterboxdScraper()
    url = "https://example.com/not-a-list/"
    assert scraper._is_valid_letterboxd_list_url(url) is False

