#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns



# #Load Data

# In[ ]:


df = pd.read_csv("Supplychain_rawData.csv")
df.head()


# In[ ]:


df.info()


# In[ ]:


df.describe().T


# In[ ]:


# Handle missing values
df.dropna(inplace=True)


# In[ ]:


# Remove duplicates
df.drop_duplicates(inplace=True)


# In[ ]:


# Clean column names
df.columns = df.columns.str.strip().str.replace(" ", "_")


# In[ ]:


# Clean currency columns
df['Unit_Price'] = df['Unit_Price'].replace(r'[\$,]', '', regex=True).astype(float)
df['Unit_Cost'] = df['Unit_Cost'].replace(r'[\$,]', '', regex=True).astype(float)


# In[ ]:


# Convert dates
df['OrderDate'] = pd.to_datetime(df['OrderDate'], dayfirst=True)
df['ShipDate'] = pd.to_datetime(df['ShipDate'], dayfirst=True)
df['DeliveryDate'] = pd.to_datetime(df['DeliveryDate'], dayfirst=True)
df['ProcuredDate'] = pd.to_datetime(df['ProcuredDate'], dayfirst=True)


# In[ ]:


# Feature engineering
df['delivery_days'] = (df['DeliveryDate'] - df['ShipDate']).dt.days
df['revenue'] = df['Order_Quantity'] * df['Unit_Price']
df['total_cost'] = df['Order_Quantity'] * df['Unit_Cost']
df['profit'] = df['revenue'] - df['total_cost']
df['order_to_ship_days'] = (df['ShipDate'] - df['OrderDate']).dt.days
df['procure_to_order_days'] = (df['OrderDate'] - df['ProcuredDate']).dt.days


# In[ ]:


#Bussiness Insights

# 1. Top revenue channel
top_channel = df.groupby('Sales_Channel')['revenue'].sum().idxmax()
print(f"Top Revenue Channel: {top_channel}")

# 2. Fastest warehouse
fastest_wh = df.groupby('WarehouseCode')['delivery_days'].mean().idxmin()
print(f"Fastest Warehouse: {fastest_wh}")

# 3. Slowest warehouse
slowest_wh = df.groupby('WarehouseCode')['delivery_days'].mean().idxmax()
print(f"Slowest Warehouse: {slowest_wh}")

# 4. High discount impact
high_discount = df[df['Discount_Applied'] > 0.2]['revenue'].mean()
low_discount = df[df['Discount_Applied'] <= 0.2]['revenue'].mean()

print(f"Avg Revenue with High Discount: {round(high_discount,2)}")
print(f"Avg Revenue with Low Discount: {round(low_discount,2)}")

# 5. Delivery risk insight
delayed_orders = df[df['delivery_days'] > df['delivery_days'].mean()].shape[0]
print(f"Orders with above-average delivery time: {delayed_orders}")


# In[ ]:


# KPI Analysis
print("\n===== KPI =====")
print(df[['revenue','profit','delivery_days']].agg(['sum','mean','min','max']))

print("\nSales by Channel:")
print(df.groupby('Sales_Channel')['revenue'].sum())

print("\nDelivery by Warehouse:")
print(df.groupby('WarehouseCode')['delivery_days'].mean())


# #Visualization

# In[ ]:


# Revenue by channel
df.groupby('Sales_Channel')['revenue'].sum().plot(kind='bar', title="Revenue by Channel")
plt.show()


# In[ ]:


# Delivery by warehouse
df.groupby('WarehouseCode')['delivery_days'].mean().plot(kind='bar', title="Delivery Time by Warehouse")
plt.show()


# In[ ]:


# Profit distribution
plt.hist(df['profit'], bins=20)
plt.title("Profit Distribution")
plt.show()


# In[ ]:


# Monthly trend
df.groupby(df['OrderDate'].dt.to_period('M'))['revenue'].sum().plot(kind='line', title="Monthly Revenue Trend")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.show()


# In[ ]:


corr = df[['Order_Quantity','Unit_Price','Discount_Applied','revenue','profit','delivery_days']].corr()
sns.heatmap(corr, annot=True, cmap='coolwarm')
plt.title("Correlation Matrix")
plt.show()


# In[ ]:


# Executive summary

print(f"Total revenue: {df['revenue'].sum():,.0f}")
print(f"Total profit: {df['profit'].sum():,.0f}")
print(f"Average delivery days: {df['delivery_days'].mean():.2f}")
print("Top performing channel:", df.groupby('Sales_Channel')['revenue'].sum().idxmax())
print("Fastest warehouse:", df.groupby('WarehouseCode')['delivery_days'].mean().idxmin())


# In[ ]:


# Export cleaned data for Excel / Power BI
df.to_csv("Cleaned_Supplychain_Data.csv", index=False)


# In[ ]:






# In[ ]:





# In[ ]:





# In[ ]:




