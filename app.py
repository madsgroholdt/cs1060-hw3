from flask import Flask, render_template, request, jsonify
import requests
import os
import csv
from datetime import datetime

app = Flask(__name__)

# X API configuration
X_API_BASE_URL = "https://api.x.com/2"
X_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAJdKzQEAAAAAeeOP3pFY3tcnqYXO2r0Dt%2BUgXBk%3DcNoKdr5vnVV47ST5LQHkc8ZPmhiyVN7EzyqKTgl52GllQi12v8"

def get_x_user_id(username):
    """Get X user ID from username using X API v2"""
    headers = {
        "Authorization": f"Bearer {X_BEARER_TOKEN}"
    }
    print("Getting X user ID for username:", username)
    # First, we need to get the user ID from the username
    response = requests.get(
        f"{X_API_BASE_URL}/users/by/username/{username}",
        headers=headers
    )
    print("Response:", response.json())
    if response.status_code != 200:
        print("Failed to get X user ID for username:", username)
        return None
    
    # The response will contain a dictionary with the user information
    users = response.json().get('data', [])
    if not users:
        return None
        
    return users.get('id')

def get_x_user_tweets(user_id):
    """Get user's tweets using X API v2"""
    headers = {
        "Authorization": f"Bearer {X_BEARER_TOKEN}"
    }
    print('Getting tweets for user ID:', user_id)
    # Get user's tweets
    response = requests.get(
        f"{X_API_BASE_URL}/users/{user_id}/tweets",
        headers=headers,
        params={
            "max_results": 100,
            "tweet.fields": "created_at,text,possibly_sensitive"
        }
    )
    print("Response:", response.json())
    if response.status_code != 200:
        return None
        
    return response.json()

def save_tweets_to_csv(username, tweets_data):
    """Save tweets to a CSV file in the data/tweets directory"""
    if not tweets_data or 'data' not in tweets_data:
        return None
        
    filename = f"data/tweets/{username}.csv"
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Write tweets to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['tweet_id', 'created_at', 'text', 'possibly_sensitive']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for tweet in tweets_data['data']:
            writer.writerow({
                'tweet_id': tweet.get('id', ''),
                'created_at': tweet.get('created_at', ''),
                'text': tweet.get('text', ''),
                'possibly_sensitive': tweet.get('possibly_sensitive', False)
            })
    
    return filename

@app.route('/')
def home():
    return render_template('home.html', active_page='home')

@app.route('/lookup')
def lookup():
    return render_template('lookup.html', active_page='lookup')

@app.route('/api/fetch-data', methods=['POST'])
def fetch_data():
    data = request.json
    
    if 'x' in data:
        x_username = data['x']
        
        # Get X user ID
        user_id = get_x_user_id(x_username)
        if not user_id:
            return jsonify({
                'error': 'Could not find X user'
            }), 404
            
        # Get user's tweets
        tweets = get_x_user_tweets(user_id)
        if not tweets:
            return jsonify({
                'error': 'Could not fetch X tweets'
            }), 404
            
        # Save tweets to CSV
        csv_file = save_tweets_to_csv(x_username, tweets)
        
        return jsonify({
            'x_data': tweets,
            'csv_file': os.path.basename(csv_file) if csv_file else None
        })
    
    return jsonify({
        'error': 'No X username provided'
    }), 400

if __name__ == '__main__':
    app.run(debug=True)
