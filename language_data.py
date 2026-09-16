
# Broad multilingual language registry. Voice/TTS availability varies by provider.
LANGUAGES = [
("English","en"),("Urdu","ur"),("Arabic","ar"),("Persian (Farsi)","fa"),
("Spanish","es"),("French","fr"),("German","de"),("Italian","it"),("Portuguese","pt"),
("Russian","ru"),("Ukrainian","uk"),("Polish","pl"),("Dutch","nl"),("Greek","el"),
("Turkish","tr"),("Hebrew","he"),("Hindi","hi"),("Bengali","bn"),("Punjabi","pa"),
("Gujarati","gu"),("Marathi","mr"),("Tamil","ta"),("Telugu","te"),("Kannada","kn"),
("Malayalam","ml"),("Nepali","ne"),("Sinhala","si"),("Pashto","ps"),("Sindhi","sd"),
("Kashmiri","ks"),("Balochi","bal"),("Chinese (Mandarin)","zh"),("Cantonese","yue"),
("Japanese","ja"),("Korean","ko"),("Vietnamese","vi"),("Thai","th"),("Indonesian","id"),
("Malay","ms"),("Filipino","fil"),("Burmese","my"),("Khmer","km"),("Lao","lo"),
("Mongolian","mn"),("Kazakh","kk"),("Uzbek","uz"),("Turkmen","tk"),("Kyrgyz","ky"),
("Tajik","tg"),("Azerbaijani","az"),("Armenian","hy"),("Georgian","ka"),
("Romanian","ro"),("Hungarian","hu"),("Czech","cs"),("Slovak","sk"),("Bulgarian","bg"),
("Serbian","sr"),("Croatian","hr"),("Bosnian","bs"),("Slovenian","sl"),
("Albanian","sq"),("Macedonian","mk"),("Lithuanian","lt"),("Latvian","lv"),
("Estonian","et"),("Finnish","fi"),("Swedish","sv"),("Norwegian","no"),("Danish","da"),
("Icelandic","is"),("Irish","ga"),("Welsh","cy"),("Scottish Gaelic","gd"),
("Afrikaans","af"),("Swahili","sw"),("Zulu","zu"),("Xhosa","xh"),("Amharic","am"),
("Somali","so"),("Hausa","ha"),("Yoruba","yo"),("Igbo","ig"),("Malagasy","mg"),
("Kinyarwanda","rw"),("Luganda","lg"),("Sesotho","st"),("Setswana","tn"),
("Shona","sn"),("Arabic (Egyptian)","arz"),("Arabic (Gulf)","afb"),
("Latin","la"),("Esperanto","eo"),("Basque","eu"),("Catalan","ca"),("Galician","gl"),
("Frisian","fy"),("Maltese","mt"),("Luxembourgish","lb"),("Breton","br"),
("Corsican","co"),("Hawaiian","haw"),("Māori","mi"),("Samoan","sm"),("Tongan","to"),
("Fijian","fj"),("Javanese","jv"),("Sundanese","su"),("Balinese","ban"),
("Tagalog","tl"),("Aramaic","arc"),("Yiddish","yi"),("Albanian","sq"),
("Quechua","qu"),("Guarani","gn"),("Nahuatl","nah"),("Aymara","ay"),
("Greenlandic","kl"),("Faroese","fo"),("Tatar","tt"),("Bashkir","ba"),
("Chechen","ce"),("Ossetian","os"),("Uyghur","ug"),("Tibetan","bo"),
("Dzongkha","dz"),("Sanskrit","sa"),("Pali","pi"),("Bhojpuri","bho"),
("Maithili","mai"),("Assamese","as"),("Odia","or"),("Konkani","kok"),
("Kurdish (Kurmanji)","ku"),("Kurdish (Sorani)","ckb"),("Dari","prs"),
("Dhivehi","dv"),("Tigrinya","ti"),("Wolof","wo"),("Akan","ak"),
("Fula","ff"),("Lingala","ln"),("Tsonga","ts"),("Venda","ve")
]

def language_options():
    return [f"{name} ({code})" for name, code in LANGUAGES]
