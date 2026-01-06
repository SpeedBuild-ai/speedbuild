import os
import sys
import requests
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import getFeatureFromApi, getFeature, findFeature

class TestMainFunctions(unittest.TestCase):

    def test_getFeatureFromApi(self):
        """Test getFeatureFromApi function"""
        result = getFeatureFromApi(1)
        self.assertIsNone(result)

    @patch('main.requests.get')
    def test_getFeature_success(self, mock_get):
        """Test getFeature with successful API response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "test feature"}
        mock_get.return_value = mock_response

        result = getFeature(1)
        self.assertEqual(result, {"id": 1, "name": "test feature"})
        mock_get.assert_called_once_with("http://127.0.0.1:9000/api/get-feature/1/")

    @patch('main.requests.get')
    def test_getFeature_failure_status(self, mock_get):
        """Test getFeature with non-200 status code"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = getFeature(1)
        self.assertIsNone(result)
        mock_get.assert_called_once_with("http://127.0.0.1:9000/api/get-feature/1/")

    @patch('main.requests.get')
    def test_getFeature_connection_error(self, mock_get):
        """Test getFeature with connection error"""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        result = getFeature(1)
        self.assertIsNone(result)
        mock_get.assert_called_once_with("http://127.0.0.1:9000/api/get-feature/1/")

    @patch('main.CodeChat')
    def test_findFeature(self, mock_codechat_class):
        """Test findFeature function"""
        mock_chat_instance = MagicMock()
        mock_codechat_class.return_value = mock_chat_instance
        mock_chat_instance.run.return_value = {
            "response": "Found the feature",
            "feature_id": 123,
            "instruction": "Use this code",
            "action": "apply_feature"
        }

        result = findFeature("query text", "framework name")
        expected_message = "framework : framework name\n\nquery : query text"
        mock_chat_instance.run.assert_called_once_with(expected_message)
        self.assertEqual(result, {
            "response": "Found the feature",
            "feature_id": 123,
            "instruction": "Use this code",
            "action": "apply_feature"
        })

if __name__ == '__main__':
    unittest.main()