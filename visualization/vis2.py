import time
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns

# https://builtin.com/data-science/tsne-python
# X = np.array([[0, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 1]])
# X_embedded = TSNE(n_components=2, learning_rate='auto', init='random', perplexity=3).fit_transform(X)

# Just to be clear, I think gpt2 has embedding size=768
from transformers import pipeline
from datasets import load_dataset
pipeline = pipeline('feature-extraction', model='lvwerra/gpt2-imdb')

ds = load_dataset("imdb", split="test")
ds = ds.rename_columns({"text": "review"})
ds = ds.filter(lambda x: len(x["review"]) > 200, batched=False)
# input_size = 5
# # input_size = LengthSampler(input_min_text_length, input_max_text_length)
# def tokenize(sample):
#     sample["input_ids"] = tokenizer.encode(sample["review"])[: input_size]
#     sample["response_ids"] = tokenizer.encode(sample["review"])[input_size :]
#     sample["query"] = tokenizer.decode(sample["input_ids"])
#     return sample
# ds = ds.map(tokenize, batched=False)
ds.set_format(type="torch")
print(len(ds)) # 25000
dataloader = torch.utils.data.DataLoader(ds, batch_size=1, shuffle=True)

all_embeddings = []
all_labels = []
for batch in dataloader:
    # print(len(batch["review"]))
    # temp = pipeline(batch["review"])
    # print(type(temp))
    # print(len(temp))
    # print(torch.tensor(pipeline(batch["review"])).shape) # (1, 4, 768
    all_embeddings.append(torch.flatten(torch.tensor(pipeline(batch["review"][0][:10]))).detach().to("cpu"))
    all_labels.append(batch["label"].detach().cpu().item())
    
for i in all_embeddings:
    print(i.shape)

max_emb_len=max([len(i) for i in all_embeddings])

all_embeddings = torch.stack([torch.cat([i, i.new_zeros(max_emb_len - len(i))], 0) for i in all_embeddings],0)
# all_embeddings = np.array(all_embeddings)
print(all_embeddings.shape) # (bs=10, seq_len * 768)

feat_cols = ['index'+str(i) for i in range(all_embeddings.shape[1])]
df = pd.DataFrame(all_embeddings,columns=feat_cols)
df['y'] = all_labels
df['label'] = df['y'].apply(lambda i: str(i))

print('Size of the dataframe: {}'.format(df.shape))
print(df)
# [out] Size of the dataframe: (bs=10, seq_len * 768)

pca = PCA(n_components=3)
pca_result = pca.fit_transform(df[feat_cols].values)

df['pca-one'] = pca_result[:,0]
df['pca-two'] = pca_result[:,1] 
df['pca-three'] = pca_result[:,2]

print('Explained variation per principal component: {}'.format(pca.explained_variance_ratio_))

mix = np.random.permutation(df.shape[0])
plt.figure(figsize=(16,10))
sns.scatterplot(
    x="pca-one", y="pca-two",
    hue="y",
    palette=sns.color_palette("hls", 10),
    data=df.loc[mix,:],
    legend="full",
    alpha=0.3
)
plt.savefig("2dpca.png")
ax = plt.figure(figsize=(16,10)).add_subplot(projection='3d')
ax.scatter(
    xs=df.loc[mix,:]["pca-one"], 
    ys=df.loc[mix,:]["pca-two"], 
    zs=df.loc[mix,:]["pca-three"], 
    c=df.loc[mix,:]["y"], 
    cmap='tab10'
)
ax.set_xlabel('pca-one')
ax.set_ylabel('pca-two')
ax.set_zlabel('pca-three')
plt.savefig("3dpca.png")








N = 10000

df_subset = df.loc[mix[:N],:].copy()

data_subset = df_subset[feat_cols].values

pca = PCA(n_components=3)
pca_result = pca.fit_transform(data_subset)

df_subset['pca-one'] = pca_result[:,0]
df_subset['pca-two'] = pca_result[:,1] 
df_subset['pca-three'] = pca_result[:,2]

print('Explained variation per principal component: {}'.format(pca.explained_variance_ratio_))

time_start = time.time()
tsne = TSNE(n_components=2, verbose=1, perplexity=3, n_iter=300)
tsne_results = tsne.fit_transform(data_subset)

print('t-SNE done! Time elapsed: {} seconds'.format(time.time()-time_start))

df_subset['tsne-2d-one'] = tsne_results[:,0]
df_subset['tsne-2d-two'] = tsne_results[:,1]

plt.figure(figsize=(16,10))
sns.scatterplot(
    x="tsne-2d-one", y="tsne-2d-two",
    hue="y",
    palette=sns.color_palette("hls", 10),
    data=df_subset,
    legend="full",
    alpha=0.3
)

plt.figure(figsize=(16,7))

ax1 = plt.subplot(1, 2, 1)
sns.scatterplot(
    x="pca-one", y="pca-two",
    hue="y",
    palette=sns.color_palette("hls", 10),
    data=df_subset,
    legend="full",
    alpha=0.3,
    ax=ax1
)

ax2 = plt.subplot(1, 2, 2)
sns.scatterplot(
    x="tsne-2d-one", y="tsne-2d-two",
    hue="y",
    palette=sns.color_palette("hls", 10),
    data=df_subset,
    legend="full",
    alpha=0.3,
    ax=ax2
)
plt.savefig("difference?.png")





pca_50 = PCA(n_components=3)
pca_result_50 = pca_50.fit_transform(data_subset)

print('Cumulative explained variation for 50 principal components: {}'.format(np.sum(pca_50.explained_variance_ratio_)))
time_start = time.time()

tsne = TSNE(n_components=2, verbose=0, perplexity=3, n_iter=300)
tsne_pca_results = tsne.fit_transform(pca_result_50)

print('t-SNE done! Time elapsed: {} seconds'.format(time.time()-time_start))

df_subset['tsne-pca50-one'] = tsne_pca_results[:,0]
df_subset['tsne-pca50-two'] = tsne_pca_results[:,1]
plt.figure(figsize=(16,4))
ax1 = plt.subplot(1, 3, 1)
sns.scatterplot(
    x="pca-one", y="pca-two",
    hue="y",
    palette=sns.color_palette("hls", 10),
    data=df_subset,
    legend="full",
    alpha=0.3,
    ax=ax1
)

ax2 = plt.subplot(1, 3, 2)
sns.scatterplot(
    x="tsne-2d-one", y="tsne-2d-two",
    hue="y",
    palette=sns.color_palette("hls", 10),
    data=df_subset,
    legend="full",
    alpha=0.3,
    ax=ax2
)

ax3 = plt.subplot(1, 3, 3)
sns.scatterplot(
    x="tsne-pca50-one", y="tsne-pca50-two",
    hue="y",
    palette=sns.color_palette("hls", 10),
    data=df_subset,
    legend="full",
    alpha=0.3,
    ax=ax3
)
plt.savefig("diff2.png")