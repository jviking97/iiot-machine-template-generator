import sys
from sklearn import cluster as cl
from sklearn import metrics
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import hdbscan

from custom_functions.corr_df import *
from custom_functions.result_plot import *

def correlation_check(filename):
    dataset = pd.read_csv(filename)
    correlation_matrix = dataset.corr()
    return correlation_matrix

def birch_clustering(pca_subset):
    # Run Birch
    bi = cl.Birch(n_clusters=None).fit(pca_subset)

    labels = bi.labels_
    core_samples_mask = np.zeros_like(bi.labels_, dtype=bool)
    index = 0
    for label in bi.labels_: 
        if label != -1:
            core_samples_mask[index] = True
        index = index + 1

    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise_ = list(labels).count(-1)

    print("birch_clustering")
    print('Estimated number of clusters: %d' % n_clusters_)
    print('Estimated number of noise points: %d' % n_noise_)
    print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(pca_subset, labels))
    if pca_subset.shape[1] > 2:
        plot_result_3d(pca_subset, labels, core_samples_mask, n_clusters_)
    else:
        plot_result_with_noise_2d(pca_subset, labels, core_samples_mask, n_clusters_)

def k_means_clustering(pca_subset, num_of_max_cluster_iterations=2):
    # Run K-Means
    iterations = 2
    while iterations <= num_of_max_cluster_iterations:
        print("Iteration with %d cluster centers" % iterations)
        km = cl.KMeans(n_clusters=iterations, random_state=0).fit(pca_subset)
        labels = km.fit_predict(pca_subset)

        # Start of results
        core_samples_mask = np.zeros_like(km.labels_, dtype=bool)
        index = 0
        for label in km.labels_: 
            if label != -1:
                core_samples_mask[index] = True
            index = index + 1
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        
        print("k_means_clustering")
        print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(pca_subset, labels))
        if pca_subset.shape[1] > 2:
            plot_result_3d(pca_subset, labels, core_samples_mask, n_clusters_)
        else:
            plot_result_with_noise_2d(pca_subset, labels, core_samples_mask, n_clusters_)
        iterations = iterations + 1

def dbscan_clustering(pca_subset, max_distance, min_samples):
    # Run DBSCAN
    db = cl.DBSCAN(eps=max_distance, min_samples=min_samples).fit(pca_subset)

    labels = db.labels_
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True

    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise_ = list(labels).count(-1)
    print("dbscan_clustering")
    print('Estimated number of clusters: %d' % n_clusters_)
    print('Estimated number of noise points: %d' % n_noise_)
    print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(pca_subset, labels))
    
    if pca_subset.shape[1] > 2:
        plot_result_3d(pca_subset, labels, core_samples_mask, n_clusters_)
    else:
        plot_result_with_noise_2d(pca_subset, labels, core_samples_mask, n_clusters_)

def hdbscan_clustering(pca_subset, min_cluster_size, min_samples, cluster_selection_epsilon):
    hdb = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples, cluster_selection_epsilon=cluster_selection_epsilon).fit(pca_subset)

    labels = hdb.labels_
    core_samples_mask = np.zeros_like(hdb.labels_, dtype=bool)
    index = 0
    for label in hdb.labels_: 
        if label != -1:
            core_samples_mask[index] = True
        index = index + 1
        
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise_ = list(labels).count(-1)
    print("hdbscan_clustering")
    print('Estimated number of clusters: %d' % n_clusters_)
    print('Estimated number of noise points: %d' % n_noise_)
    print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(pca_subset, labels))
    print("Davies-Bouldin index: %0.3f" % metrics.davies_bouldin_score(pca_subset, labels))
    print("Calinski index: %0.3f" % metrics.calinski_harabasz_score(pca_subset, labels))

    if pca_subset.shape[1] > 2:
        plot_result_3d(pca_subset, labels, core_samples_mask, n_clusters_)
    elif pca_subset.shape[1] < 4:
        plot_result_with_noise_2d(pca_subset, labels, core_samples_mask, n_clusters_)
    else:
        print("Dimensions in dataset larger than 3 dim")

    return labels

def main():
    # filepath = "datasets/iot_telemetry_data.csv"
    # filepath = "datasets/C9.csv"
    filepath = "datasets/C8.csv"
    # filepath = "datasets/gas_sensor_array.csv"
    
    # Read selected dataset
    dt = pd.read_csv(filepath)

    # Only select computable values
    dataset = dt.select_dtypes("number")

    # Correlation check
    # print(correlation_check(filepath))

    # Reduce bigger datasets to smaller size
    if len(dataset.axes[0])>100000:
        # Select every tenth row
        small_subset = dataset.iloc[::10, :]
    else:
        small_subset = dataset

    # Select relevant columns of dataset with low correlation
    small_no_corr_subset = corr_df(small_subset, 0.7)

    # Transform data
    scaled_subset = StandardScaler().fit_transform(small_no_corr_subset)

    # Reduce dimension with PCA
    pca = PCA(n_components=0.75)
    pca_subset = pca.fit_transform(scaled_subset)
    print("%d componets in PCA" % pca.n_components_)
    print(pca.explained_variance_)
    print(pca.explained_variance_ratio_)
    
    sys.stdout = open('output-hdbscan-c9.txt','wt')

    # dbscan_clustering(pca_subset, 0.4, 8)
    label_list = hdbscan_clustering(pca_subset, 1000, 15, 0.4)
    # k_means_clustering(pca_subset, 5)
    # birch_clustering(pca_subset)

    # Concatenate list of labels to small subset, output new small csv file with labels
    labeled_dataset = small_subset.assign(Cluster = label_list)
    labeled_dataset.to_csv("labeled_dataset_c8.csv", index = False)

    plt.scatter(labeled_dataset["Time"], labeled_dataset["Cluster"])
    plt.title("Distribution of clusters against time")
    plt.xlabel("Time")
    plt.ylabel("Cluster label")
    plt.show()

if __name__ == '__main__':
    main()