import pandas as pd
all_cols=["State","Username","ID","First_Name","Last_Name","Date","Time"]
entries_csv = pd.read_csv(r'./users.csv',sep=',',names=all_cols)
user_cols=["ID","First_Name","Last_Name"]
sorted_by_date = entries_csv.sort_values(by=["Date","Time"], ascending=[True,True])
sorted_by_date.to_csv("./user_entries.csv", sep=',',index_label="Index")
users_only = entries_csv[user_cols].drop_duplicates()
users_only.to_csv("./unique_users.csv", sep=',',index_label="Index")
