# Web Novel ePub Generator 📚

This is a web application built with Streamlit that allows you to download web novels and automatically convert them into ePub format.

## Features

- **URL Analysis**: Automatically extracts the chapter list from a novel's index page.
- **Smart Download**: Downloads the clean content of each chapter, removing unnecessary ads and scripts.
- **ePub Conversion**: Compiles all downloaded chapters into a single ePub file ready for reading.
- **Simple Interface**: Easy to use thanks to the intuitive user interface.

## Compatibility

> [!IMPORTANT]
> **Optimized for Novelfull.net**: The application was developed and tested primarily to work with the **Novelfull.net** website (and sites with similar structures).
>
> ⚠️ **Note for other sites**: Although the app attempts to adapt to different HTML structures, operation on sites other than Novelfull is **not guaranteed** and may require specific adaptations.

## Installation

1. Ensure you have Python installed.
2. Clone this repository or download the files.
3. Install the necessary dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:

```bash
streamlit run app.py
```

2. Enter the URL of the novel's index page (e.g., `https://novelfull.com/novel-name.html`).
3. Click on **Analyze** to find the chapters.
4. Once the chapters are found, click on **Download and Convert to ePub**.
5. Wait for the process to complete (a progress bar will show the progress).
6. Download the generated ePub file.

## Technologies

- **Streamlit**: For the web interface.
- **Requests & BeautifulSoup**: For web scraping.
- **EbookLib**: For creating ePub files.
