from inf8239_u04.data import load_data, temporal_split
df=load_data(); train,test=temporal_split(df)
print("shape",df.shape); print("target",df.target.value_counts(normalize=True).round(3).to_dict()); print("groups",df.protected_group.value_counts().to_dict()); print("train_end",train.received_date.max()); print("test_start",test.received_date.min()); print("excluded_from_model",["case_id","received_date","protected_group","target"])
# Figures cited in docs/DATASET_CARD.md
print("date_range",df.received_date.min().date(),df.received_date.max().date()); print("zones",df.zone.value_counts().to_dict()); print("age_bands",df.age_band.value_counts().to_dict())
print("missing",int(df.isna().sum().sum())); print("case_id_unique",df.case_id.is_unique); print("train_n",len(train),"test_n",len(test)); print("test_prevalence",test.groupby("protected_group").target.mean().round(2).to_dict())
