from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer


def sentiment_analysis(text):
    score = SentimentIntensityAnalyzer().polarity_scores(text)
    return score


def get_polarity(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    return polarity


def get_general_sentiment(polarity):
    if polarity == 0:
        return "neutral"
    elif polarity < 0:
        return "negative"
    else:
        return "positive"




