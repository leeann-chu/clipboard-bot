import json

class PollClass:
    def __init__(self, ctx, pollEmbed, emojiList, optionList, isAnon = False, isLocked = False, newPoll = {}):
        self.ctx = ctx
        self.emojiList = emojiList
        self.optionList = optionList
        self.pollEmbed = pollEmbed
        self.isAnon = isAnon
        self.isLocked = isLocked
        self.newPoll = newPoll

class SettingsClass:
    def __init__(self, settingsEmbed, message, isAuthor):
        self.settingsEmbed = settingsEmbed
        self.message = message
        self.isAuthor = isAuthor

def writetoFile(data, file):
    with open(f'data/{file}.json', 'w') as f:
        json.dump(data, f,  indent=4)

def readfromFile(file):
    try:
        with open(f'data/{file}.json', 'r') as f:
            data = json.load(f)
        return data
    except:
        return None