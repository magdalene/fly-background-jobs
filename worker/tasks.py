import os
from time import sleep

from mailjet_rest import Client


def test_task(name, last_name="Smith"):
    return f"Hello, {name} {last_name}"


def send_email(address, subject, body, to_name=None, from_email="shockley@dshockley.com", from_name="Darla Shockley"):
    if not to_name:
        to_name = address.split("@")[0]
    api_key = os.environ["MAILJET_API_KEY"]
    api_secret = os.environ["MAILJET_API_SECRET_KEY"]
    mailjet = Client(auth=(api_key, api_secret), version="v3.1")
    data = {
        "Messages": [
            {
                "From": {
                    "Email": from_email,
                    "Name": from_name
                },
                "To": [
                    {
                        "Email": address,
                        "Name": to_name
                    }
                ],
                "Subject": subject,
                "TextPart": body
            }
        ]
    }
    result = mailjet.send.create(data=data)
    if result.status_code >= 400:
        raise Exception(result.text)


def dummy_send_email(address, subject, body, to_name=None, from_email="shockley@dshockley.com", from_name="Darla Shockley"):
    # sleep a few seconds to simulate very slow email sending
    sleep(5)