#!/usr/bin/env python

from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelEncoder
from nltk import sent_tokenize, pos_tag, wordpunct_tokenize
from nltk.corpus import wordnet as wn
import string
from nltk import WordNetLemmatizer
import nltk

class Preprocessor(BaseEstimator, TransformerMixin):
    def __init__(self, stopwords = None, punc = None, lower = True, strip = True):
        self.lower = lower
        self.strip = strip
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        self.punct = set(string.punctuation)
        self.lemmatizer = WordNetLemmatizer()

    def get_all_words(self, X):
        return [' '.join(self.tokenize(doc) for doc in X)
        ]

    def transform(self, X):
        return[
            list(self.tokenize(doc)) for doc in X
        ]
    def tokenize(self, document):
        document = document.encode('ascii', errors = 'replace')
        #document = ''.join([ch.lower() for ch in text if ch not in string.punctuation])
        for sent in sent_tokenize(document):
            # Break the sentence into part of speech tagged tokens
            for token, tag in pos_tag(wordpunct_tokenize(sent)):
                token = token.lower() if self.lower else token
                token = token.strip() if self.strip else token
                token = token.strip('_') if self.strip else token
                token = token.strip('*') if self.strip else token
                if token in self.stopwords:
                    continue
                if all(char in self.punct for char in token):
                    continue
                lemma = self.lemmatize(token, tag)
                yield lemma

    def lemmatize(self, token, tag):
        tag = {
            'N': wn.NOUN,
            'V': wn.VERB,
            'R': wn.ADV,
            'J': wn.ADJ
        }.get(tag[0], wn.NOUN)
        return self.lemmatizer.lemmatize(token, tag)
