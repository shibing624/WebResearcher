# -*- coding: utf-8 -*-
"""
@author:XuMing(xuming624@qq.com)
@description:
"""
import json
import unittest
from unittest import mock

import requests
import sys
sys.path.append('..')
from webresearcher.weather import get_weather


class TestWeatherMCPServer(unittest.TestCase):
    """Test cases for Weather MCP Server tools."""

    @mock.patch("requests.get")
    def test_get_weather_success(self, mock_get):
        """Test that get_weather returns data correctly when request succeeds."""
        # Mock response
        mock_response = mock.Mock()
        mock_response.text = "Weather data for London"
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response

        # Call the function
        result = get_weather("London")

        # Check assertions
        mock_get.assert_called_once_with("https://wttr.in/London")
        self.assertEqual(result, "Weather data for London")

    @mock.patch("requests.get")
    def test_get_weather_error(self, mock_get):
        """Test that get_weather handles errors properly."""
        # Mock raising an exception
        mock_get.side_effect = requests.RequestException("Connection error")

        # Call the function
        result = get_weather("London")

        # Check assertions
        mock_get.assert_called_once_with("https://wttr.in/London")
        self.assertIn("Connection error", result)


if __name__ == "__main__":
    unittest.main()
