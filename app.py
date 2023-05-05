from flask import Flask, jsonify, request,session
import requests, os, uuid, json
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.utils import secure_filename
import os
from translate import recognize

os.environ["SPEECH_KEY"] = "4af8779daf30476bbeb2b01f810e8fa7"
os.environ["SPEECH_REGION"] = "centralindia"

ALLOWED_EXTENSIONS = set(['wav'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize Flask app
app = Flask(__name__)
# basedir = os.path.abspath(os.path.dirname(__file__))

# Set up SQLAlchemy and Marshmallow
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

ma = Marshmallow(app)

# Card model
class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    filePath = db.Column(db.String(200))
    languages = db.Column(db.String(100))
    translations = db.relationship('CardTranslation', backref='card', lazy=True)

    def __init__(self, type, title, description, filePath, languages):
        self.type = type
        self.title = title
        self.description = description
        self.filePath = filePath
        self.languages = languages

# Card translation model
class CardTranslation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cardId = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    title_translation = db.Column(db.String(100))
    description_translation = db.Column(db.String(500))
    audio_translation = db.Column(db.String(200))
    language_id = db.Column(db.Integer, db.ForeignKey('language.id'), nullable=False)
    language = db.relationship('Language', backref='card_translation', uselist=False)

    def __init__(self, cardId, title_translation, description_translation, audio_translation,language_id):
        self.cardId = cardId
        self.title_translation = title_translation
        self.description_translation = description_translation
        self.audio_translation = audio_translation
        self.language_id = language_id

class Language(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    languageId = db.Column(db.String(50), unique=True, nullable=False)
    languageName = db.Column(db.String(50), nullable=False)

    def __init__(self, languageId, languageName):
        self.languageId = languageId
        self.languageName = languageName


# Card schema
class CardSchema(ma.Schema):
    class Meta:
        fields = ('id', 'type', 'title', 'description', 'filePath', 'languages', 'translations')

# Card translation schema
class CardTranslationSchema(ma.Schema):
    class Meta:
        fields = ('id', 'cardId', 'title_translation', 'description_translation', 'audio_translation','language_id')

# Language schema
class LanguageSchema(ma.Schema):
    class Meta:
        fields = ('id', 'languageId', 'languageName')


card_schema = CardSchema()
cards_schema = CardSchema(many=True)
card_translation_schema = CardTranslationSchema()
card_translations_schema = CardTranslationSchema(many=True)
language_schema = LanguageSchema()
languages_schema = LanguageSchema(many=True)

# run only the 1st time
with app.app_context():
    db.create_all()

# Create a card
@app.route('/cards', methods=['POST'])
def add_card():
    type = request.json['type']
    title = request.json['title']
    description = request.json['description']
    filePath = request.json['filePath']
    languages = request.json['languages']
    
    new_card = Card(type, title, description, filePath, languages)

    # if(languages.len()>0):
    #     translator(new_card)

    db.session.add(new_card)
    db.session.commit()

    return card_schema.jsonify(new_card)

# Get all cards
@app.route('/cards', methods=['GET'])
def get_cards():
    all_cards = Card.query.all()
    result = cards_schema.dump(all_cards)

    return jsonify(result)

# Get a single card
@app.route('/cards/<id>', methods=['GET'])
def get_card(id):
    card = Card.query.get(id)

    return card_schema.jsonify(card)

# Update a card
@app.route('/cards/<id>', methods=['PUT'])
def update_card(id):
    card = Card.query.get(id)

    type = request.json['type']
    title = request.json['title']
    description = request.json['description']
    filePath = request.json['filePath']
    languages = request.json['languages']

    card.type = type
    card.title = title
    card.description = description
    card.filePath = filePath
    card.languages = languages

    db.session.commit()

    return card_schema.jsonify(card)

# Delete a card
@app.route('/cards/<id>', methods=['DELETE'])
def delete_card(id):
    card = Card.query.get(id)

    db.session.delete(card)
    db.session.commit()

    return card_schema.jsonify(card)

# Create a card translation
@app.route('/cardTranslations', methods=['POST'])
def add_card_translation():
    cardId = request.json['cardId']
    title_translation = request.json['title_translation']
    description_translation = request.json['description_translation']
    audio_translation = request.json['audio_translation']
    language_id = request.json['language_id']

    new_card_translation = CardTranslation(cardId, title_translation, description_translation, audio_translation,language_id)

    db.session.add(new_card_translation)
    db.session.commit()

    return card_translation_schema.jsonify(new_card_translation)

# Get all card translations
@app.route('/cardTranslations', methods=['GET'])
def get_card_translations():
    all_card_translations = CardTranslation.query.all()
    result = card_translations_schema.dump(all_card_translations)

    return jsonify(result)

# Get card translations for a specific card
@app.route('/cardTranslations/<cardId>', methods=['GET'])
def get_card_translations_for_card(cardId):
    card_translations = CardTranslation.query.filter_by(cardId=cardId).all()

    return card_translations_schema.jsonify(card_translations)

# Update a card translation
@app.route('/cardTranslations/<id>', methods=['PUT'])
def update_card_translation(id):
    card_translation = CardTranslation.query.get(id)

    cardId = request.json['cardId']
    title_translation = request.json['title_translation']
    description_translation = request.json['description_translation']
    audio_translation = request.json['audio_translation']
    language_id = request.json['language_id']

    card_translation.cardId = cardId
    card_translation.title_translation = title_translation
    card_translation.description_translation = description_translation
    card_translation.audio_translation = audio_translation
    card_translation.language_id = language_id

    db.session.commit()

    return card_translation_schema.jsonify(card_translation)

# Delete a card translation
@app.route('/cardTranslations/<id>', methods=['DELETE'])
def delete_card_translation(id):
    card_translation = CardTranslation.query.get(id)

    db.session.delete(card_translation)
    db.session.commit()

    return card_translation_schema.jsonify(card_translation)

# Get a card with its card translations
@app.route('/cards/<id>/translations', methods=['GET'])
def get_card_with_translations(id):
    card = Card.query.get(id)
    card_translations = card.card_translations

    result = {
        'id': card.id,
        'type': card.type,
        'title': card.title,
        'description': card.description,
        'filePath': card.filePath,
        'languages': card.languages,
        'translations': [{
            'id': ct.id,
            'title_translation': ct.title_translation,
            'description_translation': ct.description_translation,
            'audio_translation': ct.audio_translation,
            'language_id':ct.language_id
        } for ct in card_translations]
    }

    return jsonify(result)


# Create a language
@app.route('/languages', methods=['POST'])
def add_language():
    languageId = request.json['languageId']
    languageName = request.json['languageName']

    new_language = Language(languageId, languageName)

    db.session.add(new_language)
    db.session.commit()

    return language_schema.jsonify(new_language)

# Get all languages
@app.route('/languages', methods=['GET'])
def get_languages():
    all_languages = Language.query.all()
    result = languages_schema.dump(all_languages)

    return jsonify(result)

# Get a language by id
@app.route('/languages/<id>', methods=['GET'])
def get_language(id):
    language = Language.query.get(id)

    return language_schema.jsonify(language)

# Update a language
@app.route('/languages/<id>', methods=['PUT'])
def update_language(id):
    language = Language.query.get(id)

    languageId = request.json['languageId']
    languageName = request.json['languageName']

    language.languageId = languageId
    language.languageName = languageName

    db.session.commit()

    return language_schema.jsonify(language)

# Delete a language
@app.route('/languages/<id>', methods=['DELETE'])
def delete_language(id):
    language = Language.query.get(id)

    db.session.delete(language)
    db.session.commit()

    return language_schema.jsonify(language)

@app.route('/media/upload',methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400

    file = request.files['file']

    # if user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if file and allowed_file(file.filename):
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return jsonify({'file_path': filepath}), 200
    else:
        return jsonify({'error': 'Failed to upload file.'}), 500

# def getLanguage(languages):
#     language_list = languages.split(",")
#     return language_list

# def translator(card:Card):
#     lang_list = getLanguage(card.languages)
#     type = card.type
#     id = card.id
#     if(type=="text"):
#         pass

# def language_text_translation(lang_list,card:Card):
#     key = os.environ['KEY']
#     endpoint = os.environ['ENDPOINT']
#     location = os.environ['LOCATION']
#     path = '/translate?api-version=3.0'
#     target_language_parameter = '&to=' + card.languages
#     constructed_url = endpoint + path + target_language_parameter

#     headers = {
#         'Ocp-Apim-Subscription-Key': key,
#         'Ocp-Apim-Subscription-Region': location,
#         'Content-type': 'application/json',
#         'X-ClientTraceId': str(uuid.uuid4())
#     }

#     original_title = card.title
#     original_desc = card.description

#     body = [{ 'text': original_title }]

#     # Make the call using post
#     translator_request = requests.post(constructed_url, headers=headers, json=body)
#     # Retrieve the JSON response
#     translator_response = translator_request.json()
#     # Retrieve the translation
#     translated_text = translator_response[0]['translations'][0]['text']

#     for i in lang_list:
#         original_title = card.title
#         original_desc = card.description

# Run the server
if __name__ == '__main__':
    app.run(debug=True)

