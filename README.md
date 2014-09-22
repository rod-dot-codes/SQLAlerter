SQLAlerter
==========

SQL Alerter is a simple Python script to alert you once a particular MSSQL Job or Script has completed via Pushover.

Pushover is an application that you can install on your Phone or PC that acts as a simple messenger to recieve your API requests. You could quite easily replace this with an SMS or an e-mail, although I am a big fan of Pushover for teams of SQL Developers.

==Configuration

You need to set the following settings at the top of the file to get the application to work. 

You need to set the PUSHOVER API key and client key.

Furthermore, you need to specify whether you are on a Domain using Domain authentication or using user/password based authentication.

Thereafter, simply run the script: type in the name of the server you want to connect to and follow the prompts.
