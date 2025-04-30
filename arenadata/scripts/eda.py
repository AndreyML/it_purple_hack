import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score, average_precision_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier
import joblib  # Correct import for saving the model

tqdm.pandas()

# Constants
FOLDER_PATH = '/Users/andrey/Desktop/MisisProjects/tasks-public/Arenadata/scripts'
FILE_PATH = 'final_df_2.csv'

# Load data
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

# Initial data inspection
def initial_inspection(df):
    print("First few rows of the dataset:")
    print(df.head())
    print("\nDataset information:")
    print(df.info())
    print("\nMissing values in each column:")
    print(df.isnull().sum())
    print("\nNumber of duplicate rows:")
    print(df.duplicated().sum())

# Analyze time data
def analyze_time_data(df):
    df['StartSession'] = pd.to_datetime(df['StartSession'], errors='coerce')
    df['EndSession'] = pd.to_datetime(df['EndSession'], errors='coerce')
    df['SessionDuration'] = (df['EndSession'] - df['StartSession']).dt.total_seconds()
    print("\nSession Duration Statistics:")
    print(df['SessionDuration'].describe())

    plt.figure(figsize=(10, 6))
    sns.histplot(df['SessionDuration'], bins=50, kde=True)
    plt.title('Distribution of Session Duration')
    plt.xlabel('Duration (seconds)')
    plt.ylabel('Frequency')
    plt.show()

# Analyze traffic distribution
def analyze_traffic_distribution(df):
    plt.figure(figsize=(10, 6))
    sns.histplot(df['UpTx'], bins=50, kde=True, color='blue', label='UpTx')
    sns.histplot(df['DownTx'], bins=50, kde=True, color='red', label='DownTx')
    plt.title('Distribution of Traffic')
    plt.xlabel('Traffic (bits)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.show()

# Detect anomalies per client
def detect_anomalies_per_client(df):
    clients = df['IdClient'].unique()
    anomalies = []

    for client in tqdm(clients):
        client_data = df[df['IdClient'] == client]
        up_tx_mean = client_data['UpTx'].mean()
        up_tx_std = client_data['UpTx'].std()
        down_tx_mean = client_data['DownTx'].mean()
        down_tx_std = client_data['DownTx'].std()

        # Define thresholds for anomalies
        up_tx_threshold = up_tx_mean + 3 * up_tx_std
        down_tx_threshold = down_tx_mean + 3 * down_tx_std

        # Find anomalies
        up_tx_anomalies = client_data[client_data['UpTx'] > up_tx_threshold]
        down_tx_anomalies = client_data[client_data['DownTx'] > down_tx_threshold]

        if not up_tx_anomalies.empty or not down_tx_anomalies.empty:
            anomalies.append((client, up_tx_anomalies, down_tx_anomalies))

    return anomalies

# Visualize anomalies
def visualize_anomalies(anomalies):
    for client, up_anomalies, down_anomalies in anomalies:
        print(f"\nClient ID: {client}")
        if not up_anomalies.empty:
            print("UpTx Anomalies:")
            print(up_anomalies[['StartSession', 'EndSession', 'UpTx']])
        if not down_anomalies.empty:
            print("DownTx Anomalies:")
            print(down_anomalies[['StartSession', 'EndSession', 'DownTx']])

# Plot traffic per client
def plot_traffic_per_client(df):
    clients = df['IdClient'].unique()
    for client in tqdm(clients[:5]):
        client_data = df[df['IdClient'] == client]
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=client_data[['UpTx', 'DownTx']])
        plt.title(f'Traffic Distribution for Client {client}')
        plt.show()

# Plot scatter traffic
def plot_scatter_traffic(df):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='UpTx', y='DownTx', data=df, alpha=0.5)
    plt.title('Scatter Plot of UpTx vs DownTx')
    plt.xlabel('UpTx (bits)')
    plt.ylabel('DownTx (bits)')
    plt.show()

# Plot correlation heatmap
def plot_correlation_heatmap(df):
    numeric_df = df.select_dtypes(include=[np.number])
    plt.figure(figsize=(12, 8))
    sns.heatmap(numeric_df.corr(), annot=True, fmt=".2f", cmap='coolwarm')
    plt.title('Correlation Matrix')
    plt.show()

# Plot time series duration
def plot_time_series_duration(df):
    df['StartSession'] = pd.to_datetime(df['StartSession'], errors='coerce')
    df = df.sort_values('StartSession')
    plt.figure(figsize=(14, 6))
    plt.plot(df['StartSession'], df['SessionDuration'], alpha=0.5)
    plt.title('Time Series of Session Duration')
    plt.xlabel('Time')
    plt.ylabel('Session Duration (seconds)')
    plt.show()

# Plot pairplot
def plot_pairplot(df):
    sns.pairplot(df[['UpTx', 'DownTx', 'SessionDuration']])
    plt.suptitle('Pairplot of Traffic and Session Duration', y=1.02)
    plt.show()

# Plot violin traffic
def plot_violin_traffic(df):
    plt.figure(figsize=(12, 6))
    sns.violinplot(data=df[['UpTx', 'DownTx']])
    plt.title('Violin Plot of Traffic')
    plt.show()

# Plot histogram duration per client
def plot_histogram_duration_per_client(df):
    df['SessionDuration'] = pd.to_numeric(df['SessionDuration'], errors='coerce')
    clients = df['IdClient'].unique()
    for client in tqdm(clients[:5]):
        client_data = df[df['IdClient'] == client]
        if client_data['SessionDuration'].dropna().empty:
            continue
        plt.figure(figsize=(10, 6))
        sns.histplot(client_data['SessionDuration'].dropna(), bins=30, kde=True)
        plt.title(f'Session Duration Distribution for Client {client}')
        plt.xlabel('Duration (seconds)')
        plt.ylabel('Frequency')
        plt.show()

# Group and aggregate data
def group_and_aggregate(df):
    grouped = df.groupby('IdClient').agg({
        'UpTx': list,
        'DownTx': list,
        'Duartion': list,
        'StartSession': list,
        'EndSession': list
    }).reset_index()
    return grouped

# Calculate aggregates
def calculate_aggregates(df):
    aggregates = df.groupby('IdClient').agg({
        'UpTx': ['sum', 'mean', 'max', 'min', 'std'],
        'DownTx': ['sum', 'mean', 'max', 'min', 'std'],
        'Duartion': ['sum', 'mean', 'max', 'min', 'std'],
        'IdSession': 'count'
    })
    
    # Add additional features
    aggregates['ratio_updown_mean'] = aggregates[('UpTx', 'mean')] / aggregates[('DownTx', 'mean')]
    aggregates['ratio_updown_sum'] = aggregates[('UpTx', 'sum')] / aggregates[('DownTx', 'sum')]
    aggregates['cv_uptx'] = aggregates[('UpTx', 'std')] / aggregates[('UpTx', 'mean')]
    aggregates['cv_downtx'] = aggregates[('DownTx', 'std')] / aggregates[('DownTx', 'mean')]
    aggregates['cv_duration'] = aggregates[('Duartion', 'std')] / aggregates[('Duartion', 'mean')]
    aggregates['max_mean_ratio_uptx'] = aggregates[('UpTx', 'max')] / aggregates[('UpTx', 'mean')]
    aggregates['max_mean_ratio_downtx'] = aggregates[('DownTx', 'max')] / aggregates[('DownTx', 'mean')]
    aggregates['max_mean_ratio_duration'] = aggregates[('Duartion', 'max')] / aggregates[('Duartion', 'mean')]
    aggregates['skewness_uptx'] = (aggregates[('UpTx', 'mean')] - aggregates[('UpTx', 'min')]) / aggregates[('UpTx', 'std')]
    aggregates['skewness_downtx'] = (aggregates[('DownTx', 'mean')] - aggregates[('DownTx', 'min')]) / aggregates[('DownTx', 'std')]
    aggregates['bytes_per_second'] = aggregates[('UpTx', 'sum')] / aggregates[('Duartion', 'sum')]
    aggregates['download_per_second'] = aggregates[('DownTx', 'sum')] / aggregates[('Duartion', 'sum')]
    aggregates['session_intensity'] = aggregates[('IdSession', 'count')] / aggregates[('Duartion', 'sum')]
    aggregates['lag_uptx_mean'] = aggregates[('UpTx', 'mean')].shift(1)
    aggregates['lag_downtx_mean'] = aggregates[('DownTx', 'mean')].shift(1)
    aggregates['lag_duration_mean'] = aggregates[('Duartion', 'mean')].shift(1)

    aggregates = aggregates.reset_index()
    aggregates.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in aggregates.columns.values]
    aggregates.rename(columns={'IdClient_': 'IdClient'}, inplace=True)
    
    aggregates = aggregates.replace([np.inf, -np.inf], np.nan)
    aggregates = aggregates.fillna(-1)
    
    return aggregates

# Analyze client data
def analyze_client_data(grouped_df):
    for index, row in tqdm(grouped_df.iterrows()):
        if index == 5:
            break
        client_id = row['IdClient']
        up_tx = row['UpTx']
        down_tx = row['DownTx']
        session_duration = row['SessionDuration']
        start_session = row['StartSession']
        end_session = row['EndSession']
        
        # Plotting
        plt.figure(figsize=(12, 6))
        sns.histplot(up_tx, bins=30, kde=True, color='blue')
        plt.title(f'UpTx Distribution for Client {client_id}')
        plt.xlabel('UpTx (bits)')
        plt.ylabel('Frequency')
        plt.show()
        
        plt.figure(figsize=(12, 6))
        sns.histplot(down_tx, bins=30, kde=True, color='red')
        plt.title(f'DownTx Distribution for Client {client_id}')
        plt.xlabel('DownTx (bits)')
        plt.ylabel('Frequency')
        plt.show()
        
        plt.figure(figsize=(12, 6))
        sns.histplot(session_duration, bins=30, kde=True, color='green')
        plt.title(f'Session Duration Distribution for Client {client_id}')
        plt.xlabel('Duration (seconds)')
        plt.ylabel('Frequency')
        plt.show()
        
        plt.figure(figsize=(12, 6))
        plt.plot(start_session, up_tx, label='UpTx', color='blue')
        plt.plot(start_session, down_tx, label='DownTx', color='red')
        plt.title(f'Traffic Over Time for Client {client_id}')
        plt.xlabel('Time')
        plt.ylabel('Traffic (bits)')
        plt.legend()
        plt.show()
        
        plt.figure(figsize=(12, 6))
        sns.boxplot(data=[up_tx, down_tx], palette='pastel')
        plt.title(f'Traffic Boxplot for Client {client_id}')
        plt.xticks([0, 1], ['UpTx', 'DownTx'])
        plt.ylabel('Traffic (bits)')
        plt.show()
        
        plt.figure(figsize=(12, 6))
        sns.violinplot(data=[up_tx, down_tx], palette='muted')
        plt.title(f'Traffic Violin Plot for Client {client_id}')
        plt.xticks([0, 1], ['UpTx', 'DownTx'])
        plt.ylabel('Traffic (bits)')
        plt.show()

# Prepare data for training
def prepare_data(df):
    numeric_df = df.select_dtypes(include=[np.number])
    X = numeric_df.drop(columns=['target'])
    y = numeric_df['target']
    return X, y

# Remove outliers
def remove_outliers(X):
    Q1 = X.quantile(0.25)
    Q3 = X.quantile(0.75)
    IQR = Q3 - Q1
    X_clean = X[~((X < (Q1 - 1.5 * IQR)) | (X > (Q3 + 1.5 * IQR))).any(axis=1)]
    return X_clean

# Train random forest
def train_random_forest(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = GradientBoostingClassifier(random_state=42)
    model.fit(X_train, y_train)
    
    # Save the trained model
    joblib.dump(model, 'random_forest_model.pkl')
    
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    avg_precision = average_precision_score(y_test, y_pred_proba)
    
    print(f"Accuracy: {accuracy}")
    print("Classification Report:")
    print(report)
    print(f"ROC AUC: {roc_auc}")
    print(f"Average Precision: {avg_precision}")

# Main execution
if __name__ == "__main__":
    df = load_data(FILE_PATH)
    df = df.sort_values(by="StartSession", key=lambda x: pd.to_datetime(x, format="%d-%m-%Y %H:%M:%S"))
    result = pd.read_csv('RESULT.csv')
    positive_clients = result['UID'].unique()
    df_with_aggregates = calculate_aggregates(df)
    df_with_aggregates['target'] = df_with_aggregates['IdClient'].isin(positive_clients).astype(int)

    X, y = prepare_data(df_with_aggregates)
    # X = remove_outliers(X)
    # y = y[X.index]
    train_random_forest(X, y)