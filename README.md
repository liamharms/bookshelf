# bookshelf
A self-hosted home library application for bibliophiles who are starting to lose track of their books.
*Note: This project is still incomplete*
## Summary
This project gives the user an easy way to manage their books through its many features, such as storing book locations, custom tags for genres and types, and owners for families or other applications. It is intended to be hosted on a small computer that can be left running without intervention. As of right now, its scope extends only to home uses, but may be expanded for home libraries in the future.
## A Quick Look
![Homepage screenshot](https://github.com/liamharms/liamharms/blob/main/assets/bookshelf/readme/home_ss.png)
## Nice Features I'm Proud Of
- Typing or scanning in an ISBN autofills book information from Google Books and Openlibrary
- I'm rather partial to the aesthetic
## Installation
For those who wish to brave the installation, see below:
- Install and set up postgresql on the host
- Download the files in [src/](src/) to the desired directory
- Install the required libraries with `pip install -r requirements.txt` (Use a venv!)
- Create a `.env` file in `src/` with the following information:
```
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=postgresql://{username}:{password}@localhost:{port}/{database name}
SECRET_KEY={type a whole bunch of random characters here}
```
- Run `python src/app.py` and connect locally
**Congrats! If you know how to do that, you're all set!**