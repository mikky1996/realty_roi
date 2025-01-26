FROM python:3.10-slim

# Create and change to the app directory.
WORKDIR /usr/src/app
RUN pip install --upgrade pip
RUN pip install pandas beautifulsoup4==4.12.3 aiogram==3.16.0 requests==2.32.3

COPY . .
RUN pip install .
WORKDIR /usr/src/app/cinemabot/cinemabot

EXPOSE 443

# Start the application
CMD [ "python", "/usr/src/app/cinemabot/server.py"]
