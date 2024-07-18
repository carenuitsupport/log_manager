import logging
import logging.config
import logging.handlers
import traceback
from typing import override
import pyodbc
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import smtplib


# SQL HANDLER
class SQLServerHandler(logging.Handler):
    def __init__(self, server, driver, user, password, database, table):
        super().__init__()
        self.server = server
        self.driver = driver
        self.user = user
        self.password = password
        self.database = database
        self.table = table
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.conn = pyodbc.connect(
                f"DRIVER={self.driver};"
                f"SERVER={self.server};"
                f"UID={self.user};"
                f"PWD={self.password};"
                f"DATABASE={self.database}"
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            raise

    @override
    def emit(self, record):
        if self.conn is None:
            self.connect()

        try:

            sql = f"INSERT INTO {self.table} (LevelName, ModuleName, Message, PathName, FunctionName ,[LineNo], Exception, Stack, Created) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            self.cursor.execute(
                sql,
                (
                    record.levelname,
                    record.name,
                    record.getMessage(),
                    record.pathname,
                    record.funcName,
                    record.lineno,
                    self.format_exception(record.exc_info) if record.exc_info else None,
                    record.stack_info if record.stack_info else None,
                    self.format_timestamp(record.created),
                ),
            )
            self.conn.commit()
        except Exception as e:
            self.handleError(record)
            print(
                f"An error occurred while inserting log record into the database: {e}"
            )
            print(traceback.format_exc())

    def format_exception(self, exc_info):
        if exc_info:
            return "".join(traceback.format_exception(*exc_info))
        else:
            return None

    def format_timestamp(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )

    @override
    def close(self):
        if self.conn:
            self.conn.close()
        super().close()


# EMAIL HANDLER
class CustomSMTPHandler(logging.Handler):
    def __init__(self, mailhost, fromaddr, toaddrs, subject, secure=None, timeout=5.0):
        super().__init__()
        self.mailhost = mailhost
        self.fromaddr = fromaddr
        self.toaddrs = toaddrs
        self.subject = subject
        self.secure = secure
        self.timeout = timeout

    @override
    def emit(self, record):
        try:
            # Format the record
            message = self.format(record)
            # Create the email message
            msg = MIMEMultipart()
            msg["From"] = self.fromaddr
            msg["To"] = ",".join(self.toaddrs)
            msg["Date"] = formatdate(localtime=True)
            msg["Subject"] = self.subject

            # Attach the text message
            msg.attach(MIMEText(message, "html"))

            # Send the email
            smtp = smtplib.SMTP(self.mailhost, timeout=self.timeout)

            if self.secure:
                smtp.starttls()
            smtp.sendmail(self.fromaddr, self.toaddrs, msg.as_string())
            smtp.quit()
        except Exception:
            self.handleError(record)
