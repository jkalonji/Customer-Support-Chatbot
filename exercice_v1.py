from FlagEmbedding import FlagReranker

# ESSAI 1 -> Les messages sont mal classifiés. J'essaie un autre modèle
#reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation

# You can map the scores into 0-1 by set "normalize=True", which will apply sigmoid function to the score
#scores = reranker.compute_score([['I want to return the article, it does not fit me and I hate it','Rage'],
#                                 ['I want to return the article, it does not fit me and I hate it','disapointment'],
#                                 ['I want to return the article, it does not fit me and I hate it','article']],normalize=True)
#print(scores) # [0.00027803096387751553, 0.9948403768236574]

# =====================

# ESSAI 2 ne permet pas de spécifier les catgories moi-même

#from transformers import pipeline

#classifier = pipeline(task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None)

#sentences = ["Hello, could you provide more details about the features of this product? I would like to know if it is available in multiple colors."]

#model_outputs = classifier(sentences)
#print(model_outputs[0])
# produces a list of dicts for each of the labels


# ESSAI 3 avec un modèle rapide (on fera le fine tuning à la fin)

from tenacity import retry, stop_after_attempt, wait_exponential

from FlagEmbedding import FlagReranker

def load_model():
    try:
        reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True) # Setting use_fp16 to True = ++speed --performance
    except Exception as e:
        if e.contains('memory') or e.contains('does not exist'):
            reranker = FlagReranker('BAAI/bge-reranker-base', use_fp16=False)
    return reranker

def check_user_message(message):
    print(message)
    if 'racist' in message:
        return False

    else:
        return True


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1.5, min=1, max=10))
def chatbot_response(message):

    reranker = load_model()

    tag_list = ['complaint','refund','query','inventory','satisfaction']
    scores = []
    for e in tag_list:
        score = reranker.compute_score([[e, message]], normalize=True)
        print(e, ' : ', score)
        scores.append([e, score])

    sorted_data = sorted(scores, key=lambda x: x[1][0])
    print(sorted_data)
    print(sorted_data[-1][0])

#message = 'Hello, I received an item that does not match my order. How can I proceed to return it'
message = 'iaeuyhsdgbqnsZKOZ22'
message = 'how much of the product do you still have in stock?'
chatbot_response(message)