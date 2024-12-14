import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import requests

import chardet

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "seaborn",
#   "pandas",
#   "matplotlib",
#   "numpy",
# ]
# ///

def load_data(dataset_path):
    # Detect the encoding of the file
    with open(dataset_path, 'rb') as file:
        result = chardet.detect(file.read())
    encoding = result['encoding'] or 'ISO-8859-1'  # Default to ISO-8859-1 if detection fails

    # Read the CSV file with the detected encoding
    try:
        dataset = pd.read_csv(dataset_path, encoding=encoding)
    except UnicodeDecodeError:
        # Fallback to a safe encoding
        dataset = pd.read_csv(dataset_path, encoding='ISO-8859-1')
    
    return dataset

def preprocess_data(dataset):
    """Preprocess data for generic handling."""
    # Identify numeric and categorical columns
    numeric_cols = dataset.select_dtypes(include=[np.number]).columns
    categorical_cols = dataset.select_dtypes(include=[object]).columns

    # Impute missing numeric values
    imputer_numeric = SimpleImputer(strategy="median")
    dataset[numeric_cols] = imputer_numeric.fit_transform(dataset[numeric_cols])

    # Impute missing categorical values
    imputer_categorical = SimpleImputer(strategy="most_frequent")
    dataset[categorical_cols] = imputer_categorical.fit_transform(dataset[categorical_cols])

    # Handle outliers: Cap extreme values in numeric columns
    for col in numeric_cols:
        q1 = dataset[col].quantile(0.25)
        q3 = dataset[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        dataset[col] = np.clip(dataset[col], lower_bound, upper_bound)

    # Encode categorical variables
    dataset = pd.get_dummies(dataset, drop_first=True)

    return dataset

def create_visualizations(dataset):
    """Generate enhanced data visualizations."""
    numeric_data = dataset.select_dtypes(include=[np.number])
    categorical_data = dataset.select_dtypes(include=['object'])

    # Correlation heatmap
    if len(numeric_data.columns) > 1:
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric_data.corr(), annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Heatmap")
        plt.savefig("correlation_heatmap.png")
        plt.close()

    # Histograms for numeric columns
    for col in numeric_data.columns:
        plt.figure(figsize=(8, 6))
        sns.histplot(dataset[col], kde=True, bins=20, color="skyblue")
        plt.title(f"Distribution of {col}")
        plt.savefig(f"distribution_{col}.png")
        plt.close()

    # Top counts for categorical variables
    for col in categorical_data.columns:
        top_categories = dataset[col].value_counts().head(10)
        plt.figure(figsize=(8, 6))
        sns.barplot(x=top_categories.index, y=top_categories.values, palette="viridis")
        plt.title(f"Top Categories in {col}")
        plt.xticks(rotation=45)
        plt.savefig(f"top_categories_{col}.png")
        plt.close()

    # PCA visualization if numeric data has many features
    if len(numeric_data.columns) > 2:
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(numeric_data)
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x=pca_result[:, 0], y=pca_result[:, 1], palette="coolwarm")
        plt.title("PCA Visualization")
        plt.savefig("pca_visualization.png")
        plt.close()

    # KMeans clustering plot (if applicable)
    if len(numeric_data.columns) > 2:
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(numeric_data)
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x=pca_result[:, 0], y=pca_result[:, 1], hue=clusters, palette="deep")
        plt.title("KMeans Clustering")
        plt.savefig("kmeans_clustering.png")
        plt.close()

def generate_story(dataset):
    """Generate narrative using GPT-4o-Mini via AI Proxy."""
    prompt = f"""
    Dataset Overview:
    {dataset.describe().to_string()}

    Insights and Observations:
    - Include trends, patterns, and recommendations.
    """

    headers = {
        "Authorization": f"Bearer {os.environ['AIPROXY_TOKEN']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(
        "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        story = response.json()['choices'][0]['message']['content']
        with open("README.md", "w") as file:
            file.write(story)
    else:
        print(f"Error: {response.status_code}, {response.text}")

def main(file_path):
    dataset = load_data(file_path)
    if dataset is not None:
        dataset = preprocess_data(dataset)
        create_visualizations(dataset)
        generate_story(dataset)

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
