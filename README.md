# Vagner Bessa's Personal Website Project

This project is a personal website built using a combination of Python, HTML/CSS, and JavaScript. The website showcases my skills and experience as a full-stack web developer.

## Requirements

* Linux
* Poetry package manager
* Node.js (for building the static site frontend)
* Docker (optional, for easy deployment)

## Features

* Responsive design using Tailwind CSS
* Asynchronous server using aiohttp for high efficiency
* Easy deployment using Docker
* Code highlighting using Prism.js

## Project Structure

The project is structured into the following directories:

* `src`: Contains the source code for the website
* `src/templates`: Contains HTML templates for the website
* `src/static`: Contains static assets such as CSS, JavaScript, and images
* `src/tailwindcss`: Contains configuration files for Tailwind CSS

## How to Use

1. Clone the repository: `git clone https://github.com/bessavagner/bessavagner-page.git`
2. Install dependencies: `pip install -r requirements.txt` or `poetry install`
3. Rename `.sample.env` to `.env` and make the necessary modifications.
4. Add execute permission to builder script: `chmod +x build.sh`
5. Build the project: `./build.sh`
6. Run the project: `python src/main.py`
7. Open the website in your browser: `http://0.0.0.0:8080`

## Customization

To customize the project for your own purpose, follow these steps:

1. Update the content on `src/templates` directory with your own.
4. Update the `app.py` file with your own Python code

## Development

### Build

1. Set `DEBUG="1"`, `INSTALL="1"` and `BUILD_TAILWINDCSS="1"` in the `.env` file.
2. Build the project: `./build.sh`

### Styles

Go to `scr/tailwindcss` and run `npm run dev` for continuous reloading of the `src/static/css/styles.css` file.

### Run server

To run locally

```bash
python src/main.py
```
To run in container:

1. Set in the `.env` file `PRODUCTION="1"`.
2. Build the project: `./build.sh`
3. Run a container: `docker run -p 8080:8080`
4. Open the website in your browser: `http://0.0.0.0:8081`


## Deployment

To deploy the project, follow these steps:

1. Set `DEBUG="0"`, `INSTALL="1"` and `BUILD_TAILWINDCSS="1"` in the `.env` file. For deployment with docker, also set `PRODUCTION="1"`
2. Build the project: `./build.sh`

## License

This project is licensed under the ISC License.

## Acknowledgments

* Tailwind CSS: [https://tailwindcss.com/](https://tailwindcss.com/)
* aiohttp: [https://aiohttp.readthedocs.io/en/stable/](https://aiohttp.readthedocs.io/en/stable/)
* Prism.js: [https://prismjs.com/](https://prismjs.com/)
* Docker: [https://www.docker.com/](https://www.docker.com/)