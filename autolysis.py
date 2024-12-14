import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
import http.client
import json
import chardet

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "seaborn",
#   "pandas",
#   "matplotlib",
#   "numpy",
#   "scikit-learn",
#   "httpx",
#   "chardet",
#   "http.client",
# ]
# ///

def load_data(dataset_path):
    """Load the dataset with appropriate encoding."""
    with open(dataset_path, 'rb') as file:
        result = chardet.detect(file.read())
    encoding = result['encoding'] or 'ISO-8859-1'

    try:
        dataset = pd.read_csv(dataset_path, encoding=encoding)
    except UnicodeDecodeError:
        dataset = pd.read_csv(dataset_path, encoding='ISO-8859-1')

    return dataset

def preprocess_data(dataset):
    """Preprocess the dataset to handle missing values and outliers."""
    numeric_cols = dataset.select_dtypes(include=[np.number]).columns
    categorical_cols = dataset.select_dtypes(include=[object]).columns

    imputer_numeric = SimpleImputer(strategy="median")
    dataset[numeric_cols] = imputer_numeric.fit_transform(dataset[numeric_cols])

    imputer_categorical = SimpleImputer(strategy="most_frequent")
    dataset[categorical_cols] = imputer_categorical.fit_transform(dataset[categorical_cols])

    for col in numeric_cols:
        q1 = dataset[col].quantile(0.25)
        q3 = dataset[col].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        dataset[col] = np.clip(dataset[col], lower_bound, upper_bound)

    return dataset

def create_visualizations(dataset):
    """Create meaningful data visualizations."""
    numeric_data = dataset.select_dtypes(include=[np.number])

    # Distribution of key numeric columns (e.g., dynamically detect columns with significant variance)
    for col in numeric_data.columns:
        if numeric_data[col].std() > 0.5:  # Focus on columns with meaningful variance
            plt.figure(figsize=(8, 6))
            sns.histplot(numeric_data[col], kde=True, bins=20, color="skyblue")
            plt.title(f"Distribution of {col}")
            plt.savefig(f"distribution_{col}.png", dpi=150)
            plt.close()

    # Enhanced Correlation Heatmap for numeric data
    if len(numeric_data.columns) > 1:
        corr_matrix = numeric_data.corr()
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", 
                    linewidths=0.5, cbar_kws={"shrink": 0.8})
        plt.title("Full Correlation Matrix", fontsize=16)
        plt.tight_layout()
        plt.savefig("correlation_heatmap_full.png", dpi=150)
        plt.close()

        # Strong Correlations Heatmap
        strong_corr = corr_matrix[(corr_matrix >= 0.5) | (corr_matrix <= -0.5)]
        plt.figure(figsize=(10, 8))
        sns.heatmap(strong_corr, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Strong Correlations Heatmap")
        plt.savefig("strong_correlation_heatmap.png", dpi=150)
        plt.close()

    # PCA Visualization if sufficient numeric columns exist
    if len(numeric_data.columns) > 5:
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(numeric_data)
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x=pca_result[:, 0], y=pca_result[:, 1])
        plt.title("PCA Visualization")
        plt.savefig("pca_visualization.png", dpi=150)
        plt.close()

def generate_story(dataset):
    """Generate narrative for the analysis using GPT-4o-Mini."""
    prompt = f"""
    Dataset Overview:
    {dataset.describe(include='all').to_string()}

    Insights and Observations:
    - Highlight key patterns and actionable insights based on the data.
    """

    headers = {
        "Authorization": f"Bearer {os.environ['AIPROXY_TOKEN']}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }

    conn = http.client.HTTPSConnection("aiproxy.sanand.workers.dev")
    conn.request(
        "POST", "/openai/v1/chat/completions", 
        body=json.dumps(data), 
        headers=headers
    )

    response = conn.getresponse()
    if response.status == 200:
        response_data = response.read().decode("utf-8")
        story = json.loads(response_data)['choices'][0]['message']['content']

        with open("README.md", "w") as file:
            file.write(story)
    else:
        print(f"Error: {response.status}, {response.read().decode('utf-8')}")

    conn.close()

def main(file_path):
    dataset = load_data(file_path)
    if dataset is not None:
        dataset = preprocess_data(dataset)
        create_visualizations(dataset)
        generate_story(dataset)

if __name__ == "__main__":
    import sys
    main(sys.argv[1])
