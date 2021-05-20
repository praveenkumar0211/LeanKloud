import sys
import pandas as pd
csv_file=sys.argv[1]
df=pd.read_csv(csv_file)
columns=list(df.columns[1:])
df['total']=0
for i in columns:
    temp=df[i].max()
    a=(df[df[i]==temp]).to_string().split()
    print("Topper in",i,"is",a[9])
    df['total'] += df[i]
top_three=df['total'].nlargest(3).to_string().split()
first_topper=int(top_three[0])
second_topper=int(top_three[2])
third_topper=int(top_three[4])
print("Best students in the class are {}, {}, {}".format(df.iloc[first_topper,0],df.iloc[second_topper,0],df.iloc[third_topper,0]))

