import nltk
import re
from nltk import WordNetLemmatizer
nltk.download("stopwords")
nltk.download('punkt')
nltk.download('omw-1.4')
nltk.download('wordnet')
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class training:
    def __init__(self):
        self.lemma_ = WordNetLemmatizer()
        


    def clean_text(self, text):
        text = str(text)
        text = re.sub('[^a-zA-Z]', " ", text) #remove punctuations and numbers
        text = re.sub(r"\s+[a-zA-Z]\s+", ' ', text) # Single character removal
        text = re.sub(r'\s+', " ", text) #remove extra spaces
        text = text.replace("ain't", "am not").replace("aren't", "are not")
        text = ' '.join(tex.lower() for tex in text.split(' ')) # Lowering cases
        sw = nltk.corpus.stopwords.words('english')
        text = ' '.join(tex for tex in text.split() if tex not in sw) #removing stopwords
        text = ' '.join(self.lemma_.lemmatize(x) for x in text.split()) #lemmatization
        return text



    def sentiment_scores(self, sentence):
    
        # Create a SentimentIntensityAnalyzer object.
        sid_obj = SentimentIntensityAnalyzer()
    
        # polarity_scores method of SentimentIntensityAnalyzer
        # object gives a sentiment dictionary.
        # which contains pos, neg, neu, and compound scores.
        sentiment_dict = sid_obj.polarity_scores(sentence)
        
        # decide sentiment as positive, negative and neutral
        if sentiment_dict['compound'] >= 0.05 :
            sentiment = "Positive"
    
        elif sentiment_dict['compound'] <= - 0.05 :
            sentiment = "Negative"
    
        else :
            sentiment = "Neutral"
    
    
    
        return sentiment
 
