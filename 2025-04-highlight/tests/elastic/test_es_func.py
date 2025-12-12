"""
Copyright (c) SIOS Technology, Inc. All rights reserved.

MIT License
"""

from unittest import TestCase

from elastic.es_func import extract_search_results

class TestEsFunc(TestCase):
    """
    es_func内の関数をテストするためのクラス.
    """
    def test_extract_search_results_no_highlight(self):
        search_results = {
            'hits': {
                'hits': [
                    {'fields': {'content': 'test content 1'}},
                    {'fields': {'content': 'test content 2'}}
                ]
            }
        }
        expected = ['test content 1', 'test content 2']
        result = extract_search_results(search_results, has_highlight=False, field_name='content', max_count=2)
        # print(f'test_extract_search_results_no_highlight: {result}')
        assert result == expected, f'Expected {expected}, but got {result}'


    def test_extract_search_results_with_highlight(self):
        search_results = {
            'hits': {
                'hits': [
                    {'highlight': {'content': 'highlighted content 1'}, 'fields': {'content': 'test content 1'}},
                    {'highlight': {'content': 'highlighted content 2'}, 'fields': {'content': 'test content 2'}}
                ]
            }
        }
        expected = ['highlighted content 1', 'highlighted content 2']
        result = extract_search_results(search_results, has_highlight=True, field_name='content', max_count=2)
        # print(f'test_extract_search_results_with_highlight: {result}')
        assert result == expected, f'Expected {expected}, but got {result}'


    def test_extract_search_results_partial_highlight(self):
        search_results = {
            'hits': {
                'hits': [
                    {'highlight': {'content': 'highlighted content 1'}, 'fields': {'content': 'test content 1'}},
                    {'fields': {'content': 'test content 2'}}
                ]
            }
        }
        expected = ['highlighted content 1', 'test content 2']
        result = extract_search_results(search_results, has_highlight=True, field_name='content', max_count=2)
        # print(f'test_extract_search_results_partial_highlight: {result}')
        assert result == expected, f'Expected {expected}, but got {result}'


    def test_extract_search_results_exceed_max_count(self):
        search_results = {
            'hits': {
                'hits': [
                    {'fields': {'content': 'test content 1'}},
                    {'fields': {'content': 'test content 2'}},
                    {'fields': {'content': 'test content 3'}}
                ]
            }
        }
        expected = ['test content 1', 'test content 2']
        result = extract_search_results(search_results, has_highlight=False, field_name='content', max_count=2)
        # print(f'test_extract_search_results_exceed_max_count: {result}')
        assert result == expected, f'Expected {expected}, but got {result}'


    def test_extract_search_results_empty_results(self):
        search_results = {
            'hits': {
                'hits': []
            }
        }
        expected = []
        result = extract_search_results(search_results, has_highlight=False, field_name='content', max_count=2)
        # print(f'test_extract_search_results_empty_results: {result}')
        assert result == expected, f'Expected {expected}, but got {result}'

if __name__ == '__main__':
  unittest.main()
