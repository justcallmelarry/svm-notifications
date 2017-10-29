# svm-slack-notifications
Modules not installed with python 3.5 by default:
– aiohttp
– bs4

Instructions:
Add you username, password and webhook to the appropriate places in the json
file. Then do any changes you would wish to the slack payload (note that the
default settings will post to general and you might not want that)

If you prefer email notifications (or want both!), support for that is added
as well. Just add your gmail login credentials (an app password might be
required, it definatly is if you gave 2FA activated on your account).

Then just make the script run every once in a while (like every three hours)
via a cronjob and you will get notified for new activity on svm!
