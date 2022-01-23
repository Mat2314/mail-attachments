from imbox import Imbox
from getpass import getpass
import datetime
import calendar
from collections import namedtuple
import os
from dotenv import load_dotenv

load_dotenv()

DateScope = namedtuple("DateScope", "begin, end")

class EmailConnector(object):
    DOWNLOAD_CATALOGUE = "./attachments"
    ERROR_LOGS_PATH = "./error_logs.txt"

    def __init__(self, email: str, password: str, mail_server: str = None):
        self.mail_server = os.getenv("MAIL_SERVER") if os.getenv("MAIL_SERVER") else "imap.gmail.com"
        
        self.email = email
        self.password = password
        
        self.create_directory_if_not_exists()
        self.initialize_error_log_file()
        
    def initialize_error_log_file(self):
        """Create empty error log file"""
        # Create file if it doesn't exist
        if not os.path.isfile(self.ERROR_LOGS_PATH):
            open(self.ERROR_LOGS_PATH, "w").close()
        
        # Make it empty otherwise
        else:
            with open(self.ERROR_LOGS_PATH, "w") as err_file:
                err_file.write("")
        
    def create_directory_if_not_exists(self):
        """Creates attachments directory if it does not exist"""
        if not os.path.isdir(self.DOWNLOAD_CATALOGUE):
            os.mkdir(self.DOWNLOAD_CATALOGUE)
    
    def log_connection_errors(self, subject: str, date:str, message):
        """Save email erros into a file to inspect errors later on."""
        header = "".join([5*'-', subject, " ", date, 5*'-', "\n"])
        
        with open(self.ERROR_LOGS_PATH, "a") as error_file:
            error_file.write(header)
            error_file.write(message)
            error_file.write("\n\n")

    def convert_string_to_date_scope(self, datestring: str):
        """Convert mm-yyyy to scope tuple of datetime.date(...) (from, to).
            Example: 01-2022 --> ((2022, 1, 1), (2022, 1, 31))
        """
        # If string is not properly formatted raise an error
        if len(datestring) != 7:
            raise ValueError("Wrong datestring")

        # Retrieve month and year as numbers from given string
        month = int(datestring[:2])
        year = int(datestring[3:])

        # Get the last day of given month
        last_day = calendar.monthrange(year, month)[1]

        # Return the range
        return DateScope(datetime.date(year, month, 1), datetime.date(year, month, last_day))

    def retrieve_attachments_from_month(self, datestring: str, only_file_extension: str = None):
        """Connect to email account and retrieve all the attachments from all the messages
            that were received in a given month.
            Expected datestring format mm-yyyy
        """
        datescope = self.convert_string_to_date_scope(datestring)

        # Connect to the email account
        # imap.gmail.com
        with Imbox(self.mail_server,
                   username=self.email,
                   password=self.password,
                   ssl=True,
                   ssl_context=None,
                   starttls=False) as imbox:
            # Retrieve messages received in a given month
            inbox_messages_received_in_a_month = imbox.messages(date__gt=datescope.begin,
                                                                date__lt=datescope.end)
            for uid, m in inbox_messages_received_in_a_month:
                for idx, attachment in enumerate(m.attachments):
                    try:
                        attribute_filename = attachment.get('filename')
                        
                        # If the file is not with the desired extension, continue iteration
                        if only_file_extension:
                            if not attribute_filename.endswith(only_file_extension):
                                continue
                        
                        download_path = f"{self.DOWNLOAD_CATALOGUE}/{attribute_filename}"

                        with open(download_path, "wb") as fp:
                            fp.write(attachment.get('content').read())
                    except Exception as e:
                        print(f"Error -> {e}")
                        self.log_connection_errors(m.subject, str(m.date), str(e))


if __name__ == "__main__":
    email = input("Email: ")
    password = getpass()
    
    email_connector = EmailConnector(email, password)
    email_connector.retrieve_attachments_from_month("12-2021")
