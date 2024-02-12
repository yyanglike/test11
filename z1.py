import adata

# k_type: k线类型：1.日；2.周；3.月 默认：1 日k
res_df = adata.stock.market.get_market(stock_code='000001', k_type=1, start_date='2021-01-01')
res_df.to_csv('res_df.csv', index=False)
print(res_df)
