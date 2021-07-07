import json
import boto3
import os
import re

s3 = boto3.resource('s3')
comprehend = boto3.client('comprehend')
firehose = boto3.client('firehose')

entity_should_be_filtered = re.compile('^[\d#@]+$')

def lambda_handler(event, context):
    print(event)

    for record in event['Records']:
        s3_bucket = record['s3']['bucket']['name']
        s3_key = record['s3']['object']['key']
        
        obj = s3.Object(s3_bucket, s3_key)
        tweets_as_string = obj.get()['Body'].read().decode('utf-8')
        
        # S3のファイルは改行コードで区切られている
        tweets = tweets_as_string.split('\n')
        for tweet_string in tweets:
            if len(tweet_string) < 1:
                continue
            
            tweet = json.loads(tweet_string)
            
            # 感情分析をComprehendに依頼
            sentiment_response = comprehend.detect_sentiment(
                Text=tweet['text'],
                LanguageCode=tweet['lang']
                )
            print(sentiment_response)
            
            sentiment_record = {
                'tweetid': tweet['id'],
                'text': tweet['text'],
                'sentiment': sentiment_response['Sentiment'],
                'sentimentposscore': sentiment_response['SentimentScore']['Positive'],
                'sentimentnegscore': sentiment_response['SentimentScore']['Negative'],
                'sentimentneuscore': sentiment_response['SentimentScore']['Neutral'],
                'sentimentmixedscore': sentiment_response['SentimentScore']['Mixed']
            }
            
            firehose.put_record(
                DeliveryStreamName=os.environ['SENTIMENT_STREAM'],
                Record={
                    'Data': json.dumps(sentiment_record) + '\n'
                }
            )
            
            # 人名、場所などの分析をComprehendに依頼
            entities_response = comprehend.detect_entities(
                Text=tweet['text'],
                LanguageCode=tweet['lang']
                )
            print(entities_response)
            
            seen_entities = []
            for entity in entities_response['Entities']:
                if (entity_should_be_filtered.match(entity['Text'])):
                    continue
                
                id = entity['Text'] + '-' + entity['Type']
                if (id in seen_entities) == False:
                    entity_record = {
                        'tweetid': tweet['id'],
                        'entity': entity['Text'],
                        'type': entity['Type'],
                        'score': entity['Score']
                    }
                    
                    firehose.put_record(
                        DeliveryStreamName=os.environ['ENTITY_STREAM'],
                        Record={
                            'Data': json.dumps(entity_record) + '\n'
                        }
                    )
                    seen_entities.append(id)

    return 'true'
    