import pandas as pd
import numpy as np
import re

# Load CSV file into a pandas DataFrame
df = pd.read_csv('$PathTo/amazon_co-ecommerce_sample.csv')

# Select specific columns
df = df[['uniq_id', 'product_name', 'manufacturer', 'price', 'average_review_rating', 'amazon_category_and_sub_category', 'customer_reviews']]

df['amazon_category_and_sub_category'] = df['amazon_category_and_sub_category'].str.rsplit(' > ', n=1).str[-1]
print(df['amazon_category_and_sub_category'])

# Convert NaN values in customer_reviews column to empty string
df['customer_reviews'] = df['customer_reviews'].fillna('')

# Replace empty strings with NaN values
df = df.replace('', np.nan)



# Split customer_reviews column into separate lists of every 4 elements
df['customer_reviews'] = df['customer_reviews'].apply(lambda x: str(x).split(" // "))
result = []

df['customer_reviews'] = df['customer_reviews'].apply(lambda x: [item.replace('By\n    \n    ', '').replace('\n  \n on', '').strip() for item in x])

for item in df['customer_reviews']:
    sublist = []
    for i in range(0, len(item), 4):
        sublist.append(item[i:i+4])
    result.append(sublist)

df['customer_reviews'] = result

modified_reviews = []

for item in df['customer_reviews']:
    for subitem in item:
        if len(subitem) >= 4:
            match = re.search(r'\d+', subitem[3])
            if match:
                replace = match.start()
                username = subitem[3][:replace].strip()
                subitem[3] = username
            else:
                subitem[3] = ''  # Handle the case where no valid username is found
        elif len(subitem) > 0:
            subitem.append('')  # Handle the case where the data has less than four elements
        else:
            subitem.extend(['', '', '', ''])  # Handle the case where the data is empty

    modified_reviews.append(item)

df['customer_reviews'] = modified_reviews


# Drop rows with missing values (NaN)
df = df.dropna()

df.to_csv('modified_data.csv', index=False)

