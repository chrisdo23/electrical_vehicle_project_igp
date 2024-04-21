def camel_case_conversion(df):
   df.rename(columns=lambda x: x[0].lower() + x.strip().lower().replace('_', ' ').title().replace(' ', '')[1:], inplace=True)
   return df

# Function to convert snake case to camel case
def snake_to_camel(name):
   parts = name.split('_')
   return parts[0] + ''.join(x.title() for x in parts[1:])
   
def to_camel_case(df):
    # Create a dictionary to map original column names to camel case names
    camel_case_mapping = {col: snake_to_camel(col) for col in df.columns}

    # Rename columns using the camel case mapping
    df_camel_case = df.rename(columns=camel_case_mapping)

    return df_camel_case