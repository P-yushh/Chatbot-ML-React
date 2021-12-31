import random
import json
import torch
import torch.nn as nn
from nltk_utils import tokenize, bag_of_words
from model import BotModel

class talk_my_bot(object):
    model = None
    weight = None
    intentions = None
    word_dict = None
    def initialize_hyperparams(bot, param_file):
        with open(param_file, 'r') as f:
            params = json.load(f)
        bot.HIDDEN_DIM = params["NeuronsInHiddenLayer"]
        bot.N_LAYERS = params["DepthOfModel"]
        bot.weight = torch.load(params["SavedWeights"])
        bot.OUTPUT_DIM = bot.weight["Output Dim"]
        bot.INPUT_DIM = bot.weight["Input Dim"]
        bot.word_dict = bot.weight["Word Dictionary"]
        bot.tags = bot.weight["Tags"]

    def load_model(bot):
        if bot.model==None:
            bot.model = BotModel(bot.INPUT_DIM, bot.HIDDEN_DIM, bot.OUTPUT_DIM, bot.N_LAYERS)
            bot.model.load_state_dict(bot.weight["model_state"])
        return bot.model

    def prepare_to_chat(bot, user_id, dataset, param_file):
        with open(dataset, 'r') as f:
            train_file = json.load(f)
        bot.intentions = train_file[user_id]
        bot.initialize_hyperparams(param_file)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        bot.model = bot.load_model().to(device)
        bot.model.eval()

    def chat(bot, text):
        default_answer = ["I apologize, I don't understand your request.",
                    "I'm sorry my AI does not recognize that request.",
                    "I don't understand.",
                    "Please try your request again.",
                    "Pardon?",
                    "That's new for me.",
                    "I'm sorry but I'm still learning."]
        x = tokenize(text)
        # print(bot.word_dict)
        x = bag_of_words(x, bot.word_dict)
        x = x.reshape(1, x.shape[0])
        x = torch.from_numpy(x)

        output = bot.model(x)
        _, idx = torch.max(output, dim=1)
        tag = bot.tags[idx.item()]

        prob = torch.softmax(output, dim=1)
        prob = prob[0][idx.item()]
        if prob>0.77:
            for intent in bot.intentions:
                if tag==intent["tag"]:
                    return random.choice(intent["responses"])
        else:
            return random.choice(default_answer)
