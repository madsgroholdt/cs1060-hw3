# Scrubmeta - Mads Groeholdt: Homework 3

A powerful web application for analyzing social media content across X (formerly Twitter) and Reddit platforms. Scrubmeta helps users analyze social media posts and comments using advanced sentiment analysis.

## Features on the Application

- **Multi-Platform Analysis**: Fetch and analyze content from both X and Reddit
- **Sentiment Analysis**: Uses DistilBERT model to identify potentially sensitive or negative content
- **User-Friendly Interface**: Clean, modern UI for easy content lookup and analysis
- **High Accuracy**: Employs state-of-the-art natural language processing for reliable content analysis

## Setup

1. Clone the repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - `X_BEARER_TOKEN`: Your X (Twitter) API bearer token
   - `REDDIT_CLIENT_ID`: Your Reddit API client ID
   - `REDDIT_CLIENT_SECRET`: Your Reddit API client secret

## Usage

1. Start the application:

   ```bash
   python app.py
   ```

2. Navigate to `http://localhost:5000` in your web browser
3. Use the lookup interface to analyze social media content by username

## Technical Details

- **Backend**: Flask (Python)
- **ML Model**: DistilBERT for sentiment analysis
- **APIs**: X API v2, Reddit API
- **Frontend**: HTML5, CSS3 with responsive design

## Requirements

See `requirements.txt` for a complete list of dependencies. Key requirements include:

- Flask
- Transformers
- Requests

## Note

This application requires valid API credentials for both X and Reddit platforms to function properly. Make sure to set up your environment variables before running the application.
