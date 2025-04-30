import pandas as pd
import joblib
import numpy as np
from data_preprocessing import (
    load_and_combine_data,
    split_and_clean_data,
    merge_with_psxattrs,
    convert_sessions_to_gmt5,
    merge_with_subscribers
)
from eda import calculate_aggregates

FOLDER_PATH = '/Users/andrey/Desktop/MisisProjects/tasks-public/Arenadata/telecom100k'
MODEL_PATH = 'random_forest_model.pkl'
RESULT_PATH = 'RESULT2.CSV'

def preprocess_data(folder_path):
    combined_df = load_and_combine_data(folder_path)
    new_combined_df = split_and_clean_data(combined_df)
    merged_df = merge_with_psxattrs(new_combined_df, folder_path)
    merged_df['EndSession'] = merged_df['EndSession'].apply(lambda x: x.split('.')[0] if isinstance(x, str) else x)
    merged_df = convert_sessions_to_gmt5(merged_df)
    final_df = merge_with_subscribers(merged_df, folder_path)
    return final_df

def predict_scores(folder_path, model_path):
    df_preprocessed = pd.read_csv('final_df_2.csv')
    df_with_aggregates = calculate_aggregates(df_preprocessed)
    model = joblib.load(model_path)
    X = df_with_aggregates.select_dtypes(include=[np.number])
    scores = model.predict_proba(X)[:, 1]
    class_1_indices = df_with_aggregates.index[scores >= 0.5]
    required_columns = ['IdClient']
    result_df = df_preprocessed.loc[class_1_indices, required_columns]
    return result_df

if __name__ == "__main__":
    result_df = predict_scores(FOLDER_PATH, MODEL_PATH)
    final_df = pd.read_csv('final_df_2.csv')
    final_df = final_df[final_df['IdClient'].isin(result_df['IdClient'])].drop_duplicates(subset=['IdClient'])
    final_df = final_df[['IdClient', 'IdSubscriber', 'Type', 'IdPlan', 'Status']]
    final_df = final_df.rename(columns={'IdClient': 'UID', 'IdSubscriber': 'Id', "Status": "TurnOn"})
    final_df["Hacked"] = True
    final_df.to_csv(RESULT_PATH, index=False)
    print("Results saved to RESULT2.CSV") 