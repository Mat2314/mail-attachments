import pytest
import datetime
import os

from mail_connection import EmailConnector

@pytest.fixture(name="email_connector")
def fixture_email_connector():
    email_connector = EmailConnector("", "")
    return email_connector

def test_email_connector_initialization(email_connector):
    assert email_connector

@pytest.mark.parametrize("datestring, expected", (
    ("01-2022", (datetime.date(2022, 1, 1), datetime.date(2022, 1, 31))),
    ("02-2022", (datetime.date(2022, 2, 1), datetime.date(2022, 2, 28))),
    ("03-2022", (datetime.date(2022, 3, 1), datetime.date(2022, 3, 31))),
))
def test_convert_string_to_date_scope(email_connector, datestring, expected):
    assert email_connector.convert_string_to_date_scope(datestring) == expected

@pytest.mark.parametrize("wrong_datestring", (
    ("123"),
    (""),
))
def test_wrong_datestring_format(email_connector, wrong_datestring):
    with pytest.raises(ValueError):
        email_connector.convert_string_to_date_scope(wrong_datestring)
        
def test_initialize_error_log_file(email_connector):
    email_connector.initialize_error_log_file()
    assert os.path.isfile(email_connector.ERROR_LOGS_PATH)
    os.remove(email_connector.ERROR_LOGS_PATH)

def test_create_directory_if_not_exists(email_connector):
    email_connector.create_directory_if_not_exists()
    assert os.path.isdir(email_connector.DOWNLOAD_CATALOGUE)