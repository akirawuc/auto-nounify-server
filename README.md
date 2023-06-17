# Auto-Nounify

Auto-Nounify is a tool developed using the poetry package, designed to simplify the process of adding "noggles" to pictures.

## Introduction

Auto-Nounify provides an easy and automated solution for adding noggles to pictures. Whether you want to enhance your images with a touch of whimsy, incorporate a particular cultural symbol, or simply have fun with visual modifications, this tool allows you to nounify your pictures with ease.

## Features

- Automatic Nounification: Auto-Nounify automates the process of adding noggles to pictures. It saves time and enables users to incorporate their desired visual elements seamlessly.

## Installation

To install and use Auto-Nounify, follow these steps:

1. Clone the repository: `git clone https://github.com/akirawuc/auto-nounify.git`
2. Navigate to the project directory: `cd auto-nounify`
3. Install the required dependencies using poetry: `poetry install`

## Usage

1. After installing the dependencies, you would need a service account from GCP, download the key file in json format, and specify the path to the key by `export GOOGLE_APPLICATION_CREDENTIAL="/path/to/the/key_file.json"`
2. Run the following command to activate the virtual environment: `poetry shell`
3. To nounify an image with noggles, you would need to replace the file path at line #85 and #86, more features to come (including inputing the file path and maybe a frontend)
4. The tool will process the image and generate a nounified version with noggles.
5. Enjoy your nounified picture!

## Contributing

Contributions to Auto-Nounify are welcome! If you find any issues or have suggestions for improvement, please feel free to open an issue or submit a pull request.
