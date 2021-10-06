import json

class PollClass:
    def __init__(self, ctx, clipboardBot, pollEmbed, emojiList, optionList, isAnon = False, isLocked = False, newPoll = {}):
        self.ctx = ctx
        self.clipboardBot = clipboardBot
        self.emojiList = emojiList
        self.optionList = optionList
        self.pollEmbed = pollEmbed
        self.isAnon = isAnon
        self.isLocked = isLocked
        self.newPoll = newPoll     
        
    # def refreshPoll(self):
    #     self.newPoll = readfromFile()
    #     return self.newPoll
        
class SettingsClass:
    def __init__(self, settingsEmbed, message, isAuthor):
        self.settingsEmbed = settingsEmbed
        self.message = message
        self.isAuthor = isAuthor
        
def writetoFile(newPoll):
    with open('data/storedPolls.json', 'w') as fp:
        json.dump(newPoll, fp,  indent=4)
def readfromFile():
    with open('data/storedPolls.json') as fp:
        newPoll = json.load(fp)
    return newPoll
        