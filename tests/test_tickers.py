import unittest
from unittest.mock import patch, MagicMock
from lukhed_stocks.tickers import CatWrapper

class TestCatWrapper(unittest.TestCase):

    @patch('lukhed_stocks.tickers.rC.make_request')
    def test_get_cat_reported_equities(self, mock_get):
        # Mock response data
        mock_response = MagicMock()
        mock_response.content.decode.return_value = (
            'symbol|issueName|listingExchange|testIssueFlag\n'
            'A|Agilent Technologies Inc.|N|N\n'
            'AA|Alcoa Corporation|N|N\n'
            'AAA|Alternative Access First Priority CLO Bond ETF|P|N\n'
            'AAAIF|Alternative Investment Trust Unit|U|N\n'
            'AAAU|Goldman Sachs Physical Gold ETF Shares|Z|N\n'
            'AABB|Asia Broadband Inc Common Stock|U|N\n'
            'AABKF|AAREAL BANK AG NAMENS AKTIEN O N (Germany)|U|N\n'
            'AABVF|Aberdeen International Inc Ordinary Shares|U|N\n'
            'AACAF|AAC Technologies Holdings Inc Ordinary Shares (Cayman Islands)|U|N\n'
            'AACAY|AAC Technologies Holdings Inc Unsponsored ADR (Cayman Islands)|U|N'
        )
        mock_get.return_value = mock_response

        wrapper = CatWrapper()
        result = wrapper.get_cat_reported_equities()

        expected_output = [
            {
                'ticker': 'A',
                'issueName': 'Agilent Technologies Inc.',
                'listingExchange': 'N',
                'testIssueFlag': False,
                'fullData': ['A', 'Agilent Technologies Inc.', 'N', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AA',
                'issueName': 'Alcoa Corporation',
                'listingExchange': 'N',
                'testIssueFlag': False,
                'fullData': ['AA', 'Alcoa Corporation', 'N', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AAA',
                'issueName': 'Alternative Access First Priority CLO Bond ETF',
                'listingExchange': 'P',
                'testIssueFlag': False,
                'fullData': ['AAA', 'Alternative Access First Priority CLO Bond ETF', 'P', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AAAIF',
                'issueName': 'Alternative Investment Trust Unit',
                'listingExchange': 'U',
                'testIssueFlag': False,
                'fullData': ['AAAIF', 'Alternative Investment Trust Unit', 'U', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AAAU',
                'issueName': 'Goldman Sachs Physical Gold ETF Shares',
                'listingExchange': 'Z',
                'testIssueFlag': False,
                'fullData': ['AAAU', 'Goldman Sachs Physical Gold ETF Shares', 'Z', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AABB',
                'issueName': 'Asia Broadband Inc Common Stock',
                'listingExchange': 'U',
                'testIssueFlag': False,
                'fullData': ['AABB', 'Asia Broadband Inc Common Stock', 'U', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AABKF',
                'issueName': 'AAREAL BANK AG NAMENS AKTIEN O N (Germany)',
                'listingExchange': 'U',
                'testIssueFlag': False,
                'fullData': ['AABKF', 'AAREAL BANK AG NAMENS AKTIEN O N (Germany)', 'U', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AABVF',
                'issueName': 'Aberdeen International Inc Ordinary Shares',
                'listingExchange': 'U',
                'testIssueFlag': False,
                'fullData': ['AABVF', 'Aberdeen International Inc Ordinary Shares', 'U', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AACAF',
                'issueName': 'AAC Technologies Holdings Inc Ordinary Shares (Cayman Islands)',
                'listingExchange': 'U',
                'testIssueFlag': False,
                'fullData': ['AACAF', 'AAC Technologies Holdings Inc Ordinary Shares (Cayman Islands)', 'U', 'N'],
                'dataError': False
            },
            {
                'ticker': 'AACAY',
                'issueName': 'AAC Technologies Holdings Inc Unsponsored ADR (Cayman Islands)',
                'listingExchange': 'U',
                'testIssueFlag': False,
                'fullData': ['AACAY', 'AAC Technologies Holdings Inc Unsponsored ADR (Cayman Islands)', 'U', 'N'],
                'dataError': False
            }
        ]

        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()