import pytest
from unittest.mock import patch, MagicMock
from app.config import Settings
from app.dagger.aws_clients import AWSClients


class TestSettings:
    """Test cases for Settings class initialization and methods."""

    def test_settings_default_values(self):
        """Test that Settings initializes with correct default values."""
        # Act
        settings = Settings()

        # Assert
        assert settings.app_name == "Daylytics Backend"
        assert settings.debug is False
        assert settings.database_url == "sqlite:///./daylytics.db"
        assert (
            settings.kms_key_arn
            == "arn:aws:kms:us-west-2:792341830430:key/f46115bb-774a-4777-ab66-29903da24381"
        )
        assert settings.encrypted_toggl_api_token == "AQICAHg7rDJp72oZrIfl2vnBxkvlcidlgcJm7juguFV/iuWU+AEaxub94N2UG9z5FAZVO5DWAAAAfjB8BgkqhkiG9w0BBwagbzBtAgEAMGgGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMZ0EociGkIHEcd/LeAgEQgDsRzSYFs7mYrAFOAF5sbyRZxAqe+QZjlRGRfATwfbCIcAou6Xt1iwxZClYtH0CkOGCbaj+Nv/KIQ47sCQ=="
        assert settings.encrypted_toggl_email == "AQICAHg7rDJp72oZrIfl2vnBxkvlcidlgcJm7juguFV/iuWU+AGgr6DlKzWMviXYErFt/jDZAAAAdDByBgkqhkiG9w0BBwagZTBjAgEAMF4GCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMkz5Qkeft9mTcAuMeAgEQgDG+FJn6ReZNe6KngPHgIvdJ9RBSGq/Nx2JTClE6k9aaeE4+0rBPKYgs0TKr6PsFBdkq"
        assert settings.encrypted_toggl_password == "AQICAHg7rDJp72oZrIfl2vnBxkvlcidlgcJm7juguFV/iuWU+AE4eTN/RRoNeohMlPfTWPWHAAAAaDBmBgkqhkiG9w0BBwagWTBXAgEAMFIGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMqnQxOt64OqXCnPDdAgEQgCUkBJGegvNMFYl/+4PITgXcf7NE33uhUzYWRPcCORfVdXjFNxSS"
        assert settings._aws_clients is None

    def test_set_aws_clients(self):
        """Test that set_aws_clients stores AWS clients correctly."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)

        # Act
        settings.set_aws_clients(mock_aws_clients)

        # Assert
        assert settings._aws_clients is mock_aws_clients

    def test_set_aws_clients_updates_existing(self):
        """Test that set_aws_clients can update existing AWS clients."""
        # Arrange
        settings = Settings()
        mock_aws_clients_1 = MagicMock(spec=AWSClients)
        mock_aws_clients_2 = MagicMock(spec=AWSClients)

        # Act
        settings.set_aws_clients(mock_aws_clients_1)
        settings.set_aws_clients(mock_aws_clients_2)

        # Assert
        assert settings._aws_clients is mock_aws_clients_2
        assert settings._aws_clients is not mock_aws_clients_1


class TestTogglProperties:
    """Test cases for Toggl decrypted properties."""

    @patch("app.config.Settings.decrypt_value")
    def test_toggl_api_token_property(self, mock_decrypt_value):
        """Test that toggl_api_token property calls decrypt_value correctly."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)
        settings.set_aws_clients(mock_aws_clients)
        expected_decrypted = "decrypted_api_token"
        mock_decrypt_value.return_value = expected_decrypted

        # Act
        result = settings.toggl_api_token

        # Assert
        assert result == expected_decrypted
        mock_decrypt_value.assert_called_once_with(
            settings.encrypted_toggl_api_token, mock_aws_clients, settings.kms_key_arn
        )

    @patch("app.config.Settings.decrypt_value")
    def test_toggl_email_property(self, mock_decrypt_value):
        """Test that toggl_email property calls decrypt_value correctly."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)
        settings.set_aws_clients(mock_aws_clients)
        expected_decrypted = "decrypted_email"
        mock_decrypt_value.return_value = expected_decrypted

        # Act
        result = settings.toggl_email

        # Assert
        assert result == expected_decrypted
        mock_decrypt_value.assert_called_once_with(
            settings.encrypted_toggl_email, mock_aws_clients, settings.kms_key_arn
        )

    @patch("app.config.Settings.decrypt_value")
    def test_toggl_password_property(self, mock_decrypt_value):
        """Test that toggl_password property calls decrypt_value correctly."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)
        settings.set_aws_clients(mock_aws_clients)
        expected_decrypted = "decrypted_password"
        mock_decrypt_value.return_value = expected_decrypted

        # Act
        result = settings.toggl_password

        # Assert
        assert result == expected_decrypted
        mock_decrypt_value.assert_called_once_with(
            settings.encrypted_toggl_password, mock_aws_clients, settings.kms_key_arn
        )

    @patch("app.config.Settings.decrypt_value")
    def test_properties_use_stored_aws_clients(self, mock_decrypt_value):
        """Test that all properties use the stored _aws_clients instance."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)
        settings.set_aws_clients(mock_aws_clients)
        mock_decrypt_value.return_value = "decrypted_value"

        # Act
        _ = settings.toggl_api_token
        _ = settings.toggl_email
        _ = settings.toggl_password

        # Assert
        assert mock_decrypt_value.call_count == 3
        for call in mock_decrypt_value.call_args_list:
            args, _ = call
            assert (
                args[1] is mock_aws_clients
            )  # Second argument should be the stored AWS clients

    @patch("app.config.Settings.decrypt_value")
    def test_properties_use_correct_kms_key_arn(self, mock_decrypt_value):
        """Test that all properties use the correct kms_key_arn from settings."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)
        settings.set_aws_clients(mock_aws_clients)
        mock_decrypt_value.return_value = "decrypted_value"

        # Act
        _ = settings.toggl_api_token
        _ = settings.toggl_email
        _ = settings.toggl_password

        # Assert
        assert mock_decrypt_value.call_count == 3
        for call in mock_decrypt_value.call_args_list:
            args, _ = call
            assert (
                args[2] == settings.kms_key_arn
            )  # Third argument should be kms_key_arn

    @patch("app.config.Settings.decrypt_value")
    def test_toggl_api_token_property_bubbles_error(self, mock_decrypt_value):
        """Test that toggl_api_token property bubbles up errors from decrypt_value."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)
        settings.set_aws_clients(mock_aws_clients)
        test_error = ValueError("Decryption failed")
        mock_decrypt_value.side_effect = test_error

        # Act & Assert
        with pytest.raises(ValueError, match="Decryption failed"):
            _ = settings.toggl_api_token

    @patch("app.config.Settings.decrypt_value")
    def test_toggl_email_property_bubbles_error(self, mock_decrypt_value):
        """Test that toggl_email property bubbles up errors from decrypt_value."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)
        settings.set_aws_clients(mock_aws_clients)
        test_error = RuntimeError("KMS client error")
        mock_decrypt_value.side_effect = test_error

        # Act & Assert
        with pytest.raises(RuntimeError, match="KMS client error"):
            _ = settings.toggl_email

    @patch("app.config.Settings.decrypt_value")
    def test_toggl_password_property_bubbles_error(self, mock_decrypt_value):
        """Test that toggl_password property bubbles up errors from decrypt_value."""
        # Arrange
        settings = Settings()
        mock_aws_clients = MagicMock(spec=AWSClients)
        settings.set_aws_clients(mock_aws_clients)
        test_error = Exception("Unexpected error")
        mock_decrypt_value.side_effect = test_error

        # Act & Assert
        with pytest.raises(Exception, match="Unexpected error"):
            _ = settings.toggl_password
