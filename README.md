# IOT Temp Web UI

Its a simple server written in Quart which is a wrapper around Flask but lets you use Asyncio. This will run inside a AWS EC2. For Production we shall consider using a AWS Elastic Beanstalk.

We use Quart so that we can run a WebSocket concurrentlu with the HTTP server. The WebSocket will be used to communicate with the RPi with the temperature controller. The user can set a Temp Control Policy in the Web UI and it will be sent through a web socket to the RPi.

The service also exposes an API to the database. The DB is hosted at AWS and is of DynamoDB. To get connected to the DB you have to install AWS CLI and store your Access Keys.

aws configure

