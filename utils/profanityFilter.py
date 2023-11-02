from fuzzywuzzy import fuzz

offensive_hindi_words = [
		"bahenchod", "behenchod", "bhenchod", "bhenchodd", "b.c.", "bc", "bakchod", "bakchodd", 
		"bakchodi", "bevda", "bewda", "bevdey", "bewday", "bevakoof", "bevkoof", "bevkuf", "bewakoof", 
		"bewkoof", "bewkuf", "bhadua", "bhaduaa", "bhadva", "bhadvaa", "bhadwa", "bhadwaa", "bhosada", 
		"bhosda", "bhosdaa", "bhosdike", "bhonsdike", "bhosdiki", "bhosdiwala", "bhosdiwale", 
		"bhosadchodal", "bhosadchod", "bhosadchodal", "bhosadchod", "babbe", "babbey", "bube", "bubey", 
		"bur", "burr", "buurr", "buur", "charsi", "chooche", "choochi", "chuchi", "chhod", "chod", "chodd", 
		"chudne", "chudney", "chudwa", "chudwaa", "chudwane", "chudwaane", "chaat", "choot", "chut", 
		"chute", "chutia", "chutiya", "chutiye", "dalaal", "dalal", "dalle", "dalley", "fattu", "gadha", 
		"gadhe", "gadhalund", "gaand", "gand", "gandu", "gandfat", "gandfut", "gandiya", "gandiye", 
		"gote", "gotey", "gotte", "hag", "haggu", "hagne", "hagney", "harami", "haramjada", 
		"haraamjaada", "haramzyada", "haraamzyaada", "haraamjaade", "haraamzaade", "haraamkhor", "haramkhor", 
		"jhat", "jhaat", "jhaatu", "jhatu", "kutta", "kutte", "kuttey", "kutia", "kutiya", "kuttiya", 
		"kutti", "landi", "landy", "laude", "laudey", "laura", "lora", "lauda", "ling", "loda", "lode", 
		"lund", "launda", "lounde", "laundey", "laundi", "loundi", "laundiya", "loundiya", "lulli", 
		"maar", "maro", "marunga", "madarchod", "madarchodd", "madarchood", "madarchoot", "madarchut", "mamme", "mammey", "moot", "mut", "mootne", "mutne", "mooth", "muth", "nunni", 
		"nunnu", "paaji", "paji", "pesaab", "pesab", "peshaab", "peshab", "pilla", "pillay", "pille", 
		"pilley", "pisaab", "pisab", "pkmkb", "porkistan", "raand", "rand", "randi", "randy", "suar", 
		"tatte", "tatti", "tatty", "ullu", "chewtiya",

		"dengu", "lanja", "pooka", "modda", "gudda", "ne amma pukkulo naa modda", "Guddha naku", "Bosudi", "erripooka", "pichipook", "ne akka", "yedava", "dunnapotu", "addagadidha", "donga naa kodaka",
		"lauda"
	]

async def containsHindiOffensiveWord(text):

	for offensiveWord in offensive_hindi_words:
		for word in text.lower().split():
			if fuzz.ratio(offensiveWord, word) > 65:  # Adjust the similarity threshold as needed
				print(fuzz.ratio(offensiveWord, word), word, offensiveWord)
				return True
	return False