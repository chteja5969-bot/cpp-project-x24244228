
from feedback_sentiment_lib import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze("The service was excellent!")
print(f"Sentiment: {result.sentiment.value}")

