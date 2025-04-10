import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

# Ensure NLTK resources are downloaded
nltk.download('punkt')
nltk.download('stopwords')

# Stopwords with pronouns kept
stop_words = set(stopwords.words('english')) - {
    'i', 'you', 'we', 'he', 'she', 'they', 'me', 'my', 'your', 'our', 'his', 'her', 'their'
}

gloss_map = {
    "i": "ME", "you": "YOU", "we": "US", "he": "HE", "she": "SHE", "they": "THEY",
    "am": "", "is": "", "are": "",
    "going": "GO", "go": "GO", "want": "WANT", "have": "HAVE",
    "don't": "NOT", "not": "NOT",
    "store": "STORE", "because": "", "milk": "MILK", "to": ""
}

def convert_to_sign_gloss(text):
    words = word_tokenize(text.lower())
    words = [word for word in words if word not in string.punctuation]
    filtered = [word for word in words if word not in stop_words]
    gloss_sequence = [gloss_map.get(word, word.upper()) for word in filtered if gloss_map.get(word, word.upper())]
    gloss_string = " ".join(gloss_sequence)
    gloss_json = {"gloss_sequence": gloss_sequence}
    return gloss_string, gloss_json
