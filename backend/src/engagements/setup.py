from setuptools import setup

setup(
    name='Rockwell',
    version='2.0.0',
    author='Robert Andion, Saumya Bhadani, Thomas Bivins, Giovanni Luca Ciampaglia',
    author_email='randion@usf.edu, sbhadani@usf.edu, thomasbivins@usf.edu, glc3@MAIL.USF.EDU',
    package_dir={"../..":"src"},
    scripts=[],
    url='https://github.com/glciampaglia/infodiversity-mock-social-media',
    license='LICENSE.md',
    description='Python backend for twitter authorization and information gathering/processing.',
    long_description=open('README.md').read(),
    install_requires=[
         "psycopg2-binary",
         "configparser",
         "flask",
         "flask-cors",
         "requests-oauthlib",
         "numpy",
         "bs4",
         "gunicorn",
         "python-dotenv"
    ],
)
