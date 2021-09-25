class Poll:
    def __init__(self, clipboardBot, 
                 pollEmbed, settingsEmbed, emojiList, 
                 optionList, isAnon = False):
        self.clipboardBot = clipboardBot
        self.pollEmbed = pollEmbed
        self.settingsEmbed = settingsEmbed
        self.emojiList = emojiList
        self.optionList = optionList
        self.isAnon = isAnon