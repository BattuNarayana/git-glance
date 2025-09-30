# test_main.py

import pytest
from collections import Counter
from main import analyze_repo_languages

def test_analyze_repo_languages_happy_path():
    """
    Tests the language analysis function with a typical list of repositories.
    """
    # 1. ARRANGE: Set up our test data
    sample_repos = [
        {'language': 'Python'},
        {'language': 'Python'},
        {'language': 'JavaScript'},
        {'language': 'HTML'},
        {'language': 'Python'},
        {'language': 'JavaScript'},
    ]
    
    # 2. ACT: Call the function we are testing
    result = analyze_repo_languages(sample_repos)
    
    # 3. ASSERT: Check if the result is what we expect
    assert result['Python'] == 3
    assert result['JavaScript'] == 2
    assert result['HTML'] == 1
    assert isinstance(result, Counter)

def test_analyze_repo_languages_with_nones():
    """
    Tests that the function correctly ignores repositories where the language is None.
    """
    # 1. ARRANGE
    sample_repos = [
        {'language': 'Python'},
        {'language': None},  # This should be ignored
        {'language': 'JavaScript'},
        {'language': None},  # This should be ignored
    ]
    
    # 2. ACT
    result = analyze_repo_languages(sample_repos)
    
    # 3. ASSERT
    assert result['Python'] == 1
    assert result['JavaScript'] == 1
    assert None not in result  # Make sure 'None' was not counted as a language

def test_analyze_repo_languages_empty_list():
    """
    Tests that the function handles an empty list of repos gracefully.
    """
    # 1. ARRANGE
    sample_repos = []
    
    # 2. ACT
    result = analyze_repo_languages(sample_repos)
    
    # 3. ASSERT
    assert len(result) == 0
    assert isinstance(result, Counter)