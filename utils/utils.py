import requests
import smtplib
import json
import os
import locale
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from jinja2 import Template
from dotenv import load_dotenv


