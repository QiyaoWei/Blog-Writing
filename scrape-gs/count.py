import openreview
import pandas as pd
import arxiv

def get_openreview():
    # API V2
    client = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net',
        username='blablabla',
        password='blablabla'
    )

    #venues = client.get_group(id='venues').members
    #print([i for i in venues if "IPS" in i])

    # keywords = ["GAN", "VAE", "BERT", "GPT", "Meta Learning", "Capsule", "Shot Learning", "Siamese", "Triplet Loss", "Self Supervised Learning", "GNN", "Seq2Seq", "LSTM", "GRU", "R-CNN", "YOLO", "SSD", "Neural Style Transfer", "U-Net", "XLNet", "T5", "MobileNet", "EfficientNet", "ViT", "WaveNet", "DQN", "PG", "Actor-Critic", "Transformer-XL", "Longformer", "Electra", "Mixture of Experts"]


    conferences = ["ICML.cc/2024/Conference"]

    results = list()

    for conference in conferences:
        venues = client.get_group(conference)
        # print(venues.content.keys())
        # print(venues.content['submission_name'])
        submission_name = venues.content['submission_name']['value']
        # print(submission_name)
        submissions = client.get_all_notes(invitation=f'{conference}/-/{submission_name}')
        # print(len(submissions))
        # print(type(submissions))
        # print(submissions[0].keys())
        for submission in submissions:
            results.append(submission.content)
            # assert "venue" in submission.keys()
            # assert "poster" in submission.venue.value or "spotlight" in submission.venue.value or "oral" in submission.venue.value
            # for keyword in keywords:
            #     if keyword in submission.abstract.value:
            #         add_to_dict(results[conference], keyword, submission.id)
            
    results = pd.DataFrame(results)
    results.to_csv("results.csv", index=False)
    
def search_result_by_keyword():
    data = pd.read_csv("results.csv")
    write = ""
    for i in range(len(data)):
        if "role" in data["abstract"].iloc[i].lower() and "playing" in data["abstract"].iloc[i].lower():
            write += data["title"].iloc[i] + "\n"
    with open("write.txt", 'w') as f:
        f.write(write)
        
def search_result_on_arxiv():
    client = arxiv.Client()
    data = pd.read_csv("results.csv")
    result = {"title": [], "authors": []}
    for i in range(len(data)):
        title = eval(data["title"].iloc[i])["value"]
        search = arxiv.Search(query=title, max_results=100)
        try:
            results = client.results(search)
            for r in results:
                if r.title.lower() == title.lower():
                    print("success!")
                    result["title"].append(title)
                    result["authors"].append(r.authors)
                    break
        except:
            continue
        df = pd.DataFrame(result)
        df.to_csv("author.csv", index=False)
        
if __name__ == "__main__":
    get_openreview()
    # search_result_by_keyword()
    # search_result_on_arxiv()