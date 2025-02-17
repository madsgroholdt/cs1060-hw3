from flask import Flask, render_template, request, jsonify
import requests
import os
import time
from transformers import pipeline

app = Flask(__name__)

# Initialize sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# X API configuration
X_API_BASE_URL = "https://api.x.com/2"
X_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAJdKzQEAAAAAeeOP3pFY3tcnqYXO2r0Dt%2BUgXBk%3DcNoKdr5vnVV47ST5LQHkc8ZPmhiyVN7EzyqKTgl52GllQi12v8"

# Reddit API configuration
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID', 'YOUR_REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET', 'YOUR_REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.environ.get('REDDIT_USER_AGENT', 'metascrub prototype 1.0 by /u/This_Speech5109')

def analyze_sentiment(text):
    """Analyze text sentiment and return if it's strongly negative (score > 0.9)"""
    try:
        result = sentiment_analyzer(text)
        return result[0]['label'] == 'NEGATIVE' and result[0]['score'] > 0.999
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return False

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
            "tweet.fields": "created_at,text"
        }
    )
    print("Response:", response.json())
    if response.status_code != 200:
        return None
        
    tweets_data = response.json()
    
    # Add sentiment analysis to tweets
    if 'data' in tweets_data:
        for tweet in tweets_data['data']:
            tweet['possibly_sensitive'] = analyze_sentiment(tweet['text'])
    
    return tweets_data

def get_reddit_access_token():
    """Get Reddit OAuth access token"""
    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    headers = {'User-Agent': REDDIT_USER_AGENT}
    data = {
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data=data,
            headers=headers
        )
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"Error getting Reddit access token: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Exception getting Reddit access token: {e}")
        return None

def get_reddit_user_data(username):
    """Get user's posts and comments from Reddit"""
    access_token = get_reddit_access_token()
    if not access_token:
        return None
        
    headers = {
        'User-Agent': REDDIT_USER_AGENT,
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        # Get user's submissions (posts)
        posts_response = requests.get(
            f'https://oauth.reddit.com/user/{username}/submitted',
            headers=headers,
            params={'limit': 50}
        )
        
        # Add a small delay between requests
        time.sleep(1)
        
        # Get user's comments
        comments_response = requests.get(
            f'https://oauth.reddit.com/user/{username}/comments',
            headers=headers,
            params={'limit': 50}
        )
        
        if posts_response.status_code != 200 or comments_response.status_code != 200:
            print(f"Reddit API Error - Posts Status: {posts_response.status_code}, Comments Status: {comments_response.status_code}")
            print(f"Posts Response: {posts_response.text[:200]}")
            print(f"Comments Response: {comments_response.text[:200]}")
            return None
            
        posts_data = posts_response.json()
        comments_data = comments_response.json()
        
        # Combine and format the data
        combined_data = []
        
        # Process posts
        for post in posts_data.get('data', {}).get('children', []):
            post_data = post['data']
            text = post_data.get('title', '') + '\n' + (post_data.get('selftext') or '')
            
            # Use sentiment analysis instead of over_18 flag
            is_negative = analyze_sentiment(text)
            
            combined_data.append({
                'id': post_data.get('id'),
                'created_at': post_data.get('created_utc'),
                'text': text,
                'type': 'post',
                'subreddit': post_data.get('subreddit'),
                'score': post_data.get('score'),
                'possibly_sensitive': is_negative,
                'url': f"https://old.reddit.com{post_data.get('permalink')}"
            })
            
        # Process comments
        for comment in comments_data.get('data', {}).get('children', []):
            comment_data = comment['data']
            text = comment_data.get('body', '')
            
            # Use sentiment analysis for comments too
            is_negative = analyze_sentiment(text)
                
            combined_data.append({
                'id': comment_data.get('id'),
                'created_at': comment_data.get('created_utc'),
                'text': text,
                'type': 'comment',
                'subreddit': comment_data.get('subreddit'),
                'score': comment_data.get('score'),
                'possibly_sensitive': is_negative,
                'url': f"https://old.reddit.com{comment_data.get('permalink')}"
            })
            
        return {
            'data': sorted(combined_data, key=lambda x: x['created_at'], reverse=True)
        }
        
    except Exception as e:
        print(f"Error fetching Reddit data: {e}")
        return None

@app.route('/')
def home():
    return render_template('home.html', active_page='home')

@app.route('/lookup')
def lookup():
    return render_template('lookup.html', active_page='lookup')

@app.route('/api/fetch-data', methods=['POST'])
def fetch_data():
    data = request.json
    response_data = {}
    
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
            
        response_data['x_data'] = tweets
        
    if 'reddit' in data:
        reddit_username = data['reddit']
        reddit_data = get_reddit_user_data(reddit_username)
        
        if not reddit_data:
            return jsonify({
                'error': 'Could not fetch Reddit data'
            }), 404
            
        response_data['reddit_data'] = reddit_data
    
    if not response_data:
        return jsonify({
            'error': 'No username provided'
        }), 400
        
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
