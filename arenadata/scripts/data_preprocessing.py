import os
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta
import pytz

tqdm.pandas()

COLUMN_NAMES = 'IdSession|IdPSX|IdSubscriber|StartSession|EndSession|Duartion|UpTx|DownTx'

def load_and_combine_data(folder_path):
    files = [f for f in os.listdir(folder_path) if f.startswith('psx_')]
    combined_df = pd.DataFrame()

    for file in tqdm(files, desc="Loading files"):
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path)
        df['name_data'] = file
        combined_df = pd.concat([combined_df, df], ignore_index=True)

    return combined_df

def split_and_clean_data(combined_df):
    split_data = combined_df[combined_df[COLUMN_NAMES].notna()][COLUMN_NAMES].str.split('|', expand=True)
    split_data.columns = ['IdSession', 'IdPSX', 'IdSubscriber', 'StartSession', 'EndSession', 'Duartion', 'UpTx', 'DownTx']
    split_data['name_data'] = combined_df[combined_df[COLUMN_NAMES].notna()]['name_data']
    
    new_combined_df = pd.concat([
        combined_df[combined_df[COLUMN_NAMES].isna()].drop(columns=[COLUMN_NAMES]),
        split_data
    ], ignore_index=True)

    new_combined_df['EndSession'] = new_combined_df.apply(
        lambda row: row['name_data'].split('_')[-1][:-4] if not isinstance(row['EndSession'], str) or len(row['EndSession']) == 0 else row['EndSession'], axis=1
    )
    return new_combined_df

def merge_with_psxattrs(new_combined_df, folder_path):
    new_combined_df['psx_name'] = new_combined_df['name_data'].apply(lambda x: '_'.join(x.split('_')[:2]))
    new_combined_df['PSX'] = new_combined_df['psx_name'].str.split('_', expand=True)[1].astype(float)
    
    psxattrs = pd.read_csv(os.path.join(folder_path, 'psxattrs.csv'))
    merged_df = pd.merge(new_combined_df, psxattrs)
    
    merged_df['DownTx'] = merged_df.apply(lambda row: row['DownTx'] * 8 if row['TransmitUnits'] == 'bytes' else row['DownTx'], axis=1)
    merged_df['UpTx'] = merged_df.apply(lambda row: row['UpTx'] * 8 if row['TransmitUnits'] == 'bytes' else row['UpTx'], axis=1)
    
    return merged_df

def convert_sessions_to_gmt5(df):
    def convert_row(row):
        timezone_offset = row['TZ']
        timezone = pytz.timezone('Etc/' + str(timezone_offset))
        
        try:
            start_session = datetime.strptime(row['StartSession'], row['DateFormat'])
            start_session = timezone.localize(start_session).astimezone(pytz.timezone('Etc/GMT+5'))
            row['StartSession'] = start_session.strftime('%d-%m-%Y %H:%M:%S')
        except ValueError as e:
            print(f"Error parsing StartSession for row: {row} - {e}")
        
        if isinstance(row['EndSession'], str) and len(row['EndSession']) > 0:
            if row['EndSession'].startswith('20'):
                end_session = datetime.strptime(row['EndSession'], '%Y-%m-%d %H:%M:%S')
            else:
                end_session = datetime.strptime(row['EndSession'], row['DateFormat'])
        else:
            duration_seconds = int(row['Duartion'])
            end_session = start_session + timedelta(seconds=duration_seconds)
        end_session = timezone.localize(end_session).astimezone(pytz.timezone('Etc/GMT+5'))
        row['EndSession'] = end_session.strftime('%d-%m-%Y %H:%M:%S')
        return row

    df = df.progress_apply(convert_row, axis=1)
    return df

def merge_with_subscribers(merged_df, folder_path):
    client = pd.read_parquet(os.path.join(folder_path, 'client.parquet'))
    company = pd.read_parquet(os.path.join(folder_path, 'company.parquet'))
    subscribers = pd.read_csv(os.path.join(folder_path, 'subscribers.csv'))
    
    subscribers_merged = subscribers.merge(client, left_on="IdClient", right_on="Id")
    company_id = set(company['Id'].unique().tolist())
    subscribers_merged['Type'] = subscribers_merged['Id'].progress_apply(lambda x: "C" if x in company_id else "P")
    subscribers_merged.to_csv('subscribers_merged.csv', index=False)
    
    needed_df = merged_df[['IdSession', 'IdPSX', 'IdSubscriber', 'StartSession', 'EndSession', 'Duartion', 'UpTx', 'DownTx']]
    needed_df['IdSubscriber'] = needed_df['IdSubscriber'].astype(int)
    final_df = needed_df.merge(subscribers_merged, left_on='IdSubscriber', right_on='IdOnPSX', how='inner')
    
    return final_df

def main():
    folder_path = '/Users/andrey/Desktop/MisisProjects/tasks-public/Arenadata/telecom1000k'
    combined_df = load_and_combine_data(folder_path)
    new_combined_df = split_and_clean_data(combined_df)
    merged_df = merge_with_psxattrs(new_combined_df, folder_path)
    merged_df['EndSession'] = merged_df['EndSession'].apply(lambda x: x.split('.')[0] if isinstance(x, str) else x)
    merged_df = convert_sessions_to_gmt5(merged_df)
    final_df = merge_with_subscribers(merged_df, folder_path)
    final_df.to_csv('final_df_2.csv', index=False)

if __name__ == "__main__":
    main()